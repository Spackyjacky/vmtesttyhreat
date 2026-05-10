"""
Pure filter functions for job listings.
Each function is side-effect free and independently unit-testable.

A "job dict" is expected to have these keys (all optional except noted):
    id               str  (required)
    title            str
    company          str
    location         str
    url              str
    easy_apply       bool
    salary_text      str | None  — raw string e.g. "$80,000 – $120,000/yr"
    salary_min       int | None  — parsed annual min (populated by this module)
    salary_max       int | None  — parsed annual max
    job_type         str | None  — e.g. "Full-time"
    description_snippet  str
"""
from __future__ import annotations

import re
from typing import List, Optional, Tuple

from src.config import FilterConfig

# Hours in a standard work year used to convert hourly → annual
_HOURS_PER_YEAR = 2080


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def apply_filters(
    jobs: List[dict],
    config: FilterConfig,
) -> Tuple[List[dict], List[dict]]:
    """
    Split jobs into (accepted, rejected).
    Rejected items have a 'reject_reason' key added.
    """
    accepted: List[dict] = []
    rejected: List[dict] = []

    for job in jobs:
        # Pre-parse salary text into normalised fields used by _passes_salary
        if job.get("salary_text") and job.get("salary_min") is None:
            lo, hi = parse_salary_text(job["salary_text"])
            job["salary_min"] = lo
            job["salary_max"] = hi

        passed, reason = _evaluate(job, config)
        if passed:
            accepted.append(job)
        else:
            job["reject_reason"] = reason
            rejected.append(job)

    return accepted, rejected


def parse_salary_text(salary_text: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Parse LinkedIn salary strings into (annual_min, annual_max).

    Handles:
        "$80,000/yr"             → (80000, 80000)
        "$80,000 – $120,000/yr"  → (80000, 120000)
        "$80K – $120K/yr"        → (80000, 120000)
        "$45/hr"                 → (93600, 93600)   [45 * 2080]
        "$45 – $60/hr"           → (93600, 124800)

    Returns (None, None) if the string cannot be parsed.
    """
    if not salary_text:
        return None, None

    text = salary_text.replace(",", "").upper()

    # Detect unit
    is_hourly = "/HR" in text or "PER HOUR" in text or "HOUR" in text
    is_annual = "/YR" in text or "YEAR" in text or "/YEAR" in text or "ANNUAL" in text

    # Extract all numeric values (handles "K" suffix)
    numbers: List[int] = []
    for match in re.finditer(r"\$?([\d]+(?:\.[\d]+)?)\s*K?", text):
        raw = match.group(0)
        value_str = match.group(1)
        value = float(value_str)
        if "K" in raw.upper().split(value_str)[-1][:2]:
            value *= 1000
        numbers.append(int(value))

    if not numbers:
        return None, None

    lo = numbers[0]
    hi = numbers[-1] if len(numbers) > 1 else lo

    if is_hourly:
        lo = int(lo * _HOURS_PER_YEAR)
        hi = int(hi * _HOURS_PER_YEAR)
    elif not is_annual:
        # Ambiguous — treat values <1000 as hourly, others as annual
        if lo < 1000:
            lo = int(lo * _HOURS_PER_YEAR)
            hi = int(hi * _HOURS_PER_YEAR)

    # Sanity check: swap if out of order
    if lo > hi:
        lo, hi = hi, lo

    return lo, hi


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _evaluate(job: dict, cfg: FilterConfig) -> Tuple[bool, str]:
    """Return (passes, reason). Stops at the first failing check."""
    for check in (
        _passes_exclude_keywords,
        _passes_salary,
        _passes_location,
        _passes_job_type,
    ):
        ok, reason = check(job, cfg)
        if not ok:
            return False, reason
    return True, ""


def _passes_salary(job: dict, cfg: FilterConfig) -> Tuple[bool, str]:
    job_min = job.get("salary_min")
    job_max = job.get("salary_max")

    has_salary_data = job_min is not None or job_max is not None

    if not has_salary_data:
        if cfg.filter_undisclosed_salary:
            return False, "Salary not disclosed"
        return True, ""

    # If user has no salary bounds configured, pass everything
    if cfg.salary_min is None and cfg.salary_max is None:
        return True, ""

    # Use midpoint for comparison when we have a range
    job_mid = (
        (job_min + job_max) // 2
        if job_min is not None and job_max is not None
        else (job_min or job_max)
    )

    if cfg.salary_min is not None and job_mid < cfg.salary_min:
        return False, f"Salary {job_mid:,} < minimum {cfg.salary_min:,}"
    if cfg.salary_max is not None and job_mid > cfg.salary_max:
        return False, f"Salary {job_mid:,} > maximum {cfg.salary_max:,}"

    return True, ""


def _passes_location(job: dict, cfg: FilterConfig) -> Tuple[bool, str]:
    # Remote-only preference: skip location check entirely
    if cfg.remote_preference == "remote":
        return True, ""

    # No location filter configured: pass everything
    if not cfg.locations:
        return True, ""

    job_location = (job.get("location") or "").lower()
    for loc in cfg.locations:
        if loc.lower() in job_location:
            return True, ""

    return False, f"Location '{job.get('location')}' not in configured locations"


def _passes_job_type(job: dict, cfg: FilterConfig) -> Tuple[bool, str]:
    if not cfg.job_types:
        return True, ""

    raw_type = (job.get("job_type") or "").lower().strip()
    if not raw_type:
        # Job type unknown — don't reject, let it through
        return True, ""

    # Normalise LinkedIn labels: "Full-time" → "full-time", "Contract" → "contract"
    normalised = raw_type.replace(" ", "-")

    for jt in cfg.job_types:
        if jt in normalised or normalised in jt:
            return True, ""

    return False, f"Job type '{raw_type}' not in configured types {cfg.job_types}"


def _passes_exclude_keywords(job: dict, cfg: FilterConfig) -> Tuple[bool, str]:
    if not cfg.exclude_keywords:
        return True, ""

    searchable = " ".join([
        job.get("title") or "",
        job.get("company") or "",
        job.get("description_snippet") or "",
    ]).lower()

    for kw in cfg.exclude_keywords:
        if kw.lower() in searchable:
            return False, f"Excluded keyword: '{kw}'"

    return True, ""
