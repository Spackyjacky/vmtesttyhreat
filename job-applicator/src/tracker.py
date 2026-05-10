"""
SQLite-backed tracker for job application state.
Handles deduplication across runs and tracks application status.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Status constants
# ---------------------------------------------------------------------------
STATUS_APPLIED = "APPLIED"
STATUS_PENDING_MANUAL = "PENDING_MANUAL"
STATUS_SKIPPED_DUPLICATE = "SKIPPED_DUPLICATE"
STATUS_SKIPPED_FILTERED = "SKIPPED_FILTERED"
STATUS_SKIPPED_TOO_MANY_QUESTIONS = "SKIPPED_TOO_MANY_QUESTIONS"
STATUS_ERROR = "ERROR"
STATUS_ALREADY_APPLIED = "ALREADY_APPLIED"

ALL_STATUSES = {
    STATUS_APPLIED,
    STATUS_PENDING_MANUAL,
    STATUS_SKIPPED_DUPLICATE,
    STATUS_SKIPPED_FILTERED,
    STATUS_SKIPPED_TOO_MANY_QUESTIONS,
    STATUS_ERROR,
    STATUS_ALREADY_APPLIED,
}

# ---------------------------------------------------------------------------
# DDL
# ---------------------------------------------------------------------------
_SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id              TEXT PRIMARY KEY,
    title           TEXT NOT NULL,
    company         TEXT NOT NULL,
    location        TEXT,
    url             TEXT NOT NULL,
    easy_apply      INTEGER NOT NULL DEFAULT 0,
    salary_text     TEXT,
    status          TEXT NOT NULL,
    applied_at      TEXT,
    skip_reason     TEXT,
    notes           TEXT,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS job_status_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id      TEXT NOT NULL REFERENCES jobs(id),
    old_status  TEXT,
    new_status  TEXT NOT NULL,
    changed_at  TEXT NOT NULL,
    reason      TEXT
);

CREATE TABLE IF NOT EXISTS run_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_at          TEXT NOT NULL,
    roles_searched  TEXT,
    jobs_found      INTEGER,
    jobs_applied    INTEGER,
    jobs_manual     INTEGER,
    jobs_skipped    INTEGER,
    dry_run         INTEGER
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Tracker class
# ---------------------------------------------------------------------------

class Tracker:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._migrate()

    def _migrate(self) -> None:
        with self._conn:
            self._conn.executescript(_SCHEMA)

    # ── Queries ──────────────────────────────────────────────────────────────

    def is_seen(self, job_id: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM jobs WHERE id = ?", (job_id,)
        ).fetchone()
        return row is not None

    def upsert_job(self, job: Dict) -> None:
        """
        Insert a new job row, or update mutable fields if it already exists.
        Preserves an existing terminal status (APPLIED, ALREADY_APPLIED) so a
        re-run never overwrites a successful application record.
        """
        now = _now()
        job_id = job["id"]
        existing = self._conn.execute(
            "SELECT status FROM jobs WHERE id = ?", (job_id,)
        ).fetchone()

        if existing is None:
            with self._conn:
                self._conn.execute(
                    """
                    INSERT INTO jobs
                        (id, title, company, location, url, easy_apply,
                         salary_text, status, applied_at, skip_reason,
                         notes, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        job_id,
                        job.get("title", ""),
                        job.get("company", ""),
                        job.get("location", ""),
                        job.get("url", ""),
                        1 if job.get("easy_apply") else 0,
                        job.get("salary_text"),
                        job.get("status", STATUS_PENDING_MANUAL),
                        job.get("applied_at"),
                        job.get("skip_reason"),
                        job.get("notes"),
                        now,
                        now,
                    ),
                )
        else:
            terminal = {STATUS_APPLIED, STATUS_ALREADY_APPLIED}
            if existing["status"] not in terminal:
                with self._conn:
                    self._conn.execute(
                        """
                        UPDATE jobs SET
                            title = ?, company = ?, location = ?,
                            url = ?, easy_apply = ?, salary_text = ?,
                            updated_at = ?
                        WHERE id = ?
                        """,
                        (
                            job.get("title", ""),
                            job.get("company", ""),
                            job.get("location", ""),
                            job.get("url", ""),
                            1 if job.get("easy_apply") else 0,
                            job.get("salary_text"),
                            now,
                            job_id,
                        ),
                    )

    def update_status(
        self,
        job_id: str,
        status: str,
        reason: Optional[str] = None,
    ) -> None:
        now = _now()
        row = self._conn.execute(
            "SELECT status FROM jobs WHERE id = ?", (job_id,)
        ).fetchone()
        old_status = row["status"] if row else None

        applied_at = now if status == STATUS_APPLIED else None

        with self._conn:
            self._conn.execute(
                """
                UPDATE jobs
                SET status = ?,
                    skip_reason = CASE WHEN ? IS NOT NULL THEN ? ELSE skip_reason END,
                    applied_at  = CASE WHEN ? IS NOT NULL THEN ? ELSE applied_at END,
                    updated_at  = ?
                WHERE id = ?
                """,
                (status, reason, reason, applied_at, applied_at, now, job_id),
            )
            self._conn.execute(
                """
                INSERT INTO job_status_history
                    (job_id, old_status, new_status, changed_at, reason)
                VALUES (?, ?, ?, ?, ?)
                """,
                (job_id, old_status, status, now, reason),
            )

    def get_pending_manual(self) -> List[Dict]:
        rows = self._conn.execute(
            """
            SELECT id, title, company, location, url, skip_reason
            FROM jobs
            WHERE status = ?
            ORDER BY created_at DESC
            """,
            (STATUS_PENDING_MANUAL,),
        ).fetchall()
        return [dict(r) for r in rows]

    def log_run(self, roles: List[str], stats: Dict, dry_run: bool) -> None:
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO run_log
                    (run_at, roles_searched, jobs_found, jobs_applied,
                     jobs_manual, jobs_skipped, dry_run)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    _now(),
                    json.dumps(roles),
                    stats.get("found", 0),
                    stats.get("applied", 0),
                    stats.get("manual", 0),
                    stats.get("skipped", 0),
                    1 if dry_run else 0,
                ),
            )

    def close(self) -> None:
        self._conn.commit()
        self._conn.close()
