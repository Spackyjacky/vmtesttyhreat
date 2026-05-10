"""Unit tests for src/filters.py — all pure functions, no I/O needed."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from src.filters import apply_filters, parse_salary_text
from src.config import FilterConfig


def _cfg(**kwargs) -> FilterConfig:
    defaults = dict(
        salary_min=None,
        salary_max=None,
        filter_undisclosed_salary=False,
        locations=[],
        remote_preference="any",
        job_types=[],
        exclude_keywords=[],
    )
    defaults.update(kwargs)
    return FilterConfig(**defaults)


def _job(**kwargs) -> dict:
    defaults = dict(
        id="1",
        title="Security Analyst",
        company="Acme Corp",
        location="New York, NY",
        url="https://linkedin.com/jobs/view/1/",
        easy_apply=True,
        salary_text=None,
        salary_min=None,
        salary_max=None,
        job_type="Full-time",
        description_snippet="Security monitoring and incident response.",
    )
    defaults.update(kwargs)
    return defaults


# ---------------------------------------------------------------------------
# parse_salary_text
# ---------------------------------------------------------------------------

class TestParseSalaryText:
    def test_annual_single(self):
        assert parse_salary_text("$80,000/yr") == (80000, 80000)

    def test_annual_range(self):
        assert parse_salary_text("$80,000 – $120,000/yr") == (80000, 120000)

    def test_hourly_single(self):
        lo, hi = parse_salary_text("$45/hr")
        assert lo == hi == 45 * 2080

    def test_hourly_range(self):
        lo, hi = parse_salary_text("$45 – $60/hr")
        assert lo == 45 * 2080
        assert hi == 60 * 2080

    def test_k_suffix(self):
        lo, hi = parse_salary_text("$80K – $120K/yr")
        assert lo == 80000
        assert hi == 120000

    def test_empty_string(self):
        assert parse_salary_text("") == (None, None)

    def test_none_string(self):
        assert parse_salary_text(None) == (None, None)

    def test_unparseable(self):
        assert parse_salary_text("Competitive") == (None, None)

    def test_swap_order(self):
        # If the text somehow has high then low, result should still be ordered
        lo, hi = parse_salary_text("$120,000 – $80,000/yr")
        assert lo <= hi


# ---------------------------------------------------------------------------
# Salary filter
# ---------------------------------------------------------------------------

class TestSalaryFilter:
    def test_passes_within_range(self):
        job = _job(salary_text="$90,000/yr")
        accepted, _ = apply_filters([job], _cfg(salary_min=60000, salary_max=130000))
        assert len(accepted) == 1

    def test_rejects_below_min(self):
        job = _job(salary_text="$50,000/yr")
        _, rejected = apply_filters([job], _cfg(salary_min=60000, salary_max=130000))
        assert len(rejected) == 1
        assert "minimum" in rejected[0]["reject_reason"]

    def test_rejects_above_max(self):
        job = _job(salary_text="$150,000/yr")
        _, rejected = apply_filters([job], _cfg(salary_min=60000, salary_max=130000))
        assert len(rejected) == 1
        assert "maximum" in rejected[0]["reject_reason"]

    def test_passes_undisclosed_salary_by_default(self):
        job = _job(salary_text=None)
        accepted, _ = apply_filters([job], _cfg(salary_min=60000, salary_max=130000))
        assert len(accepted) == 1

    def test_rejects_undisclosed_when_configured(self):
        job = _job(salary_text=None)
        _, rejected = apply_filters(
            [job], _cfg(salary_min=60000, filter_undisclosed_salary=True)
        )
        assert len(rejected) == 1
        assert "disclosed" in rejected[0]["reject_reason"].lower()

    def test_no_salary_bounds_passes_everything(self):
        job = _job(salary_text="$200,000/yr")
        accepted, _ = apply_filters([job], _cfg())
        assert len(accepted) == 1


# ---------------------------------------------------------------------------
# Location filter
# ---------------------------------------------------------------------------

class TestLocationFilter:
    def test_passes_matching_location(self):
        job = _job(location="New York, NY")
        accepted, _ = apply_filters([job], _cfg(locations=["New York"]))
        assert len(accepted) == 1

    def test_rejects_non_matching_location(self):
        job = _job(location="San Francisco, CA")
        _, rejected = apply_filters([job], _cfg(locations=["New York"]))
        assert len(rejected) == 1

    def test_remote_preference_skips_location_check(self):
        job = _job(location="San Francisco, CA")
        accepted, _ = apply_filters(
            [job], _cfg(remote_preference="remote", locations=["New York"])
        )
        assert len(accepted) == 1

    def test_empty_locations_passes_all(self):
        job = _job(location="Anywhere")
        accepted, _ = apply_filters([job], _cfg(locations=[]))
        assert len(accepted) == 1

    def test_case_insensitive_match(self):
        job = _job(location="NEW YORK, NY")
        accepted, _ = apply_filters([job], _cfg(locations=["new york"]))
        assert len(accepted) == 1


# ---------------------------------------------------------------------------
# Job type filter
# ---------------------------------------------------------------------------

class TestJobTypeFilter:
    def test_passes_matching_job_type(self):
        job = _job(job_type="Full-time")
        accepted, _ = apply_filters([job], _cfg(job_types=["full-time"]))
        assert len(accepted) == 1

    def test_rejects_non_matching_job_type(self):
        job = _job(job_type="Part-time")
        _, rejected = apply_filters([job], _cfg(job_types=["full-time"]))
        assert len(rejected) == 1

    def test_passes_with_multiple_types(self):
        job = _job(job_type="Contract")
        accepted, _ = apply_filters([job], _cfg(job_types=["full-time", "contract"]))
        assert len(accepted) == 1

    def test_passes_unknown_job_type(self):
        job = _job(job_type=None)
        accepted, _ = apply_filters([job], _cfg(job_types=["full-time"]))
        assert len(accepted) == 1

    def test_empty_job_types_passes_all(self):
        job = _job(job_type="Internship")
        accepted, _ = apply_filters([job], _cfg(job_types=[]))
        assert len(accepted) == 1


# ---------------------------------------------------------------------------
# Keyword exclusion filter
# ---------------------------------------------------------------------------

class TestExcludeKeywords:
    def test_rejects_keyword_in_title(self):
        job = _job(title="Senior SOC Analyst - TS/SCI required")
        _, rejected = apply_filters([job], _cfg(exclude_keywords=["TS/SCI"]))
        assert len(rejected) == 1
        assert "TS/SCI" in rejected[0]["reject_reason"]

    def test_rejects_keyword_in_description(self):
        job = _job(description_snippet="Must have clearance required.")
        _, rejected = apply_filters([job], _cfg(exclude_keywords=["clearance required"]))
        assert len(rejected) == 1

    def test_rejects_keyword_in_company(self):
        job = _job(company="Unpaid Ventures LLC")
        _, rejected = apply_filters([job], _cfg(exclude_keywords=["unpaid"]))
        assert len(rejected) == 1

    def test_passes_when_no_match(self):
        job = _job(title="SOC Analyst", description_snippet="Great team.")
        accepted, _ = apply_filters([job], _cfg(exclude_keywords=["clearance required"]))
        assert len(accepted) == 1

    def test_case_insensitive(self):
        job = _job(title="SOC Analyst - UNPAID internship")
        _, rejected = apply_filters([job], _cfg(exclude_keywords=["unpaid"]))
        assert len(rejected) == 1

    def test_empty_keywords_passes_all(self):
        job = _job(title="TS/SCI required")
        accepted, _ = apply_filters([job], _cfg(exclude_keywords=[]))
        assert len(accepted) == 1


# ---------------------------------------------------------------------------
# Combined filter
# ---------------------------------------------------------------------------

class TestCombinedFilters:
    def test_first_failure_short_circuits(self):
        job = _job(
            title="Intern SOC Analyst",
            salary_text="$20,000/yr",
            location="Mars",
        )
        cfg = _cfg(
            salary_min=60000,
            locations=["New York"],
            exclude_keywords=["intern"],
        )
        _, rejected = apply_filters([job], cfg)
        # Should fail on exclude_keyword first (checked first)
        assert "intern" in rejected[0]["reject_reason"].lower()

    def test_multiple_jobs_mixed(self):
        jobs = [
            _job(id="1", title="SOC Analyst", salary_text="$90,000/yr",
                 location="New York", job_type="Full-time"),
            _job(id="2", title="Intern SOC Analyst", salary_text="$30,000/yr",
                 location="Remote"),
            _job(id="3", title="Threat Intel Lead", salary_text="$110,000/yr",
                 location="Austin, TX", job_type="Full-time"),
        ]
        cfg = _cfg(
            salary_min=60000,
            locations=["New York", "Austin"],
            job_types=["full-time"],
            exclude_keywords=["intern"],
        )
        accepted, rejected = apply_filters(jobs, cfg)
        assert {j["id"] for j in accepted} == {"1", "3"}
        assert {j["id"] for j in rejected} == {"2"}
