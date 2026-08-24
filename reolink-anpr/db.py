"""SQLite storage for captured vehicle events.

One connection is opened per call rather than held open, since events are
written by several independent camera processes and read by the dashboard
process concurrently. WAL mode lets those overlap without locking errors.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp          TEXT NOT NULL,
    camera             TEXT NOT NULL,
    vehicle_type       TEXT,
    plate              TEXT,
    plate_confidence   REAL,
    color              TEXT,
    full_image_path    TEXT NOT NULL,
    vehicle_image_path TEXT NOT NULL,
    plate_image_path   TEXT
);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events (timestamp);
CREATE INDEX IF NOT EXISTS idx_events_plate ON events (plate);
CREATE INDEX IF NOT EXISTS idx_events_color ON events (color);
CREATE INDEX IF NOT EXISTS idx_events_camera ON events (camera);
"""


@dataclass
class Event:
    id: int
    timestamp: str
    camera: str
    vehicle_type: Optional[str]
    plate: Optional[str]
    plate_confidence: Optional[float]
    color: Optional[str]
    full_image_path: str
    vehicle_image_path: str
    plate_image_path: Optional[str]

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Event":
        return cls(**{k: row[k] for k in row.keys()})


def connect(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path: str | Path) -> None:
    conn = connect(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def insert_event(
    db_path: str | Path,
    *,
    timestamp: str,
    camera: str,
    vehicle_type: Optional[str],
    plate: Optional[str],
    plate_confidence: Optional[float],
    color: Optional[str],
    full_image_path: str,
    vehicle_image_path: str,
    plate_image_path: Optional[str],
) -> int:
    conn = connect(db_path)
    try:
        cur = conn.execute(
            """
            INSERT INTO events (
                timestamp, camera, vehicle_type, plate, plate_confidence,
                color, full_image_path, vehicle_image_path, plate_image_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                timestamp,
                camera,
                vehicle_type,
                plate,
                plate_confidence,
                color,
                full_image_path,
                vehicle_image_path,
                plate_image_path,
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def search_events(
    db_path: str | Path,
    *,
    plate: Optional[str] = None,
    color: Optional[str] = None,
    camera: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = 200,
    offset: int = 0,
) -> list[Event]:
    """Search events. `plate` does a case-insensitive substring match;
    `start`/`end` are inclusive ISO-8601 timestamp bounds."""
    clauses = []
    params: list = []

    if plate:
        clauses.append("plate LIKE ? ESCAPE '\\'")
        escaped = plate.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        params.append(f"%{escaped}%")
    if color:
        clauses.append("color = ?")
        params.append(color)
    if camera:
        clauses.append("camera = ?")
        params.append(camera)
    if start:
        clauses.append("timestamp >= ?")
        params.append(start)
    if end:
        clauses.append("timestamp <= ?")
        params.append(end)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    query = (
        f"SELECT * FROM events {where} "
        "ORDER BY timestamp DESC LIMIT ? OFFSET ?"
    )
    params.extend([limit, offset])

    conn = connect(db_path)
    try:
        rows = conn.execute(query, params).fetchall()
        return [Event.from_row(r) for r in rows]
    finally:
        conn.close()


def get_event(db_path: str | Path, event_id: int) -> Optional[Event]:
    conn = connect(db_path)
    try:
        row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
        return Event.from_row(row) if row else None
    finally:
        conn.close()


def distinct_colors(db_path: str | Path) -> list[str]:
    conn = connect(db_path)
    try:
        rows = conn.execute(
            "SELECT DISTINCT color FROM events WHERE color IS NOT NULL ORDER BY color"
        ).fetchall()
        return [r["color"] for r in rows]
    finally:
        conn.close()


def distinct_cameras(db_path: str | Path) -> list[str]:
    conn = connect(db_path)
    try:
        rows = conn.execute(
            "SELECT DISTINCT camera FROM events ORDER BY camera"
        ).fetchall()
        return [r["camera"] for r in rows]
    finally:
        conn.close()


def delete_events_before(db_path: str | Path, cutoff_iso: str) -> list[Event]:
    """Delete and return events older than cutoff_iso, so the caller can
    remove the corresponding image files from disk."""
    conn = connect(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM events WHERE timestamp < ?", (cutoff_iso,)
        ).fetchall()
        events = [Event.from_row(r) for r in rows]
        conn.execute("DELETE FROM events WHERE timestamp < ?", (cutoff_iso,))
        conn.commit()
        return events
    finally:
        conn.close()
