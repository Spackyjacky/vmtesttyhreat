"""
job-applicator — automated LinkedIn job search and Easy Apply tool.

Usage:
    python main.py                        Full cycle: search → filter → apply → notify
    python main.py --dry-run              Search + filter, print what would be applied
    python main.py --search-only          Search + filter, save to search_results.json
    python main.py --notify-only          Email all pending-manual jobs, skip search
    python main.py --config myconfig.yaml Use a specific config file
    python main.py --no-headless          Run with a visible browser window
    python main.py -v                     Verbose (DEBUG) logging
"""
from __future__ import annotations

import argparse
import json
import logging
import logging.handlers
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    fmt = "[%(asctime)s] %(levelname)-8s %(message)s"
    datefmt = "%H:%M:%S"

    root = logging.getLogger()
    root.setLevel(level)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(logging.Formatter(fmt, datefmt))
    root.addHandler(ch)

    # Rotating file handler
    try:
        fh = logging.handlers.RotatingFileHandler(
            "job_applicator.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        fh.setLevel(level)
        fh.setFormatter(logging.Formatter(fmt, datefmt))
        root.addHandler(fh)
    except OSError:
        pass  # If we can't write a log file, just continue with console logging


logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="job-applicator",
        description="Search LinkedIn, auto-apply with Easy Apply, and email manual-apply lists.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--config",
        default="config.yaml",
        metavar="FILE",
        help="Path to config YAML file (default: config.yaml)",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Search and filter, but do not submit applications or send emails.",
    )
    p.add_argument(
        "--search-only",
        action="store_true",
        help="Search and filter, save results to search_results.json. No applications.",
    )
    p.add_argument(
        "--notify-only",
        action="store_true",
        help="Send email notification for all pending-manual jobs. Skip search.",
    )
    p.add_argument(
        "--no-headless",
        action="store_true",
        help="Override headless:true in config — show the browser window.",
    )
    p.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable DEBUG logging.",
    )
    return p


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    _setup_logging(args.verbose)

    # ── Load config ──────────────────────────────────────────────────────────
    config_path = Path(args.config)
    if not config_path.is_absolute():
        # Resolve relative to the directory containing main.py
        config_path = Path(__file__).parent / config_path

    try:
        from src.config import load_config
        cfg = load_config(config_path)
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        logger.error(
            "Copy config.yaml.example to config.yaml and fill in your details."
        )
        return 1
    except ValueError as exc:
        logger.error("Config error: %s", exc)
        return 1

    # CLI flags override config values
    if args.dry_run:
        cfg.application_settings.dry_run = True
    if args.no_headless:
        cfg.application_settings.headless = False

    dry_run = cfg.application_settings.dry_run

    # ── Initialise tracker ───────────────────────────────────────────────────
    from src.tracker import (
        Tracker,
        STATUS_APPLIED,
        STATUS_ALREADY_APPLIED,
        STATUS_ERROR,
        STATUS_PENDING_MANUAL,
        STATUS_SKIPPED_DUPLICATE,
        STATUS_SKIPPED_FILTERED,
        STATUS_SKIPPED_TOO_MANY_QUESTIONS,
    )
    from src.filters import apply_filters
    from src.notifier import Notifier

    tracker = Tracker(cfg.application_settings.db_path)
    notifier = Notifier(cfg.email_notifications)

    stats = {"found": 0, "applied": 0, "manual": 0, "skipped": 0, "errors": 0}

    # ── Notify-only mode ─────────────────────────────────────────────────────
    if args.notify_only:
        logger.info("Notify-only mode: sending pending-manual email digest…")
        pending = tracker.get_pending_manual()
        if not pending:
            logger.info("No pending-manual jobs in the database.")
        else:
            logger.info("%d pending-manual jobs found.", len(pending))
            notifier.send_manual_apply_digest(pending)
        tracker.close()
        return 0

    # ── Search phase ─────────────────────────────────────────────────────────
    from src.linkedin import LinkedInSession, ManualInterventionRequired, LinkedInRateLimitError

    all_filtered_jobs: list = []

    try:
        with LinkedInSession(
            cfg.linkedin, cfg.application_settings, dry_run=dry_run
        ) as session:
            session.set_filter_config(
                cfg.filters.remote_preference,
                cfg.filters.job_types,
            )

            session.login()

            for role in cfg.target_roles:
                logger.info("── Searching for: %s ──", role)
                raw_jobs = session.search_jobs(
                    role,
                    max_pages=cfg.application_settings.max_pages_per_role,
                )
                logger.info("Found %d raw listings for '%s'.", len(raw_jobs), role)
                stats["found"] += len(raw_jobs)

                # Fetch descriptions if keyword exclusions are configured
                if cfg.filters.exclude_keywords:
                    for job in raw_jobs:
                        if not job.get("description_snippet"):
                            detail = session.scrape_job_detail(job["id"])
                            job.update(detail)

                # Deduplicate against DB
                new_jobs = []
                for job in raw_jobs:
                    if tracker.is_seen(job["id"]):
                        logger.debug(
                            "Duplicate: %s (%s)", job.get("title"), job["id"]
                        )
                        stats["skipped"] += 1
                    else:
                        new_jobs.append(job)

                # Apply filters
                accepted, rejected = apply_filters(new_jobs, cfg.filters)
                for job in rejected:
                    logger.debug(
                        "Filtered out: %s — %s",
                        job.get("title"),
                        job.get("reject_reason"),
                    )
                    tracker.upsert_job(job)
                    tracker.update_status(
                        job["id"],
                        STATUS_SKIPPED_FILTERED,
                        job.get("reject_reason"),
                    )
                    stats["skipped"] += 1

                all_filtered_jobs.extend(accepted)
                logger.info(
                    "'%s': %d accepted after filtering (of %d new).",
                    role,
                    len(accepted),
                    len(new_jobs),
                )

            # ── Search-only mode ─────────────────────────────────────────────
            if args.search_only:
                output_path = cfg.config_dir / "search_results.json"
                with open(output_path, "w", encoding="utf-8") as fh:
                    json.dump(all_filtered_jobs, fh, indent=2, default=str)
                logger.info(
                    "Search-only mode: %d jobs saved to %s",
                    len(all_filtered_jobs),
                    output_path,
                )
                tracker.log_run(cfg.target_roles, stats, dry_run)
                tracker.close()
                return 0

            # ── Apply phase ──────────────────────────────────────────────────
            limit = cfg.application_settings.max_applications_per_run
            apply_queue = all_filtered_jobs if limit == 0 else all_filtered_jobs[:limit]
            if limit > 0 and len(all_filtered_jobs) > limit:
                logger.info(
                    "Capping at %d applications (found %d). "
                    "Remaining saved for next run.",
                    limit,
                    len(all_filtered_jobs),
                )

            for job in apply_queue:
                job_label = f"{job.get('title')} @ {job.get('company')}"

                # Save job to DB before attempting
                tracker.upsert_job(job)

                if not job.get("easy_apply"):
                    logger.info("Non-Easy-Apply: %-50s → manual", job_label)
                    tracker.update_status(
                        job["id"],
                        STATUS_PENDING_MANUAL,
                        "External application portal",
                    )
                    stats["manual"] += 1
                    continue

                status = session.apply_easy_apply(job)
                tracker.update_status(
                    job["id"],
                    status,
                    _status_reason(status),
                )

                if status == STATUS_APPLIED:
                    logger.info("Applied ✓  %s", job_label)
                    stats["applied"] += 1
                elif status in (
                    STATUS_SKIPPED_TOO_MANY_QUESTIONS,
                    STATUS_PENDING_MANUAL,
                ):
                    logger.info("→ Manual:  %s  (%s)", job_label, status)
                    tracker.update_status(
                        job["id"],
                        STATUS_PENDING_MANUAL,
                        _status_reason(status),
                    )
                    stats["manual"] += 1
                elif status == STATUS_ALREADY_APPLIED:
                    logger.info("Already applied: %s", job_label)
                    stats["skipped"] += 1
                elif status == STATUS_ERROR:
                    logger.warning("Error applying to: %s", job_label)
                    stats["errors"] += 1

    except ManualInterventionRequired as exc:
        logger.error("Manual intervention required: %s", exc)
        tracker.close()
        return 2
    except LinkedInRateLimitError as exc:
        logger.error("LinkedIn rate limit: %s", exc)
        tracker.close()
        return 3
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
        tracker.close()
        return 130

    # ── Notify phase ─────────────────────────────────────────────────────────
    pending = tracker.get_pending_manual()
    if pending and not dry_run:
        logger.info("Sending email digest for %d manual-apply jobs…", len(pending))
        notifier.send_manual_apply_digest(pending)
    elif dry_run and pending:
        logger.info("[DRY RUN] Would send email for %d manual-apply jobs.", len(pending))

    # ── Summary ──────────────────────────────────────────────────────────────
    tracker.log_run(cfg.target_roles, stats, dry_run)
    tracker.close()

    _print_summary(stats, dry_run)
    return 0


def _status_reason(status: str) -> str:
    reasons = {
        "SKIPPED_TOO_MANY_QUESTIONS": "Too many custom form questions",
        "ERROR": "Application error",
        "PENDING_MANUAL": "External application portal",
        "ALREADY_APPLIED": "Already applied previously",
    }
    return reasons.get(status, "")


def _print_summary(stats: dict, dry_run: bool) -> None:
    prefix = "[DRY RUN] " if dry_run else ""
    print("\n" + "─" * 50)
    print(f"{prefix}Run complete")
    print("─" * 50)
    print(f"  Jobs found (raw):   {stats['found']}")
    print(f"  Applied:            {stats['applied']}")
    print(f"  Manual required:    {stats['manual']}")
    print(f"  Skipped/filtered:   {stats['skipped']}")
    if stats["errors"]:
        print(f"  Errors:             {stats['errors']}")
    print("─" * 50)


if __name__ == "__main__":
    sys.exit(main())
