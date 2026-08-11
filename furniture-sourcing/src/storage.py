import sqlite3
from typing import List

from .models import Listing


def init_db(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS listings (
            source TEXT NOT NULL,
            external_id TEXT NOT NULL,
            title TEXT,
            price REAL,
            currency TEXT,
            url TEXT,
            location TEXT,
            image_url TEXT,
            search_term TEXT,
            first_seen TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (source, external_id)
        )
        """
    )
    conn.commit()
    return conn


def upsert_listings(conn: sqlite3.Connection, listings: List[Listing]) -> List[Listing]:
    """Insert listings not already in the DB. Returns the ones that were new."""
    new_listings = []
    for listing in listings:
        cur = conn.execute(
            "SELECT 1 FROM listings WHERE source = ? AND external_id = ?",
            (listing.source, listing.external_id),
        )
        if cur.fetchone() is None:
            conn.execute(
                """
                INSERT INTO listings
                    (source, external_id, title, price, currency, url, location, image_url, search_term)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    listing.source,
                    listing.external_id,
                    listing.title,
                    listing.price,
                    listing.currency,
                    listing.url,
                    listing.location,
                    listing.image_url,
                    listing.search_term,
                ),
            )
            new_listings.append(listing)
    conn.commit()
    return new_listings


def get_recent(conn: sqlite3.Connection, limit: int = 50):
    cur = conn.execute(
        "SELECT * FROM listings ORDER BY first_seen DESC LIMIT ?", (limit,)
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]
