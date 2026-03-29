# Command Center — Claude Session Instructions

## Session Bootstrap (run at start of EVERY session)

### Tier 1 — Always Load (lean, always in context)
Read these files at the start of every session without exception:
- `command_center/memory/user.md`       — Who I am, my role
- `command_center/memory/preferences.md` — How I like to work
- `command_center/memory/people.md`      — Key contacts

### Tier 2 — Main Session Only (not cron jobs or sub-agents)
If this is an interactive session (not a cron job or sub-agent task):
- Read `command_center/memory/MEMORY.md`  — Distilled long-term facts
- Read `command_center/memory/decisions.md` — Key decisions reference

### Tier 3 — On-Demand Daily Logs
- Load today's log: `command_center/memory/daily/YYYY-MM-DD.md`
- Load yesterday's log if it exists
- Do NOT load older logs automatically — search via memory_search.py if needed:
  ```
  python3 command_center/scripts/memory_search.py "your query"
  ```

### Session Types
| Session Type | Loads |
|---|---|
| Main interactive | Tier 1 + Tier 2 + today/yesterday logs |
| Cron job | Only its specific task payload |
| Sub-agent | Only the task brief passed to it |

---

## During the Session

- When the user describes a **decision**, log it:
  ```
  python3 -c "
  import sys; sys.path.insert(0,'command_center')
  from command_center import save_decision
  save_decision('DECISION', 'REASONING', 'EXPECTED OUTCOME')
  "
  ```
  Or open the Command Center UI and use the Decision Log screen.

- When something important happens, append to today's log:
  ```
  python3 -c "
  import sys; sys.path.insert(0,'command_center')
  from command_center import append_daily_log
  append_daily_log('entry text')
  "
  ```

---

## Session End — Memory Update Protocol

At the end of every interactive session, do the following:

1. **Update MEMORY.md** (`command_center/memory/MEMORY.md`) with any new facts, patterns, or lessons worth carrying forward. Keep it lean — distilled insight only.

2. **Update the relevant Tier 1 file** if anything changed:
   - New person met → `people.md`
   - Preference discovered → `preferences.md`
   - Key decision → `decisions.md`

3. **Write a closing entry** to today's daily log summarising what was accomplished.

4. **Do NOT** carry every conversation detail into MEMORY.md. Only write things that need to be remembered next session.

---

## Running the Command Center

```bash
cd /home/user/vmtesttyhreat/command_center
python3 command_center.py
```

## Cron Jobs (install with `crontab -e`)
```
# Decision review — daily at 9am
0 9 * * * /usr/bin/python3 /home/user/vmtesttyhreat/command_center/scripts/decision_review.py >> /home/user/vmtesttyhreat/command_center/logs/decision_review.log 2>&1

# Task agent — hourly
0 * * * * /usr/bin/python3 /home/user/vmtesttyhreat/command_center/scripts/task_agent.py >> /home/user/vmtesttyhreat/command_center/logs/tasks.log 2>&1
```

## Check Reviews
```bash
/home/user/vmtesttyhreat/command_center/scripts/review.sh
```
