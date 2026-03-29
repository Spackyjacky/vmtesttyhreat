#!/usr/bin/env python3
"""
CLI memory search utility.
Usage: python3 memory_search.py "your query"
"""
import sys
import sqlite3
from pathlib import Path

BASE      = Path(__file__).parent.parent
MEMORY_DB = BASE / "data" / "memory.db"

def search(query):
    if not MEMORY_DB.exists():
        print("No memory index found.")
        return
    conn = sqlite3.connect(MEMORY_DB)
    rows = conn.execute(
        "SELECT date, category, content FROM memory_fts WHERE memory_fts MATCH ? ORDER BY rank",
        (query,)
    ).fetchall()
    conn.close()
    if not rows:
        print("No results found.")
        return
    for date, cat, content in rows:
        print(f"[{date}] [{cat}] {content}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: memory_search.py <query>")
        sys.exit(1)
    search(" ".join(sys.argv[1:]))
