#!/usr/bin/env python3
"""Prunes captures older than storage.retention_days from disk and the DB.

Intended to run periodically via the anpr-cleanup systemd timer, but safe
to run manually too.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path

import db
from config import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [cleanup] %(levelname)s: %(message)s",
)
log = logging.getLogger("cleanup")


def main():
    config = load_config()
    storage = config["storage"]
    captures_dir = Path(storage["captures_dir"])
    db_path = storage["database_path"]
    retention_days = int(storage.get("retention_days", 30))

    cutoff = datetime.now() - timedelta(days=retention_days)
    cutoff_iso = cutoff.isoformat(timespec="seconds")

    db.init_db(db_path)
    events = db.delete_events_before(db_path, cutoff_iso)
    log.info("Removing %d event(s) older than %s", len(events), cutoff_iso)

    for event in events:
        for rel_path in (event.full_image_path, event.vehicle_image_path, event.plate_image_path):
            if not rel_path:
                continue
            path = captures_dir / rel_path
            path.unlink(missing_ok=True)

    _prune_empty_dirs(captures_dir)
    log.info("Cleanup complete")


def _prune_empty_dirs(root: Path):
    if not root.exists():
        return
    for path in sorted(root.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if path.is_dir() and not any(path.iterdir()):
            path.rmdir()


if __name__ == "__main__":
    main()
