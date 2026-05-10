"""Unit tests for src/tracker.py — uses in-memory SQLite so no file I/O."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from src.tracker import (
    Tracker,
    STATUS_APPLIED,
    STATUS_ALREADY_APPLIED,
    STATUS_PENDING_MANUAL,
    STATUS_SKIPPED_FILTERED,
)


@pytest.fixture
def tracker(tmp_path):
    """Return a fresh Tracker backed by a temp SQLite file."""
    db_file = tmp_path / "test.db"
    t = Tracker(db_file)
    yield t
    t.close()


def _sample_job(**overrides) -> dict:
    base = {
        "id": "12345",
        "title": "Security Analyst",
        "company": "Acme Corp",
        "location": "New York, NY",
        "url": "https://linkedin.com/jobs/view/12345/",
        "easy_apply": True,
        "salary_text": "$90,000/yr",
        "status": STATUS_PENDING_MANUAL,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# is_seen
# ---------------------------------------------------------------------------

class TestIsSeen:
    def test_unseen_job_returns_false(self, tracker):
        assert tracker.is_seen("99999") is False

    def test_seen_after_upsert(self, tracker):
        tracker.upsert_job(_sample_job())
        assert tracker.is_seen("12345") is True

    def test_different_id_unseen(self, tracker):
        tracker.upsert_job(_sample_job())
        assert tracker.is_seen("99999") is False


# ---------------------------------------------------------------------------
# upsert_job
# ---------------------------------------------------------------------------

class TestUpsertJob:
    def test_insert_new_job(self, tracker):
        tracker.upsert_job(_sample_job())
        assert tracker.is_seen("12345")

    def test_update_does_not_overwrite_applied_status(self, tracker):
        tracker.upsert_job(_sample_job(status=STATUS_APPLIED))
        tracker.update_status("12345", STATUS_APPLIED)
        # Re-upsert with different data — status should stay APPLIED
        tracker.upsert_job(_sample_job(title="Changed Title"))
        row = tracker._conn.execute(
            "SELECT status FROM jobs WHERE id = ?", ("12345",)
        ).fetchone()
        assert row["status"] == STATUS_APPLIED

    def test_update_does_not_overwrite_already_applied_status(self, tracker):
        tracker.upsert_job(_sample_job())
        tracker.update_status("12345", STATUS_ALREADY_APPLIED)
        tracker.upsert_job(_sample_job(title="New Title"))
        row = tracker._conn.execute(
            "SELECT status FROM jobs WHERE id = ?", ("12345",)
        ).fetchone()
        assert row["status"] == STATUS_ALREADY_APPLIED

    def test_second_upsert_updates_non_terminal(self, tracker):
        tracker.upsert_job(_sample_job(title="Old Title"))
        # PENDING_MANUAL is not terminal — title should update
        tracker.upsert_job(_sample_job(title="New Title"))
        row = tracker._conn.execute(
            "SELECT title FROM jobs WHERE id = ?", ("12345",)
        ).fetchone()
        assert row["title"] == "New Title"


# ---------------------------------------------------------------------------
# update_status
# ---------------------------------------------------------------------------

class TestUpdateStatus:
    def test_status_changes(self, tracker):
        tracker.upsert_job(_sample_job())
        tracker.update_status("12345", STATUS_APPLIED)
        row = tracker._conn.execute(
            "SELECT status FROM jobs WHERE id = ?", ("12345",)
        ).fetchone()
        assert row["status"] == STATUS_APPLIED

    def test_history_appended(self, tracker):
        tracker.upsert_job(_sample_job())
        tracker.update_status("12345", STATUS_APPLIED, "application submitted")
        history = tracker._conn.execute(
            "SELECT * FROM job_status_history WHERE job_id = ?", ("12345",)
        ).fetchall()
        assert len(history) == 1
        assert history[0]["new_status"] == STATUS_APPLIED
        assert history[0]["reason"] == "application submitted"

    def test_multiple_status_changes_all_recorded(self, tracker):
        tracker.upsert_job(_sample_job())
        tracker.update_status("12345", STATUS_PENDING_MANUAL)
        tracker.update_status("12345", STATUS_APPLIED)
        history = tracker._conn.execute(
            "SELECT * FROM job_status_history WHERE job_id = ? ORDER BY id",
            ("12345",),
        ).fetchall()
        assert len(history) == 2
        assert history[0]["new_status"] == STATUS_PENDING_MANUAL
        assert history[1]["new_status"] == STATUS_APPLIED

    def test_applied_at_set_when_applied(self, tracker):
        tracker.upsert_job(_sample_job())
        tracker.update_status("12345", STATUS_APPLIED)
        row = tracker._conn.execute(
            "SELECT applied_at FROM jobs WHERE id = ?", ("12345",)
        ).fetchone()
        assert row["applied_at"] is not None

    def test_applied_at_not_set_for_other_statuses(self, tracker):
        tracker.upsert_job(_sample_job())
        tracker.update_status("12345", STATUS_PENDING_MANUAL)
        row = tracker._conn.execute(
            "SELECT applied_at FROM jobs WHERE id = ?", ("12345",)
        ).fetchone()
        assert row["applied_at"] is None


# ---------------------------------------------------------------------------
# get_pending_manual
# ---------------------------------------------------------------------------

class TestGetPendingManual:
    def test_returns_pending_manual_jobs(self, tracker):
        tracker.upsert_job(_sample_job(id="1", status=STATUS_PENDING_MANUAL))
        tracker.upsert_job(_sample_job(id="2", status=STATUS_APPLIED))
        tracker.update_status("1", STATUS_PENDING_MANUAL)
        results = tracker.get_pending_manual()
        ids = {r["id"] for r in results}
        assert "1" in ids
        assert "2" not in ids

    def test_returns_empty_when_none_pending(self, tracker):
        tracker.upsert_job(_sample_job())
        tracker.update_status("12345", STATUS_APPLIED)
        assert tracker.get_pending_manual() == []

    def test_includes_skip_reason(self, tracker):
        tracker.upsert_job(_sample_job())
        tracker.update_status("12345", STATUS_PENDING_MANUAL, "External portal")
        results = tracker.get_pending_manual()
        assert results[0]["skip_reason"] == "External portal"


# ---------------------------------------------------------------------------
# log_run
# ---------------------------------------------------------------------------

class TestLogRun:
    def test_run_log_written(self, tracker):
        tracker.log_run(
            roles=["SOC Analyst", "Security Analyst"],
            stats={"found": 10, "applied": 5, "manual": 3, "skipped": 2},
            dry_run=False,
        )
        rows = tracker._conn.execute("SELECT * FROM run_log").fetchall()
        assert len(rows) == 1
        assert rows[0]["jobs_found"] == 10
        assert rows[0]["jobs_applied"] == 5
        assert rows[0]["dry_run"] == 0

    def test_dry_run_flag_recorded(self, tracker):
        tracker.log_run(roles=[], stats={}, dry_run=True)
        rows = tracker._conn.execute("SELECT * FROM run_log").fetchall()
        assert rows[0]["dry_run"] == 1


# ---------------------------------------------------------------------------
# Migration idempotency
# ---------------------------------------------------------------------------

class TestMigration:
    def test_migrate_twice_is_safe(self, tmp_path):
        db_file = tmp_path / "double.db"
        t1 = Tracker(db_file)
        t1.close()
        # Second Tracker on same file should not error
        t2 = Tracker(db_file)
        t2.close()
