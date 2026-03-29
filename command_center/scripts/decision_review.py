#!/usr/bin/env python3
"""
Daily decision review checker.
Run via cron: 0 9 * * * /usr/bin/python3 /path/to/decision_review.py
"""
import csv
from pathlib import Path
from datetime import datetime

BASE          = Path(__file__).parent.parent
DECISIONS_CSV = BASE / "data" / "decisions.csv"
REVIEW_FLAG   = BASE / "data" / "review_due.txt"

def today_str():
    return datetime.now().strftime("%Y-%m-%d")

def main():
    if not DECISIONS_CSV.exists():
        print("No decisions.csv found.")
        return

    flagged = []
    with open(DECISIONS_CSV, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("review_date","") <= today_str() and row.get("status","") == "active":
                flagged.append(row)

    if not flagged:
        print(f"[{today_str()}] No decisions due for review.")
        REVIEW_FLAG.write_text("")
        return

    print(f"[{today_str()}] ⚠  {len(flagged)} decision(s) due for review:")
    lines = [f"[{today_str()}] REVIEW DUE: {len(flagged)} decision(s)\n"]
    for r in flagged:
        msg = f"  • {r['date']}: {r['decision'][:60]} (review: {r['review_date']})"
        print(msg)
        lines.append(msg + "\n")

    REVIEW_FLAG.write_text("".join(lines))
    print(f"\nFlag file written to: {REVIEW_FLAG}")

if __name__ == "__main__":
    main()
