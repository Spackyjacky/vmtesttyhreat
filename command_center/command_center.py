"""
Command Center — Personal Performance System
Tkinter rebuild — black/orange terminal aesthetic
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json, csv, os, sqlite3, threading
from datetime import datetime, timedelta
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE       = Path(__file__).parent
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

# ── Colours / Fonts ────────────────────────────────────────────────────────────
BG        = "#0a0a0a"
BG2       = "#0f0f0f"
BG3       = "#141414"
PANEL     = "#111111"
ORANGE    = "#ff8c00"
ORANGE2   = "#ff6600"
ORANGE3   = "#ff4500"
ORANGE_DIM= "#994400"
GREEN     = "#00ff88"
RED       = "#ff2200"
GREY      = "#555555"
WHITE     = "#e0e0e0"

FONT_MONO   = ("Consolas", 10)
FONT_MONO_S = ("Consolas", 9)
FONT_MONO_L = ("Consolas", 12)
FONT_BOLD   = ("Consolas", 10, "bold")
FONT_BOLD_L = ("Consolas", 13, "bold")
FONT_TITLE  = ("Consolas", 16, "bold")

PRIORITIES      = ["critical", "high", "medium", "low"]
PRIORITY_COLOUR = {"critical": RED, "high": ORANGE3, "medium": ORANGE, "low": GREY}

# ── Data helpers ───────────────────────────────────────────────────────────────
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
    with open(TASKS_LOG, "a") as f:
        f.write(f"[{now_str()}] {msg}\n")

def load_decisions():
    if not DECISIONS_CSV.exists():
        return []
    with open(DECISIONS_CSV, newline="") as f:
        return list(csv.DictReader(f))

def save_decision(decision, reasoning, expected_outcome):
    review = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    fieldnames = ["date","decision","reasoning","expected_outcome","review_date","status"]
    write_header = not DECISIONS_CSV.exists() or DECISIONS_CSV.stat().st_size == 0
    with open(DECISIONS_CSV, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            w.writeheader()
        w.writerow({"date": today_str(), "decision": decision,
                    "reasoning": reasoning, "expected_outcome": expected_outcome,
                    "review_date": review, "status": "active"})

def get_flagged():
    return [r for r in load_decisions()
            if r.get("review_date","") <= today_str() and r.get("status","") == "active"]

def get_daily_path(date_str=None):
    return DAILY_DIR / f"{date_str or today_str()}.md"

def append_daily_log(entry):
    with open(get_daily_path(), "a") as f:
        f.write(f"\n## {now_str()}\n{entry}\n")

def read_recent_logs():
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    out = ""
    for d in [yesterday, today_str()]:
        p = get_daily_path(d)
        if p.exists():
            out += f"\n─── {d} ───\n" + p.read_text()
    return out.strip() or "No log entries yet."

# ── SQLite FTS ─────────────────────────────────────────────────────────────────
def init_db():
    c = sqlite3.connect(MEMORY_DB)
    c.execute("CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(date, category, content)")
    c.commit(); c.close()

def index_memory(category, content):
    c = sqlite3.connect(MEMORY_DB)
    c.execute("INSERT INTO memory_fts VALUES (?,?,?)", (today_str(), category, content))
    c.commit(); c.close()

def search_memory(query):
    c = sqlite3.connect(MEMORY_DB)
    rows = c.execute("SELECT date,category,content FROM memory_fts WHERE memory_fts MATCH ? ORDER BY rank", (query,)).fetchall()
    c.close()
    return rows

init_db()

# ══════════════════════════════════════════════════════════════════════════════
# REUSABLE WIDGETS
# ══════════════════════════════════════════════════════════════════════════════

def styled_frame(parent, **kw):
    return tk.Frame(parent, bg=kw.pop("bg", PANEL), **kw)

def styled_label(parent, text, size=10, bold=False, colour=ORANGE, **kw):
    weight = "bold" if bold else "normal"
    return tk.Label(parent, text=text, bg=kw.pop("bg", PANEL), fg=colour,
                    font=("Consolas", size, weight), **kw)

def styled_button(parent, text, command, width=20, colour=ORANGE, bg=BG3, **kw):
    return tk.Button(parent, text=text, command=command, bg=bg, fg=colour,
                     font=FONT_BOLD, relief="flat", bd=0,
                     activebackground=ORANGE3, activeforeground=BG,
                     cursor="hand2", width=width, pady=4, **kw)

def styled_entry(parent, textvariable=None, width=40, **kw):
    return tk.Entry(parent, textvariable=textvariable, width=width,
                    bg=BG3, fg=ORANGE, insertbackground=ORANGE,
                    font=FONT_MONO, relief="flat", bd=4, **kw)

def styled_text(parent, height=6, width=60, **kw):
    return tk.Text(parent, height=height, width=width,
                   bg=BG3, fg=ORANGE, insertbackground=ORANGE,
                   font=FONT_MONO, relief="flat", bd=4,
                   selectbackground=ORANGE3, selectforeground=BG, **kw)

def separator(parent, pady=6):
    tk.Frame(parent, bg=ORANGE3, height=1).pack(fill="x", pady=pady)

def section_title(parent, text):
    f = tk.Frame(parent, bg=PANEL)
    f.pack(fill="x", pady=(10,4))
    tk.Label(f, text=f"◆ {text}", bg=PANEL, fg=ORANGE,
             font=FONT_BOLD_L, anchor="w").pack(side="left", padx=6)
    tk.Frame(f, bg=ORANGE3, height=1).pack(side="left", fill="x", expand=True, padx=6)

def make_treeview(parent, columns, heights=12):
    style = ttk.Style()
    style.configure("CC.Treeview",
        background=BG2, foreground=ORANGE, fieldbackground=BG2,
        font=FONT_MONO_S, rowheight=22, borderwidth=0)
    style.configure("CC.Treeview.Heading",
        background=BG3, foreground=ORANGE, font=FONT_BOLD,
        relief="flat", borderwidth=0)
    style.map("CC.Treeview",
        background=[("selected", ORANGE3)],
        foreground=[("selected", BG)])
    style.map("CC.Treeview.Heading", background=[("active", BG3)])

    frame = tk.Frame(parent, bg=BG2, highlightbackground=ORANGE3, highlightthickness=1)
    frame.pack(fill="both", expand=True, padx=6, pady=4)

    tv = ttk.Treeview(frame, columns=columns, show="headings",
                      style="CC.Treeview", height=heights, selectmode="browse")
    vsb = tk.Scrollbar(frame, orient="vertical", command=tv.yview,
                       bg=BG3, troughcolor=BG, width=10)
    tv.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")
    tv.pack(fill="both", expand=True)
    return tv


# ══════════════════════════════════════════════════════════════════════════════
# SCREENS — each is a tk.Frame swapped into the content area
# ══════════════════════════════════════════════════════════════════════════════

class DashboardScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=PANEL)
        self.app = app
        self._build()

    def _build(self):
        # Title
        tk.Label(self, text="▓▓  COMMAND CENTER  ▓▓", bg=PANEL, fg=ORANGE,
                 font=FONT_TITLE).pack(pady=(18,4))
        tk.Label(self, text="Personal Performance System", bg=PANEL, fg=ORANGE_DIM,
                 font=FONT_MONO_S).pack()
        tk.Frame(self, bg=ORANGE3, height=1).pack(fill="x", padx=20, pady=10)

        # Stats row
        stats_frame = tk.Frame(self, bg=PANEL)
        stats_frame.pack(fill="x", padx=20, pady=4)
        self._stat(stats_frame, "OPEN TASKS",   self._open_tasks())
        self._stat(stats_frame, "DECISIONS",    str(len(load_decisions())))
        self._stat(stats_frame, "REVIEW DUE",   str(len(get_flagged())), alert=len(get_flagged())>0)
        self._stat(stats_frame, "TODAY'S DATE", today_str(), colour=ORANGE_DIM)

        tk.Frame(self, bg=ORANGE3, height=1).pack(fill="x", padx=20, pady=10)

        # Lower panels
        lower = tk.Frame(self, bg=PANEL)
        lower.pack(fill="both", expand=True, padx=20, pady=4)
        lower.columnconfigure(0, weight=1)
        lower.columnconfigure(1, weight=1)
        lower.columnconfigure(2, weight=1)

        self._panel_quick(lower)
        self._panel_flagged(lower)
        self._panel_log(lower)

    def _stat(self, parent, label, value, alert=False, colour=None):
        fg = RED if alert else (colour or GREEN)
        box = tk.Frame(parent, bg=BG3, highlightbackground=ORANGE3, highlightthickness=1)
        box.pack(side="left", expand=True, fill="x", padx=6, ipady=8)
        tk.Label(box, text=label, bg=BG3, fg=ORANGE_DIM, font=FONT_MONO_S).pack(pady=(6,0))
        tk.Label(box, text=value,  bg=BG3, fg=fg, font=FONT_BOLD_L).pack(pady=(0,6))

    def _open_tasks(self):
        return str(len([t for t in load_tasks() if t.get("status") not in ("resolved",)]))

    def _panel_quick(self, parent):
        f = tk.Frame(parent, bg=BG3, highlightbackground=ORANGE3, highlightthickness=1)
        f.grid(row=0, column=0, sticky="nsew", padx=6, pady=4)
        tk.Label(f, text="◆ QUICK ACTIONS", bg=BG3, fg=ORANGE, font=FONT_BOLD).pack(pady=(10,6))
        tk.Frame(f, bg=ORANGE3, height=1).pack(fill="x", padx=6)
        actions = [
            (" Memory Manager", lambda: self.app.show("memory")),
            (" Decision Log",   lambda: self.app.show("decisions")),
            (" Task Manager",   lambda: self.app.show("tasks")),
            (" Daily Log",      lambda: self.app.show("log")),
            (" Memory Search",  lambda: self.app.show("search")),
        ]
        for label, cmd in actions:
            b = tk.Button(f, text=label, command=cmd, bg=BG3, fg=ORANGE,
                          font=FONT_MONO, relief="flat", anchor="w",
                          activebackground=ORANGE3, activeforeground=BG,
                          cursor="hand2", padx=14, pady=3)
            b.pack(fill="x", padx=8, pady=2)

    def _panel_flagged(self, parent):
        f = tk.Frame(parent, bg=BG3, highlightbackground=ORANGE3, highlightthickness=1)
        f.grid(row=0, column=1, sticky="nsew", padx=6, pady=4)
        tk.Label(f, text="◆ FLAGGED FOR REVIEW", bg=BG3, fg=ORANGE, font=FONT_BOLD).pack(pady=(10,6))
        tk.Frame(f, bg=ORANGE3, height=1).pack(fill="x", padx=6)
        flagged = get_flagged()
        if not flagged:
            tk.Label(f, text="\n✓  No reviews due", bg=BG3, fg=GREEN, font=FONT_MONO).pack(pady=10)
        else:
            for r in flagged[:6]:
                row = tk.Frame(f, bg=BG3)
                row.pack(fill="x", padx=8, pady=2)
                tk.Label(row, text="●", bg=BG3, fg=RED, font=FONT_MONO_S).pack(side="left")
                tk.Label(row, text=f" {r['date']}  {r['decision'][:32]}",
                         bg=BG3, fg=ORANGE, font=FONT_MONO_S, anchor="w").pack(side="left")

    def _panel_log(self, parent):
        f = tk.Frame(parent, bg=BG3, highlightbackground=ORANGE3, highlightthickness=1)
        f.grid(row=0, column=2, sticky="nsew", padx=6, pady=4)
        tk.Label(f, text="◆ TODAY'S LOG", bg=BG3, fg=ORANGE, font=FONT_BOLD).pack(pady=(10,6))
        tk.Frame(f, bg=ORANGE3, height=1).pack(fill="x", padx=6)
        p = get_daily_path()
        lines = []
        if p.exists():
            lines = [l for l in p.read_text().splitlines() if l.strip()][-10:]
        txt = scrolledtext.ScrolledText(f, bg=BG3, fg=ORANGE_DIM, font=FONT_MONO_S,
                                        relief="flat", bd=0, height=10, wrap="word",
                                        state="normal")
        txt.pack(fill="both", expand=True, padx=6, pady=6)
        txt.insert("1.0", "\n".join(lines) if lines else "No entries yet.")
        txt.config(state="disabled")


# ── Memory Screen ──────────────────────────────────────────────────────────────
class MemoryScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=PANEL)
        self.app = app
        self._build()

    def _build(self):
        section_title(self, "MEMORY MANAGER")

        panes = tk.Frame(self, bg=PANEL)
        panes.pack(fill="both", expand=True, padx=10)
        panes.columnconfigure(0, weight=1)
        panes.columnconfigure(1, weight=2)

        # Left — file list
        left = tk.Frame(panes, bg=BG3, highlightbackground=ORANGE3, highlightthickness=1)
        left.grid(row=0, column=0, sticky="nsew", padx=(0,6), pady=4)
        tk.Label(left, text="MEMORY FILES", bg=BG3, fg=ORANGE, font=FONT_BOLD).pack(pady=(8,4))
        tk.Frame(left, bg=ORANGE3, height=1).pack(fill="x", padx=6)

        self.file_lb = tk.Listbox(left, bg=BG3, fg=ORANGE, font=FONT_MONO,
                                   selectbackground=ORANGE3, selectforeground=BG,
                                   relief="flat", bd=0, activestyle="none", height=8)
        files = ["user.md — Identity", "people.md — Contacts",
                 "preferences.md — Prefs", "decisions.md — Key Decisions",
                 "MEMORY.md — Long-term Facts"]
        for f in files:
            self.file_lb.insert("end", f"  {f}")
        self.file_lb.pack(fill="both", expand=True, padx=4, pady=4)
        styled_button(left, "Open & Edit Selected", self._open_file, width=22).pack(pady=8)

        # Right — quick log
        right = tk.Frame(panes, bg=BG3, highlightbackground=ORANGE3, highlightthickness=1)
        right.grid(row=0, column=1, sticky="nsew", pady=4)
        tk.Label(right, text="QUICK LOG TO TODAY", bg=BG3, fg=ORANGE, font=FONT_BOLD).pack(pady=(8,4))
        tk.Frame(right, bg=ORANGE3, height=1).pack(fill="x", padx=6)

        form = tk.Frame(right, bg=BG3)
        form.pack(fill="x", padx=10, pady=6)
        tk.Label(form, text="Category:", bg=BG3, fg=ORANGE_DIM, font=FONT_MONO_S).grid(row=0, column=0, sticky="w", pady=3)
        self.cat_var = tk.StringVar(value="general")
        cats = ["general","decision","people","task","note","win","blocker"]
        cat_menu = ttk.Combobox(form, textvariable=self.cat_var, values=cats,
                                 state="readonly", width=14, font=FONT_MONO_S)
        cat_menu.grid(row=0, column=1, sticky="w", padx=6)
        self._style_combo(cat_menu)

        tk.Label(form, text="Entry:", bg=BG3, fg=ORANGE_DIM, font=FONT_MONO_S).grid(row=1, column=0, sticky="nw", pady=3)
        self.log_entry = styled_text(form, height=4, width=45)
        self.log_entry.grid(row=1, column=1, pady=3, padx=6)
        styled_button(right, "Save to Daily Log + Index", self._save_log, width=26).pack(pady=6)

        # Recent logs
        section_title(self, "RECENT MEMORY  (Today + Yesterday)")
        self.log_view = scrolledtext.ScrolledText(
            self, bg=BG2, fg=ORANGE_DIM, font=FONT_MONO_S,
            relief="flat", bd=0, height=10, wrap="word", state="normal")
        self.log_view.pack(fill="both", expand=True, padx=10, pady=(0,8))
        self._refresh_log()

    def _style_combo(self, combo):
        style = ttk.Style()
        style.configure("CC.TCombobox", fieldbackground=BG3, background=BG3,
                         foreground=ORANGE, selectbackground=ORANGE3,
                         selectforeground=BG, font=FONT_MONO_S)
        combo.configure(style="CC.TCombobox")

    def _refresh_log(self):
        self.log_view.config(state="normal")
        self.log_view.delete("1.0", "end")
        self.log_view.insert("1.0", read_recent_logs())
        self.log_view.config(state="disabled")

    def _save_log(self):
        entry = self.log_entry.get("1.0", "end").strip()
        if not entry:
            messagebox.showwarning("Empty", "Enter something first.", parent=self)
            return
        cat = self.cat_var.get()
        append_daily_log(f"[{cat}] {entry}")
        index_memory(cat, entry)
        self.log_entry.delete("1.0", "end")
        self._refresh_log()
        self.app.status(f"Logged under [{cat}] and indexed.")

    def _open_file(self):
        sel = self.file_lb.curselection()
        if not sel:
            messagebox.showinfo("Select a file", "Click a file first.", parent=self)
            return
        names = ["user.md","people.md","preferences.md","decisions.md","MEMORY.md"]
        path = MEMORY_DIR / names[sel[0]]
        FileEditorWindow(self, path, self.app)


# ── File Editor Window ─────────────────────────────────────────────────────────
class FileEditorWindow(tk.Toplevel):
    def __init__(self, parent, path: Path, app):
        super().__init__(parent)
        self.path = path
        self.app  = app
        self.title(f"Edit — {path.name}")
        self.configure(bg=PANEL)
        self.geometry("700x500")
        self._build()

    def _build(self):
        tk.Label(self, text=f"◆ EDITING: {self.path.name}",
                 bg=PANEL, fg=ORANGE, font=FONT_BOLD_L).pack(pady=(10,4), padx=10, anchor="w")
        tk.Frame(self, bg=ORANGE3, height=1).pack(fill="x", padx=10)

        self.editor = scrolledtext.ScrolledText(
            self, bg=BG3, fg=ORANGE, insertbackground=ORANGE,
            font=FONT_MONO, relief="flat", bd=6,
            selectbackground=ORANGE3, selectforeground=BG)
        self.editor.pack(fill="both", expand=True, padx=10, pady=8)
        if self.path.exists():
            self.editor.insert("1.0", self.path.read_text())

        btn_row = tk.Frame(self, bg=PANEL)
        btn_row.pack(pady=8)
        styled_button(btn_row, "Save", self._save, width=14, bg=ORANGE3, colour=BG).pack(side="left", padx=6)
        styled_button(btn_row, "Cancel", self.destroy, width=14).pack(side="left", padx=6)

    def _save(self):
        self.path.write_text(self.editor.get("1.0","end"))
        self.app.status(f"Saved {self.path.name}")
        self.destroy()



# ── Decision Screen ────────────────────────────────────────────────────────────
class DecisionScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=PANEL)
        self.app = app
        self._build()

    def _build(self):
        section_title(self, "DECISION LOG")

        # Add form
        form_frame = tk.Frame(self, bg=BG3, highlightbackground=ORANGE3, highlightthickness=1)
        form_frame.pack(fill="x", padx=10, pady=4)
        tk.Label(form_frame, text="LOG NEW DECISION", bg=BG3, fg=ORANGE, font=FONT_BOLD).pack(pady=(8,4))
        tk.Frame(form_frame, bg=ORANGE3, height=1).pack(fill="x", padx=6)

        inner = tk.Frame(form_frame, bg=BG3)
        inner.pack(fill="x", padx=14, pady=8)
        inner.columnconfigure(1, weight=1)

        fields = [
            ("Decision:",        "What did you decide?"),
            ("Reasoning:",       "Why did you make this decision?"),
            ("Expected Outcome:","What do you expect to happen?"),
        ]
        self.dec_vars = []
        for i, (label, hint) in enumerate(fields):
            tk.Label(inner, text=label, bg=BG3, fg=ORANGE_DIM,
                     font=FONT_MONO_S, width=18, anchor="e").grid(row=i, column=0, pady=4, sticky="e")
            var = tk.StringVar()
            e = styled_entry(inner, textvariable=var, width=55)
            e.grid(row=i, column=1, pady=4, padx=(8,0), sticky="ew")
            # Placeholder
            e.insert(0, hint)
            e.config(fg=ORANGE_DIM)
            e.bind("<FocusIn>",  lambda ev, en=e, h=hint: self._clear_hint(ev, en, h))
            e.bind("<FocusOut>", lambda ev, en=e, h=hint, v=var: self._restore_hint(ev, en, h, v))
            self.dec_vars.append((var, hint))

        styled_button(form_frame, "Log Decision  (30-day review auto-set)",
                      self._log_decision, width=40, bg=ORANGE3, colour=BG).pack(pady=(0,10))

        # History table
        section_title(self, "DECISION HISTORY")

        cols = ("Date","Decision","Reasoning","Review Date","Status")
        self.tree = make_treeview(self, cols, heights=10)
        self.tree.column("Date",        width=90,  stretch=False)
        self.tree.column("Decision",    width=220, stretch=True)
        self.tree.column("Reasoning",   width=200, stretch=True)
        self.tree.column("Review Date", width=90,  stretch=False)
        self.tree.column("Status",      width=80,  stretch=False)
        for c in cols:
            self.tree.heading(c, text=c)
        self._refresh_table()

        # Action row
        btn_row = tk.Frame(self, bg=PANEL)
        btn_row.pack(pady=6)
        styled_button(btn_row, "Mark Selected as Reviewed",
                      self._mark_reviewed, width=26).pack(side="left", padx=6)
        styled_button(btn_row, "Delete Selected",
                      self._delete_decision, width=18).pack(side="left", padx=6)

        # Flagged banner
        self.flag_label = tk.Label(self, text="", bg=PANEL, fg=RED, font=FONT_BOLD)
        self.flag_label.pack()
        self._update_banner()

    def _clear_hint(self, ev, entry, hint):
        if entry.get() == hint:
            entry.delete(0, "end")
            entry.config(fg=ORANGE)

    def _restore_hint(self, ev, entry, hint, var):
        if not entry.get():
            entry.insert(0, hint)
            entry.config(fg=ORANGE_DIM)

    def _get_field(self, idx):
        var, hint = self.dec_vars[idx]
        val = var.get().strip()
        return "" if val == hint else val

    def _log_decision(self):
        dec    = self._get_field(0)
        reason = self._get_field(1)
        outcome= self._get_field(2)
        if not dec:
            messagebox.showwarning("Required", "Decision field is required.", parent=self)
            return
        save_decision(dec, reason, outcome)
        index_memory("decision", f"{dec} | {reason} | {outcome}")
        append_daily_log(f"[decision] {dec}")
        # Clear fields
        for var, hint in self.dec_vars:
            var.set(hint)
        self._refresh_table()
        self._update_banner()
        self.app.status("Decision logged. 30-day review set.")

    def _refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for r in load_decisions():
            overdue = r.get("review_date","") <= today_str() and r.get("status","") == "active"
            tag = "overdue" if overdue else "normal"
            self.tree.insert("", "end", values=(
                r.get("date",""), r.get("decision","")[:45],
                r.get("reasoning","")[:40],
                r.get("review_date",""), r.get("status","")
            ), tags=(tag,))
        self.tree.tag_configure("overdue", foreground=RED)
        self.tree.tag_configure("normal",  foreground=ORANGE)

    def _update_banner(self):
        n = len(get_flagged())
        if n:
            self.flag_label.config(text=f"  ⚠  {n} decision(s) overdue for review  ⚠")
        else:
            self.flag_label.config(text="  ✓  All decisions reviewed", fg=GREEN)

    def _mark_reviewed(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Select a decision first.", parent=self)
            return
        vals = self.tree.item(sel[0], "values")
        date_val = vals[0]
        dec_val  = vals[1]
        rows = load_decisions()
        for r in rows:
            if r.get("date") == date_val and r.get("decision","").startswith(dec_val[:30]):
                r["status"] = "reviewed"
        with open(DECISIONS_CSV, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["date","decision","reasoning","expected_outcome","review_date","status"])
            w.writeheader(); w.writerows(rows)
        self._refresh_table()
        self._update_banner()
        self.app.status("Marked as reviewed.")

    def _delete_decision(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Select a decision first.", parent=self)
            return
        if not messagebox.askyesno("Confirm", "Delete this decision?", parent=self):
            return
        vals = self.tree.item(sel[0], "values")
        rows = [r for r in load_decisions()
                if not (r.get("date") == vals[0] and r.get("decision","").startswith(vals[1][:30]))]
        with open(DECISIONS_CSV, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["date","decision","reasoning","expected_outcome","review_date","status"])
            w.writeheader(); w.writerows(rows)
        self._refresh_table()
        self._update_banner()
        self.app.status("Decision deleted.")


# ── Task Add/Edit Modal ────────────────────────────────────────────────────────
class TaskModal(tk.Toplevel):
    def __init__(self, parent, app, task=None, on_save=None):
        super().__init__(parent)
        self.app     = app
        self.task    = task
        self.on_save = on_save
        self.result  = None
        title = "Edit Task" if task else "Add Task"
        self.title(title)
        self.configure(bg=PANEL)
        self.geometry("520x300")
        self.resizable(False, False)
        self.grab_set()
        self._build()

    def _build(self):
        tk.Label(self, text=f"◆ {'EDIT' if self.task else 'ADD'} TASK",
                 bg=PANEL, fg=ORANGE, font=FONT_BOLD_L).pack(pady=(12,4), padx=16, anchor="w")
        tk.Frame(self, bg=ORANGE3, height=1).pack(fill="x", padx=16)

        form = tk.Frame(self, bg=PANEL)
        form.pack(fill="x", padx=20, pady=10)
        form.columnconfigure(1, weight=1)

        # Title
        tk.Label(form, text="Title:", bg=PANEL, fg=ORANGE_DIM,
                 font=FONT_MONO_S, width=12, anchor="e").grid(row=0, column=0, pady=6, sticky="e")
        self.title_var = tk.StringVar(value=self.task.get("title","") if self.task else "")
        styled_entry(form, textvariable=self.title_var, width=38).grid(row=0, column=1, padx=8, sticky="ew")

        # Description
        tk.Label(form, text="Description:", bg=PANEL, fg=ORANGE_DIM,
                 font=FONT_MONO_S, width=12, anchor="e").grid(row=1, column=0, pady=6, sticky="ne")
        self.desc_text = styled_text(form, height=3, width=38)
        self.desc_text.grid(row=1, column=1, padx=8, sticky="ew")
        if self.task:
            self.desc_text.insert("1.0", self.task.get("description",""))

        # Priority
        tk.Label(form, text="Priority:", bg=PANEL, fg=ORANGE_DIM,
                 font=FONT_MONO_S, width=12, anchor="e").grid(row=2, column=0, pady=6, sticky="e")
        self.prio_var = tk.StringVar(value=self.task.get("priority","medium") if self.task else "medium")
        prio_frame = tk.Frame(form, bg=PANEL)
        prio_frame.grid(row=2, column=1, padx=8, sticky="w")
        for p in PRIORITIES:
            rb = tk.Radiobutton(prio_frame, text=p.upper(), variable=self.prio_var, value=p,
                                bg=PANEL, fg=PRIORITY_COLOUR[p], selectcolor=BG3,
                                activebackground=PANEL, activeforeground=PRIORITY_COLOUR[p],
                                font=FONT_MONO_S)
            rb.pack(side="left", padx=6)

        btn_row = tk.Frame(self, bg=PANEL)
        btn_row.pack(pady=10)
        styled_button(btn_row, "Save", self._save, width=12, bg=ORANGE3, colour=BG).pack(side="left", padx=8)
        styled_button(btn_row, "Cancel", self.destroy, width=12).pack(side="left", padx=8)

    def _save(self):
        title = self.title_var.get().strip()
        if not title:
            messagebox.showwarning("Required", "Title is required.", parent=self)
            return
        self.result = {
            "title":       title,
            "description": self.desc_text.get("1.0","end").strip(),
            "priority":    self.prio_var.get(),
        }
        if self.on_save:
            self.on_save(self.result)
        self.destroy()


# ── Task Screen ────────────────────────────────────────────────────────────────
class TaskScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=PANEL)
        self.app = app
        self._build()

    def _build(self):
        section_title(self, "TASK MANAGER")

        # Toolbar
        bar = tk.Frame(self, bg=PANEL)
        bar.pack(fill="x", padx=10, pady=4)
        styled_button(bar, "+ Add Task",      self._add,     width=14, bg=ORANGE3, colour=BG).pack(side="left", padx=4)
        styled_button(bar, "✎ Edit",           self._edit,    width=10).pack(side="left", padx=4)
        styled_button(bar, "✓ Resolve",        self._resolve, width=12).pack(side="left", padx=4)
        styled_button(bar, "✕ Delete",         self._delete,  width=10).pack(side="left", padx=4)
        styled_button(bar, "↺ Refresh",        self._refresh, width=10).pack(side="right", padx=4)

        # Filter
        filter_frame = tk.Frame(self, bg=PANEL)
        filter_frame.pack(fill="x", padx=10, pady=(0,4))
        tk.Label(filter_frame, text="Show:", bg=PANEL, fg=ORANGE_DIM, font=FONT_MONO_S).pack(side="left")
        self.filter_var = tk.StringVar(value="open")
        for val, lbl in [("open","Open"),("all","All"),("resolved","Resolved")]:
            rb = tk.Radiobutton(filter_frame, text=lbl, variable=self.filter_var, value=val,
                                command=self._refresh, bg=PANEL, fg=ORANGE,
                                selectcolor=BG3, activebackground=PANEL,
                                activeforeground=ORANGE, font=FONT_MONO_S)
            rb.pack(side="left", padx=8)

        # Table
        cols = ("ID","Priority","Title","Description","Status","Created")
        self.tree = make_treeview(self, cols, heights=14)
        self.tree.column("ID",          width=40,  stretch=False)
        self.tree.column("Priority",    width=80,  stretch=False)
        self.tree.column("Title",       width=200, stretch=True)
        self.tree.column("Description", width=200, stretch=True)
        self.tree.column("Status",      width=90,  stretch=False)
        self.tree.column("Created",     width=90,  stretch=False)
        for c in cols:
            self.tree.heading(c, text=c)
        self.tree.bind("<Double-1>", lambda e: self._edit())

        # Log tail — must be created before calling _refresh()
        section_title(self, "TASK LOG")
        self.log_view = scrolledtext.ScrolledText(
            self, bg=BG2, fg=ORANGE_DIM, font=FONT_MONO_S,
            relief="flat", bd=0, height=6, wrap="word", state="normal")
        self.log_view.pack(fill="x", padx=10, pady=(0,8))

        self._refresh()

    def _get_tasks(self):
        tasks = load_tasks()
        filt  = self.filter_var.get()
        if filt == "open":
            tasks = [t for t in tasks if t.get("status") not in ("resolved",)]
        elif filt == "resolved":
            tasks = [t for t in tasks if t.get("status") == "resolved"]
        return sorted(tasks, key=lambda t: PRIORITIES.index(t.get("priority","low")))

    def _refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for t in self._get_tasks():
            p    = t.get("priority","low")
            stat = t.get("status","open")
            tag  = "resolved_tag" if stat == "resolved" else p
            self.tree.insert("", "end", iid=str(t["id"]), values=(
                t.get("id",""),
                p.upper(),
                t.get("title","")[:40],
                t.get("description","")[:40],
                stat,
                t.get("created","")[:10],
            ), tags=(tag,))
        for p in PRIORITIES:
            self.tree.tag_configure(p, foreground=PRIORITY_COLOUR[p])
        self.tree.tag_configure("resolved_tag", foreground=GREEN)
        self._refresh_log()

    def _refresh_log(self):
        self.log_view.config(state="normal")
        self.log_view.delete("1.0","end")
        if TASKS_LOG.exists():
            lines = TASKS_LOG.read_text().splitlines()[-20:]
            self.log_view.insert("1.0", "\n".join(lines))
        self.log_view.config(state="disabled")
        self.log_view.see("end")

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Select a task first.", parent=self)
            return None
        return int(sel[0])

    def _add(self):
        def on_save(result):
            tasks  = load_tasks()
            new_id = max((t.get("id",0) for t in tasks), default=0) + 1
            tasks.append({
                "id": new_id, "title": result["title"],
                "description": result["description"],
                "priority": result["priority"],
                "status": "open", "created": today_str(), "resolved": None
            })
            save_tasks(tasks)
            log_task(f"ADDED [{result['priority'].upper()}] {result['title']}")
            self._refresh()
            self.app.status(f"Task added: {result['title']}")
        TaskModal(self, self.app, on_save=on_save)

    def _edit(self):
        tid = self._selected_id()
        if tid is None: return
        task = next((t for t in load_tasks() if t.get("id") == tid), None)
        if not task: return
        def on_save(result):
            tasks = load_tasks()
            for t in tasks:
                if t.get("id") == tid:
                    t["title"]       = result["title"]
                    t["description"] = result["description"]
                    t["priority"]    = result["priority"]
            save_tasks(tasks)
            log_task(f"EDITED task #{tid}: {result['title']}")
            self._refresh()
            self.app.status(f"Task #{tid} updated.")
        TaskModal(self, self.app, task=task, on_save=on_save)

    def _resolve(self):
        tid = self._selected_id()
        if tid is None: return
        tasks = load_tasks()
        title = ""
        for t in tasks:
            if t.get("id") == tid:
                t["status"]   = "resolved"
                t["resolved"] = today_str()
                title = t.get("title","")
        save_tasks(tasks)
        log_task(f"RESOLVED task #{tid}: {title}")
        self._refresh()
        self.app.status(f"Task #{tid} resolved.")

    def _delete(self):
        tid = self._selected_id()
        if tid is None: return
        if not messagebox.askyesno("Confirm", f"Delete task #{tid}?", parent=self):
            return
        tasks = [t for t in load_tasks() if t.get("id") != tid]
        save_tasks(tasks)
        log_task(f"DELETED task #{tid}")
        self._refresh()
        self.app.status(f"Task #{tid} deleted.")


# ── Daily Log Screen ───────────────────────────────────────────────────────────
class DailyLogScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=PANEL)
        self.app = app
        self._build()

    def _build(self):
        section_title(self, f"DAILY LOG  —  {today_str()}")

        # Entry panel
        entry_frame = tk.Frame(self, bg=BG3, highlightbackground=ORANGE3, highlightthickness=1)
        entry_frame.pack(fill="x", padx=10, pady=4)
        tk.Label(entry_frame, text="New Entry:", bg=BG3, fg=ORANGE_DIM, font=FONT_MONO_S).pack(
            anchor="w", padx=10, pady=(8,2))
        self.entry_box = styled_text(entry_frame, height=4, width=80)
        self.entry_box.pack(fill="x", padx=10, pady=4)
        btn_row = tk.Frame(entry_frame, bg=BG3)
        btn_row.pack(fill="x", padx=10, pady=(0,8))
        styled_button(btn_row, "Append to Today's Log", self._append, width=24,
                      bg=ORANGE3, colour=BG).pack(side="left")
        styled_button(btn_row, "Clear", self._clear_entry, width=10).pack(side="left", padx=8)

        # Date picker row
        nav = tk.Frame(self, bg=PANEL)
        nav.pack(fill="x", padx=10, pady=(6,2))
        tk.Label(nav, text="View date:", bg=PANEL, fg=ORANGE_DIM, font=FONT_MONO_S).pack(side="left")
        self.date_var = tk.StringVar(value=today_str())
        date_entry = styled_entry(nav, textvariable=self.date_var, width=12)
        date_entry.pack(side="left", padx=6)
        styled_button(nav, "Load", self._load_date, width=8).pack(side="left")
        styled_button(nav, "Today", self._go_today, width=8).pack(side="left", padx=4)

        # Log view
        section_title(self, "LOG CONTENTS")
        self.log_view = scrolledtext.ScrolledText(
            self, bg=BG2, fg=ORANGE, font=FONT_MONO_S,
            relief="flat", bd=0, height=18, wrap="word", state="normal")
        self.log_view.pack(fill="both", expand=True, padx=10, pady=(0,8))
        self._load_date()

    def _append(self):
        entry = self.entry_box.get("1.0","end").strip()
        if not entry:
            return
        append_daily_log(entry)
        self.entry_box.delete("1.0","end")
        self._load_date()
        self.app.status("Entry logged.")

    def _clear_entry(self):
        self.entry_box.delete("1.0","end")

    def _load_date(self):
        date = self.date_var.get().strip()
        p = DAILY_DIR / f"{date}.md"
        self.log_view.config(state="normal")
        self.log_view.delete("1.0","end")
        if p.exists():
            self.log_view.insert("1.0", p.read_text())
        else:
            self.log_view.insert("1.0", f"No log for {date}.")
        self.log_view.config(state="disabled")
        self.log_view.see("end")

    def _go_today(self):
        self.date_var.set(today_str())
        self._load_date()


# ── Search Screen ──────────────────────────────────────────────────────────────
class SearchScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=PANEL)
        self.app = app
        self._build()

    def _build(self):
        section_title(self, "MEMORY SEARCH")

        tk.Label(self, text="Searches all indexed log entries (daily logs, decisions, notes)",
                 bg=PANEL, fg=ORANGE_DIM, font=FONT_MONO_S).pack(padx=10, anchor="w")

        search_frame = tk.Frame(self, bg=PANEL)
        search_frame.pack(fill="x", padx=10, pady=8)
        self.query_var = tk.StringVar()
        entry = styled_entry(search_frame, textvariable=self.query_var, width=50)
        entry.pack(side="left")
        entry.bind("<Return>", lambda e: self._search())
        styled_button(search_frame, "Search", self._search, width=10,
                      bg=ORANGE3, colour=BG).pack(side="left", padx=8)
        styled_button(search_frame, "Clear", self._clear, width=8).pack(side="left")

        self.result_label = tk.Label(self, text="", bg=PANEL, fg=ORANGE_DIM, font=FONT_MONO_S)
        self.result_label.pack(padx=10, anchor="w")

        cols = ("Date", "Category", "Content")
        self.tree = make_treeview(self, cols, heights=12)
        self.tree.column("Date",     width=90,  stretch=False)
        self.tree.column("Category", width=90,  stretch=False)
        self.tree.column("Content",  width=500, stretch=True)
        for c in cols:
            self.tree.heading(c, text=c)

        section_title(self, "SEARCH IN DAILY LOG FILES")
        tk.Label(self, text="Grep across all daily log files on disk:",
                 bg=PANEL, fg=ORANGE_DIM, font=FONT_MONO_S).pack(padx=10, anchor="w")
        grep_frame = tk.Frame(self, bg=PANEL)
        grep_frame.pack(fill="x", padx=10, pady=6)
        self.grep_var = tk.StringVar()
        grep_entry = styled_entry(grep_frame, textvariable=self.grep_var, width=50)
        grep_entry.pack(side="left")
        grep_entry.bind("<Return>", lambda e: self._grep())
        styled_button(grep_frame, "Search Files", self._grep, width=14).pack(side="left", padx=8)

        self.grep_view = scrolledtext.ScrolledText(
            self, bg=BG2, fg=ORANGE_DIM, font=FONT_MONO_S,
            relief="flat", bd=0, height=8, wrap="word", state="normal")
        self.grep_view.pack(fill="both", expand=True, padx=10, pady=(0,8))

    def _search(self):
        q = self.query_var.get().strip()
        if not q:
            return
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            results = search_memory(q)
        except Exception as e:
            self.result_label.config(text=f"Error: {e}", fg=RED)
            return
        self.result_label.config(
            text=f"{'No results.' if not results else f'{len(results)} result(s) found.'}",
            fg=GREEN if results else ORANGE_DIM)
        for date, cat, content in results[:50]:
            self.tree.insert("", "end", values=(date, cat, content[:120]))

    def _clear(self):
        self.query_var.set("")
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.result_label.config(text="")

    def _grep(self):
        q = self.grep_var.get().strip()
        self.grep_view.config(state="normal")
        self.grep_view.delete("1.0","end")
        if not q:
            return
        matches = []
        if DAILY_DIR.exists():
            for f in sorted(DAILY_DIR.glob("*.md")):
                for i, line in enumerate(f.read_text().splitlines(), 1):
                    if q.lower() in line.lower():
                        matches.append(f"[{f.stem}:{i}] {line}")
        out = "\n".join(matches[:100]) if matches else f"No matches for '{q}'"
        self.grep_view.insert("1.0", out)
        self.grep_view.config(state="disabled")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ══════════════════════════════════════════════════════════════════════════════

class CommandCenterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("COMMAND CENTER — Personal Performance System")
        self.geometry("1200x750")
        self.minsize(900, 600)
        self.configure(bg=BG)
        self._setup_icon()
        self._build_layout()
        self._screens = {}
        self.show("dashboard")
        self.after(100, self._check_reviews_on_start)

    def _setup_icon(self):
        # Blank icon to avoid default Tk icon
        try:
            self.iconbitmap(default="")
        except Exception:
            pass

    def _build_layout(self):
        # ── Top bar ──
        top = tk.Frame(self, bg=BG, height=44)
        top.pack(fill="x")
        top.pack_propagate(False)

        tk.Label(top, text="▓ COMMAND CENTER", bg=BG, fg=ORANGE,
                 font=("Consolas", 14, "bold")).pack(side="left", padx=16, pady=8)

        self.clock_label = tk.Label(top, text="", bg=BG, fg=ORANGE_DIM, font=FONT_MONO_S)
        self.clock_label.pack(side="right", padx=16)
        self._tick()

        tk.Frame(self, bg=ORANGE3, height=1).pack(fill="x")

        # ── Main area ──
        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True)

        # Sidebar
        self.sidebar = tk.Frame(main, bg=BG2, width=170)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        tk.Frame(main, bg=ORANGE3, width=1).pack(side="left", fill="y")

        # Content
        self.content = tk.Frame(main, bg=PANEL)
        self.content.pack(side="left", fill="both", expand=True)

        # Status bar
        tk.Frame(self, bg=ORANGE3, height=1).pack(fill="x")
        self.status_bar = tk.Label(self, text="Ready.", bg=BG, fg=ORANGE_DIM,
                                   font=FONT_MONO_S, anchor="w")
        self.status_bar.pack(fill="x", padx=10, pady=3)

        self._build_sidebar()

    def _build_sidebar(self):
        tk.Label(self.sidebar, text="\nNAVIGATION\n", bg=BG2, fg=ORANGE_DIM,
                 font=("Consolas", 8, "bold")).pack(fill="x", padx=4)
        tk.Frame(self.sidebar, bg=ORANGE3, height=1).pack(fill="x", padx=8, pady=2)

        self.nav_buttons = {}
        nav_items = [
            ("dashboard",  "⌂  Dashboard"),
            ("memory",     "◈  Memory"),
            ("decisions",  "◆  Decisions"),
            ("tasks",      "☰  Tasks"),
            ("log",        "✎  Daily Log"),
            ("search",     "⌕  Search"),
        ]
        for key, label in nav_items:
            btn = tk.Button(
                self.sidebar, text=label,
                command=lambda k=key: self.show(k),
                bg=BG2, fg=ORANGE, font=FONT_MONO,
                relief="flat", anchor="w", padx=14, pady=7,
                activebackground=ORANGE3, activeforeground=BG,
                cursor="hand2", bd=0,
            )
            btn.pack(fill="x", pady=1)
            self.nav_buttons[key] = btn

        # Review alert
        tk.Frame(self.sidebar, bg=ORANGE3, height=1).pack(fill="x", padx=8, pady=8)
        self.review_badge = tk.Label(self.sidebar, text="", bg=BG2, fg=RED,
                                     font=("Consolas", 8, "bold"), wraplength=150)
        self.review_badge.pack(padx=8, pady=4)
        self._update_badge()

        # Footer
        tk.Frame(self.sidebar, bg=PANEL).pack(fill="both", expand=True)
        tk.Label(self.sidebar, text="v2.0  tkinter", bg=BG2,
                 fg=GREY, font=("Consolas", 7)).pack(pady=8)

    def _update_badge(self):
        n = len(get_flagged())
        if n:
            self.review_badge.config(text=f"⚠ {n} review(s) due\ngo to Decisions")
        else:
            self.review_badge.config(text="✓ no reviews due", fg=GREEN)

    def show(self, name):
        # Highlight active nav button
        for k, btn in self.nav_buttons.items():
            btn.config(bg=ORANGE3 if k == name else BG2,
                       fg=BG if k == name else ORANGE)

        # Destroy previous screen
        for w in self.content.winfo_children():
            w.destroy()

        # Build or rebuild screen
        screen_map = {
            "dashboard": DashboardScreen,
            "memory":    MemoryScreen,
            "decisions": DecisionScreen,
            "tasks":     TaskScreen,
            "log":       DailyLogScreen,
            "search":    SearchScreen,
        }
        cls = screen_map.get(name)
        if cls:
            screen = cls(self.content, self)
            screen.pack(fill="both", expand=True)
        self._update_badge()

    def status(self, msg):
        self.status_bar.config(text=f"  ●  {msg}  —  {now_str()}")
        self.after(6000, lambda: self.status_bar.config(text="  Ready."))

    def _tick(self):
        self.clock_label.config(text=datetime.now().strftime("  %A  %d %b %Y  %H:%M:%S  "))
        self.after(1000, self._tick)

    def _check_reviews_on_start(self):
        flagged = get_flagged()
        if flagged:
            messagebox.showwarning(
                "Review Due",
                f"{len(flagged)} decision(s) are overdue for review.\n\nGo to Decisions to review them.",
                parent=self
            )


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = CommandCenterApp()
    app.mainloop()
