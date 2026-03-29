"""
Command Center - Personal Performance System
Black/Orange terminal aesthetic
"""

import json
import csv
import os
import sys
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import (
    Header, Footer, Static, ListView, ListItem, Label,
    Input, Button, TextArea, Select, DataTable, Markdown
)
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.screen import Screen, ModalScreen
from textual.binding import Binding
from textual import events
from rich.text import Text

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE = Path(__file__).parent
MEMORY_DIR = BASE / "memory"
DATA_DIR   = BASE / "data"
LOGS_DIR   = BASE / "logs"
DAILY_DIR  = MEMORY_DIR / "daily"

DECISIONS_CSV = DATA_DIR / "decisions.csv"
TASKS_JSON    = DATA_DIR / "tasks.json"
TASKS_LOG     = LOGS_DIR / "tasks.log"
MEMORY_DB     = DATA_DIR / "memory.db"

for d in [MEMORY_DIR, DATA_DIR, LOGS_DIR, DAILY_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Helpers ────────────────────────────────────────────────────────────────────
def today_str():
    return datetime.now().strftime("%Y-%m-%d")

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def load_tasks():
    if not TASKS_JSON.exists():
        return []
    try:
        return json.loads(TASKS_JSON.read_text()) or []
    except Exception:
        return []

def save_tasks(tasks):
    TASKS_JSON.write_text(json.dumps(tasks, indent=2))

def log_task(msg):
    TASKS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(TASKS_LOG, "a") as f:
        f.write(f"[{now_str()}] {msg}\n")

def load_decisions():
    rows = []
    if not DECISIONS_CSV.exists():
        return rows
    with open(DECISIONS_CSV, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

def save_decision(decision, reasoning, expected_outcome):
    date = today_str()
    review_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    fieldnames = ["date","decision","reasoning","expected_outcome","review_date","status"]
    write_header = not DECISIONS_CSV.exists() or DECISIONS_CSV.stat().st_size == 0
    with open(DECISIONS_CSV, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow({
            "date": date,
            "decision": decision,
            "reasoning": reasoning,
            "expected_outcome": expected_outcome,
            "review_date": review_date,
            "status": "active"
        })

def get_flagged_decisions():
    today = today_str()
    return [r for r in load_decisions() if r.get("review_date","") <= today and r.get("status","") == "active"]

def get_daily_log_path(date_str=None):
    if date_str is None:
        date_str = today_str()
    return DAILY_DIR / f"{date_str}.md"

def append_daily_log(entry):
    path = get_daily_log_path()
    with open(path, "a") as f:
        f.write(f"\n## {now_str()}\n{entry}\n")

def read_recent_logs():
    today = today_str()
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    content = ""
    for d in [yesterday, today]:
        p = get_daily_log_path(d)
        if p.exists():
            content += f"\n---\n# {d}\n" + p.read_text()
    return content or "_No recent log entries._"

# ── SQLite memory index ────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(MEMORY_DB)
    conn.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts
        USING fts5(date, category, content)""")
    conn.commit()
    conn.close()

def index_memory(category, content):
    conn = sqlite3.connect(MEMORY_DB)
    conn.execute("INSERT INTO memory_fts VALUES (?,?,?)", (today_str(), category, content))
    conn.commit()
    conn.close()

def search_memory(query):
    conn = sqlite3.connect(MEMORY_DB)
    rows = conn.execute(
        "SELECT date, category, content FROM memory_fts WHERE memory_fts MATCH ? ORDER BY rank",
        (query,)
    ).fetchall()
    conn.close()
    return rows

init_db()

# ── CSS ────────────────────────────────────────────────────────────────────────
CSS = """
Screen {
    background: #0a0a0a;
    color: #ff8c00;
}

Header {
    background: #0a0a0a;
    color: #ff8c00;
    border-bottom: solid #ff8c00;
    text-style: bold;
}

Footer {
    background: #0a0a0a;
    color: #ff6600;
    border-top: solid #ff6600;
}

.panel {
    background: #0d0d0d;
    border: solid #ff6600;
    padding: 1 2;
    margin: 0 1;
}

.panel-title {
    color: #ff8c00;
    text-style: bold;
    text-align: center;
    border-bottom: solid #ff4500;
    margin-bottom: 1;
    padding-bottom: 1;
}

.menu-item {
    background: #0d0d0d;
    color: #ff8c00;
    padding: 1 3;
    border: solid #ff4500;
    margin: 0 1 1 1;
    text-align: center;
}

.menu-item:hover {
    background: #1a0d00;
    border: solid #ff8c00;
    color: #ffaa00;
}

.menu-item:focus {
    background: #ff4500;
    color: #000000;
    border: solid #ffaa00;
}

Button {
    background: #1a0800;
    color: #ff8c00;
    border: solid #ff6600;
    min-width: 14;
}

Button:hover {
    background: #ff4500;
    color: #000000;
}

Button.-primary {
    background: #ff4500;
    color: #000000;
    border: solid #ff8c00;
    text-style: bold;
}

Input {
    background: #0d0d0d;
    color: #ff8c00;
    border: solid #ff6600;
}

Input:focus {
    border: solid #ffaa00;
}

TextArea {
    background: #0d0d0d;
    color: #ff8c00;
    border: solid #ff6600;
}

TextArea:focus {
    border: solid #ffaa00;
}

Select {
    background: #0d0d0d;
    color: #ff8c00;
    border: solid #ff6600;
}

DataTable {
    background: #0a0a0a;
    color: #ff8c00;
}

DataTable > .datatable--header {
    background: #1a0800;
    color: #ffaa00;
    text-style: bold;
}

DataTable > .datatable--cursor {
    background: #ff4500;
    color: #000000;
}

DataTable > .datatable--odd-row {
    background: #0d0500;
}

ListView {
    background: #0a0a0a;
    border: solid #ff6600;
}

ListItem {
    background: #0a0a0a;
    color: #ff8c00;
    padding: 0 1;
}

ListItem:hover {
    background: #1a0800;
}

ListItem.--highlight {
    background: #ff4500;
    color: #000000;
}

.status-ok { color: #00ff88; }
.status-warn { color: #ff8c00; }
.status-alert { color: #ff2200; }

.priority-critical { color: #ff0000; text-style: bold; }
.priority-high     { color: #ff6600; text-style: bold; }
.priority-medium   { color: #ffaa00; }
.priority-low      { color: #888888; }

Markdown {
    background: #0a0a0a;
    color: #ff8c00;
}

ScrollableContainer {
    background: #0a0a0a;
}

#dashboard_stats {
    height: auto;
}

.stat-box {
    background: #0d0500;
    border: solid #ff4500;
    padding: 1 2;
    margin: 0 1;
    min-width: 20;
    text-align: center;
}

.stat-number {
    color: #ff8c00;
    text-style: bold;
}

.divider {
    border-top: solid #ff4500;
    margin: 1 0;
}

ModalScreen {
    background: rgba(0,0,0,0.8);
    align: center middle;
}

#modal_container {
    background: #0d0d0d;
    border: solid #ff8c00;
    padding: 2 3;
    width: 70;
    height: auto;
    max-height: 40;
}

#modal_title {
    color: #ffaa00;
    text-style: bold;
    text-align: center;
    margin-bottom: 1;
}

.form-label {
    color: #ff6600;
    margin-top: 1;
}

.btn-row {
    margin-top: 1;
    height: auto;
}
"""

# ══════════════════════════════════════════════════════════════════════════════
# SCREENS
# ══════════════════════════════════════════════════════════════════════════════

class DashboardScreen(Screen):
    """Home dashboard with stats overview."""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        with ScrollableContainer():
            yield Static("▓▓▓  COMMAND CENTER  ▓▓▓", id="cc_title", classes="panel-title")
            with Horizontal(id="dashboard_stats"):
                yield self._stat_box()
            yield Static("", classes="divider")
            with Horizontal():
                with Container(classes="panel"):
                    yield Static("◆ QUICK ACTIONS", classes="panel-title")
                    yield Button("[ M ] Memory Manager",  id="goto_memory",    classes="menu-item")
                    yield Button("[ D ] Decision Log",    id="goto_decisions", classes="menu-item")
                    yield Button("[ T ] Task Manager",    id="goto_tasks",     classes="menu-item")
                    yield Button("[ L ] Daily Log",       id="goto_log",       classes="menu-item")
                    yield Button("[ S ] Memory Search",   id="goto_search",    classes="menu-item")
                with Container(classes="panel"):
                    yield Static("◆ FLAGGED FOR REVIEW", classes="panel-title")
                    yield self._flagged_widget()
                with Container(classes="panel"):
                    yield Static("◆ TODAY'S LOG", classes="panel-title")
                    yield self._today_log_widget()

    def _stat_box(self):
        tasks = load_tasks()
        open_tasks = [t for t in tasks if t.get("status") != "resolved"]
        flagged = get_flagged_decisions()
        decisions = load_decisions()
        today_log = get_daily_log_path()
        log_entries = today_log.read_text().count("##") if today_log.exists() else 0

        with Horizontal() as h:
            h.border_title = ""
        return Horizontal(
            Static(f"[b]OPEN TASKS[/b]\n[#ff8c00]{len(open_tasks)}[/]", classes="stat-box"),
            Static(f"[b]DECISIONS[/b]\n[#ff8c00]{len(decisions)}[/]", classes="stat-box"),
            Static(f"[b]REVIEW DUE[/b]\n[{'#ff2200' if flagged else '#00ff88'}]{len(flagged)}[/]", classes="stat-box"),
            Static(f"[b]LOG ENTRIES[/b]\n[#ff8c00]{log_entries}[/]", classes="stat-box"),
        )

    def _flagged_widget(self):
        flagged = get_flagged_decisions()
        if not flagged:
            return Static("[#00ff88]✓ No reviews due[/]")
        lines = []
        for r in flagged[:5]:
            lines.append(f"[#ff2200]● {r['date']}[/] {r['decision'][:40]}")
        return Static("\n".join(lines))

    def _today_log_widget(self):
        path = get_daily_log_path()
        if not path.exists():
            return Static("[#888888]No entries today[/]")
        text = path.read_text()
        lines = [l for l in text.splitlines() if l.strip()][-8:]
        return Static("\n".join(lines) or "[#888888]No entries today[/]")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        destinations = {
            "goto_memory":    MemoryScreen,
            "goto_decisions": DecisionScreen,
            "goto_tasks":     TaskScreen,
            "goto_log":       DailyLogScreen,
            "goto_search":    SearchScreen,
        }
        if event.button.id in destinations:
            self.app.push_screen(destinations[event.button.id]())


# ── Memory Screen ──────────────────────────────────────────────────────────────
class MemoryScreen(Screen):
    BINDINGS = [Binding("escape", "pop_screen", "Back")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        with ScrollableContainer():
            yield Static("◆ MEMORY MANAGER", classes="panel-title")
            with Horizontal():
                with Container(classes="panel"):
                    yield Static("MEMORY FILES", classes="panel-title")
                    yield ListView(
                        ListItem(Label("user.md        — Identity")),
                        ListItem(Label("people.md      — Contacts")),
                        ListItem(Label("preferences.md — Prefs")),
                        ListItem(Label("decisions.md   — Key Decisions")),
                        ListItem(Label("MEMORY.md      — Long-term Facts")),
                        id="mem_file_list"
                    )
                    yield Button("Open Selected", id="open_mem_file", classes="menu-item")
                with Container(classes="panel"):
                    yield Static("QUICK LOG TO TODAY", classes="panel-title")
                    yield Static("Category:", classes="form-label")
                    yield Select(
                        [("General","general"),("Decision","decision"),
                         ("People","people"),("Task","task"),("Note","note")],
                        id="log_category", value="general"
                    )
                    yield Static("Entry:", classes="form-label")
                    yield TextArea(id="log_entry")
                    yield Button("Save to Daily Log + Index", id="save_log", classes="menu-item")
            yield Static("", classes="divider")
            yield Static("◆ RECENT MEMORY (Today + Yesterday)", classes="panel-title")
            yield Markdown(read_recent_logs(), id="recent_log_view")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save_log":
            entry = self.query_one("#log_entry", TextArea).text.strip()
            cat = self.query_one("#log_category", Select).value
            if entry:
                append_daily_log(f"**[{cat}]** {entry}")
                index_memory(cat, entry)
                self.query_one("#log_entry", TextArea).clear()
                self.query_one("#recent_log_view", Markdown).update(read_recent_logs())
                self.notify("Logged and indexed.", severity="information")
        elif event.button.id == "open_mem_file":
            files = ["user.md","people.md","preferences.md","decisions.md","MEMORY.md"]
            idx = self.query_one("#mem_file_list", ListView).index
            if idx is not None and idx < len(files):
                self.app.push_screen(FileEditScreen(MEMORY_DIR / files[idx]))

    def action_pop_screen(self):
        self.app.pop_screen()


# ── File Editor ────────────────────────────────────────────────────────────────
class FileEditScreen(Screen):
    BINDINGS = [Binding("escape", "pop_screen", "Back")]

    def __init__(self, path: Path):
        super().__init__()
        self.path = path

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        yield Static(f"◆ EDITING: {self.path.name}", classes="panel-title")
        yield TextArea(self.path.read_text() if self.path.exists() else "", id="file_editor")
        with Horizontal(classes="btn-row"):
            yield Button("Save", id="save_file", classes="-primary")
            yield Button("Cancel", id="cancel_edit")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save_file":
            content = self.query_one("#file_editor", TextArea).text
            self.path.write_text(content)
            self.notify(f"Saved {self.path.name}", severity="information")
            self.app.pop_screen()
        elif event.button.id == "cancel_edit":
            self.app.pop_screen()

    def action_pop_screen(self):
        self.app.pop_screen()


# ── Decision Screen ────────────────────────────────────────────────────────────
class DecisionScreen(Screen):
    BINDINGS = [Binding("escape", "pop_screen", "Back")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        with ScrollableContainer():
            yield Static("◆ DECISION LOG", classes="panel-title")
            with Container(classes="panel"):
                yield Static("LOG NEW DECISION", classes="panel-title")
                yield Static("Decision:", classes="form-label")
                yield Input(placeholder="What did you decide?", id="dec_decision")
                yield Static("Reasoning:", classes="form-label")
                yield Input(placeholder="Why did you make this decision?", id="dec_reasoning")
                yield Static("Expected Outcome:", classes="form-label")
                yield Input(placeholder="What do you expect to happen?", id="dec_outcome")
                yield Button("Log Decision (30-day review auto-set)", id="log_decision", classes="-primary")
            yield Static("", classes="divider")
            yield Static("◆ DECISION HISTORY", classes="panel-title")
            yield self._build_table()
            flagged = get_flagged_decisions()
            if flagged:
                yield Static(f"[#ff2200]⚠  {len(flagged)} DECISION(S) DUE FOR REVIEW[/]")
                yield Button("Mark Selected as Reviewed", id="mark_reviewed")

    def _build_table(self):
        table = DataTable(id="decisions_table")
        table.add_columns("Date", "Decision", "Review Date", "Status")
        for row in load_decisions():
            status = row.get("status","active")
            style = "#ff2200" if (row.get("review_date","") <= today_str() and status == "active") else "#ff8c00"
            table.add_row(
                row.get("date",""),
                row.get("decision","")[:50],
                row.get("review_date",""),
                f"[{style}]{status}[/]"
            )
        return table

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "log_decision":
            dec      = self.query_one("#dec_decision", Input).value.strip()
            reason   = self.query_one("#dec_reasoning", Input).value.strip()
            outcome  = self.query_one("#dec_outcome", Input).value.strip()
            if dec:
                save_decision(dec, reason, outcome)
                index_memory("decision", f"{dec} | {reason} | {outcome}")
                append_daily_log(f"**[decision]** {dec}")
                for fid in ["#dec_decision","#dec_reasoning","#dec_outcome"]:
                    self.query_one(fid, Input).value = ""
                self.notify("Decision logged. Review in 30 days.", severity="information")
                self.refresh(recompose=True)
        elif event.button.id == "mark_reviewed":
            rows = load_decisions()
            today = today_str()
            updated = []
            for r in rows:
                if r.get("review_date","") <= today and r.get("status","") == "active":
                    r["status"] = "reviewed"
                updated.append(r)
            if rows:
                with open(DECISIONS_CSV, "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=["date","decision","reasoning","expected_outcome","review_date","status"])
                    writer.writeheader()
                    writer.writerows(updated)
            self.notify("Flagged decisions marked as reviewed.", severity="information")
            self.refresh(recompose=True)

    def action_pop_screen(self):
        self.app.pop_screen()


# ── Task Screen ────────────────────────────────────────────────────────────────
PRIORITIES = ["critical","high","medium","low"]
PRIORITY_COLOURS = {"critical":"#ff0000","high":"#ff6600","medium":"#ffaa00","low":"#888888"}

class AddTaskModal(ModalScreen):
    def __init__(self, task=None):
        super().__init__()
        self.task = task  # None = new, dict = edit

    def compose(self) -> ComposeResult:
        is_edit = self.task is not None
        with Container(id="modal_container"):
            yield Static("◆ EDIT TASK" if is_edit else "◆ ADD TASK", id="modal_title")
            yield Static("Title:", classes="form-label")
            yield Input(value=self.task.get("title","") if is_edit else "", id="task_title")
            yield Static("Description:", classes="form-label")
            yield Input(value=self.task.get("description","") if is_edit else "", id="task_desc")
            yield Static("Priority:", classes="form-label")
            yield Select(
                [(p.upper(), p) for p in PRIORITIES],
                id="task_priority",
                value=self.task.get("priority","medium") if is_edit else "medium"
            )
            with Horizontal(classes="btn-row"):
                yield Button("Save", id="modal_save", classes="-primary")
                yield Button("Cancel", id="modal_cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "modal_save":
            title    = self.query_one("#task_title", Input).value.strip()
            desc     = self.query_one("#task_desc", Input).value.strip()
            priority = self.query_one("#task_priority", Select).value
            if title:
                self.dismiss({"title": title, "description": desc, "priority": priority})
        elif event.button.id == "modal_cancel":
            self.dismiss(None)


class TaskScreen(Screen):
    BINDINGS = [
        Binding("escape", "pop_screen", "Back"),
        Binding("a", "add_task", "Add"),
        Binding("e", "edit_task", "Edit"),
        Binding("d", "delete_task", "Delete"),
        Binding("r", "resolve_task", "Resolve"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        with Container(classes="panel"):
            yield Static("◆ TASK MANAGER  [dim]a=add  e=edit  d=delete  r=resolve[/]", classes="panel-title")
            yield self._build_table()
        with Horizontal(classes="btn-row"):
            yield Button("Add Task [A]",     id="btn_add",     classes="menu-item")
            yield Button("Edit Task [E]",    id="btn_edit",    classes="menu-item")
            yield Button("Delete Task [D]",  id="btn_delete",  classes="menu-item")
            yield Button("Resolve Task [R]", id="btn_resolve", classes="menu-item")

    def _build_table(self):
        table = DataTable(id="tasks_table", cursor_type="row")
        table.add_columns("ID", "Priority", "Title", "Description", "Status", "Created")
        for t in sorted(load_tasks(), key=lambda x: PRIORITIES.index(x.get("priority","low"))):
            c = PRIORITY_COLOURS.get(t.get("priority","low"), "#ff8c00")
            status_c = "#00ff88" if t.get("status") == "resolved" else "#ff8c00"
            table.add_row(
                str(t.get("id",""))[:4],
                f"[{c}]{t.get('priority','').upper()}[/]",
                t.get("title","")[:35],
                t.get("description","")[:35],
                f"[{status_c}]{t.get('status','open')}[/]",
                t.get("created","")[:10],
            )
        return table

    def _selected_task_id(self):
        table = self.query_one("#tasks_table", DataTable)
        if table.cursor_row < 0:
            return None
        tasks = sorted(load_tasks(), key=lambda x: PRIORITIES.index(x.get("priority","low")))
        if table.cursor_row < len(tasks):
            return tasks[table.cursor_row].get("id")
        return None

    def on_button_pressed(self, event: Button.Pressed) -> None:
        actions = {
            "btn_add":     self.action_add_task,
            "btn_edit":    self.action_edit_task,
            "btn_delete":  self.action_delete_task,
            "btn_resolve": self.action_resolve_task,
        }
        if event.button.id in actions:
            actions[event.button.id]()

    def action_add_task(self):
        def handle(result):
            if result:
                tasks = load_tasks()
                new_id = max((t.get("id",0) for t in tasks), default=0) + 1
                tasks.append({
                    "id": new_id,
                    "title": result["title"],
                    "description": result["description"],
                    "priority": result["priority"],
                    "status": "open",
                    "created": today_str(),
                    "resolved": None
                })
                save_tasks(tasks)
                log_task(f"ADDED [{result['priority'].upper()}] {result['title']}")
                self.refresh(recompose=True)
                self.notify("Task added.", severity="information")
        self.app.push_screen(AddTaskModal(), handle)

    def action_edit_task(self):
        tid = self._selected_task_id()
        if tid is None:
            self.notify("Select a task first.", severity="warning")
            return
        tasks = load_tasks()
        task = next((t for t in tasks if t.get("id") == tid), None)
        if not task:
            return
        def handle(result):
            if result:
                for t in tasks:
                    if t.get("id") == tid:
                        t["title"]       = result["title"]
                        t["description"] = result["description"]
                        t["priority"]    = result["priority"]
                save_tasks(tasks)
                log_task(f"EDITED task #{tid}: {result['title']}")
                self.refresh(recompose=True)
                self.notify("Task updated.", severity="information")
        self.app.push_screen(AddTaskModal(task=task), handle)

    def action_delete_task(self):
        tid = self._selected_task_id()
        if tid is None:
            self.notify("Select a task first.", severity="warning")
            return
        tasks = [t for t in load_tasks() if t.get("id") != tid]
        save_tasks(tasks)
        log_task(f"DELETED task #{tid}")
        self.refresh(recompose=True)
        self.notify("Task deleted.", severity="warning")

    def action_resolve_task(self):
        tid = self._selected_task_id()
        if tid is None:
            self.notify("Select a task first.", severity="warning")
            return
        tasks = load_tasks()
        for t in tasks:
            if t.get("id") == tid:
                t["status"]   = "resolved"
                t["resolved"] = today_str()
        save_tasks(tasks)
        log_task(f"RESOLVED task #{tid}")
        self.refresh(recompose=True)
        self.notify("Task resolved!", severity="information")

    def action_pop_screen(self):
        self.app.pop_screen()


# ── Daily Log Screen ───────────────────────────────────────────────────────────
class DailyLogScreen(Screen):
    BINDINGS = [Binding("escape", "pop_screen", "Back")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        with ScrollableContainer():
            yield Static("◆ DAILY LOG", classes="panel-title")
            with Container(classes="panel"):
                yield Static("Quick Entry:", classes="form-label")
                yield TextArea(id="quick_entry")
                yield Button("Append to Today's Log", id="append_log", classes="-primary")
            yield Static("", classes="divider")
            yield Markdown(read_recent_logs(), id="log_view")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "append_log":
            entry = self.query_one("#quick_entry", TextArea).text.strip()
            if entry:
                append_daily_log(entry)
                self.query_one("#quick_entry", TextArea).clear()
                self.query_one("#log_view", Markdown).update(read_recent_logs())
                self.notify("Logged.", severity="information")

    def action_pop_screen(self):
        self.app.pop_screen()


# ── Search Screen ──────────────────────────────────────────────────────────────
class SearchScreen(Screen):
    BINDINGS = [Binding("escape", "pop_screen", "Back")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        with Container(classes="panel"):
            yield Static("◆ MEMORY SEARCH (Full-Text)", classes="panel-title")
            with Horizontal():
                yield Input(placeholder="Search memory index...", id="search_input")
                yield Button("Search", id="do_search", classes="-primary")
            yield Static("", id="search_results")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "do_search":
            self._do_search()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._do_search()

    def _do_search(self):
        q = self.query_one("#search_input", Input).value.strip()
        if not q:
            return
        results = search_memory(q)
        if not results:
            self.query_one("#search_results", Static).update("[#888888]No results found.[/]")
        else:
            lines = [f"[#ffaa00]{r[0]}[/] [[#ff6600]{r[1]}[/]] {r[2]}" for r in results[:20]]
            self.query_one("#search_results", Static).update("\n".join(lines))

    def action_pop_screen(self):
        self.app.pop_screen()


# ══════════════════════════════════════════════════════════════════════════════
# APP
# ══════════════════════════════════════════════════════════════════════════════

class CommandCenter(App):
    TITLE = "COMMAND CENTER"
    SUB_TITLE = "Personal Performance System"
    CSS = CSS
    BINDINGS = [
        Binding("ctrl+q", "quit",            "Quit"),
        Binding("ctrl+h", "push_home",       "Home"),
        Binding("ctrl+m", "push_memory",     "Memory"),
        Binding("ctrl+d", "push_decisions",  "Decisions"),
        Binding("ctrl+t", "push_tasks",      "Tasks"),
        Binding("ctrl+l", "push_log",        "Log"),
        Binding("ctrl+s", "push_search",     "Search"),
    ]

    def on_mount(self) -> None:
        self.push_screen(DashboardScreen())

    def action_push_home(self):       self.push_screen(DashboardScreen())
    def action_push_memory(self):     self.push_screen(MemoryScreen())
    def action_push_decisions(self):  self.push_screen(DecisionScreen())
    def action_push_tasks(self):      self.push_screen(TaskScreen())
    def action_push_log(self):        self.push_screen(DailyLogScreen())
    def action_push_search(self):     self.push_screen(SearchScreen())


if __name__ == "__main__":
    CommandCenter().run()
