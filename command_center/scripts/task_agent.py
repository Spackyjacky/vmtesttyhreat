#!/usr/bin/env python3
"""
Hourly task agent — works through open tasks highest priority first.
Run via cron: 0 * * * * /usr/bin/python3 /path/to/task_agent.py
"""
import json
import sys
from pathlib import Path
from datetime import datetime

BASE      = Path(__file__).parent.parent
TASKS_JSON = BASE / "data" / "tasks.json"
TASKS_LOG  = BASE / "logs" / "tasks.log"

PRIORITIES = ["critical","high","medium","low"]

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def log(msg):
    TASKS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(TASKS_LOG, "a") as f:
        f.write(f"[{now_str()}] {msg}\n")
    print(msg)

def main():
    if not TASKS_JSON.exists():
        log("AGENT: No tasks.json found.")
        sys.exit(0)

    tasks = json.loads(TASKS_JSON.read_text()) or []
    open_tasks = [t for t in tasks if t.get("status") not in ("resolved","skipped")]

    if not open_tasks:
        log("AGENT: Task list empty — nothing to do.")
        sys.exit(0)

    # Sort by priority
    open_tasks.sort(key=lambda t: PRIORITIES.index(t.get("priority","low")))
    top = open_tasks[0]

    log(f"AGENT: Processing task #{top['id']} [{top['priority'].upper()}] — {top['title']}")
    log(f"AGENT: Description: {top.get('description','(none)')}")
    log(f"AGENT: Marking as 'in_progress' — manual review required to resolve.")

    # Mark as in_progress
    for t in tasks:
        if t.get("id") == top["id"] and t.get("status") == "open":
            t["status"] = "in_progress"
            t["last_touched"] = now_str()

    TASKS_JSON.write_text(json.dumps(tasks, indent=2))
    log(f"AGENT: Done. Task #{top['id']} is now in_progress.")

if __name__ == "__main__":
    main()
