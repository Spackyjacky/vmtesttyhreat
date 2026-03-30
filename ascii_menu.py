"""
ThreatPad ASCII Quick Menu
==========================
Keyboard-driven 3-level modal popup + Ctrl+1 / Ctrl+2 rapid workflow.

Levels
  1  Action      N=New Incident  O=Open Incident  P=Phone Call  M=Meeting Notes
  2  Template    1-5  (varies by action; for Open: client picker)
  3  Client      1-N  (ESC goes back)

After selection a new tab is created with the correct template + client header.

Ctrl+1  Defang current tab → safe-copy to clipboard → save to history → reopen menu
Ctrl+2  Copy current tab content into a new Escalation Note tab → same flow
"""

import tkinter as tk
import json
import os
import re
from datetime import datetime
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

MENU_CONFIG_FILE  = "ascii_menu_config.json"
NOTE_HISTORY_FILE = "note_history.json"
MAX_HISTORY       = 15

# Colour scheme (dark, hacker-green feel)
BG        = "#0d1117"
FG_FRAME  = "#21b559"   # bright green border / titles
FG_KEY    = "#00bfff"   # cyan  — the shortcut key letter
FG_ITEM   = "#e0e0e0"   # white — item text
FG_HOVER  = "#00ff88"   # bright green hover
FG_DIM    = "#555555"   # dimmed footer text
FG_WARN   = "#ff6b6b"   # red warning
BG_HOVER  = "#0f2d1a"   # hover row background
FONT      = ("Consolas", 12)
FONT_B    = ("Consolas", 12, "bold")
FONT_T    = ("Consolas", 11)


# ─────────────────────────────────────────────────────────────────────────────
# DEFAULT CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_CONFIG = {
    "clients": ["Client Alpha", "Client Beta", "Client Gamma"],
    "templates": {
        "N": [
            "Standard Incident",
            "Phishing Investigation",
            "Ransomware Response",
            "Malware Analysis",
            "Generic Incident",
        ],
        "P": [
            "Call Log",
            "Vendor Call",
            "Client Briefing",
            "IR Coordination Call",
            "Generic Call Note",
        ],
        "M": [
            "Team Meeting",
            "Incident Review",
            "Post-Incident Review",
            "Client Meeting",
            "Generic Meeting",
        ],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# TEMPLATE BODIES
# ─────────────────────────────────────────────────────────────────────────────

def _ts():
    return datetime.now().strftime("%Y-%m-%d")

def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def _make_template(action_key: str, template_name: str, client: str) -> str:
    """Return pre-filled note body for the chosen action / template / client."""
    date   = _ts()
    ts     = _now()
    client_line = f"Client     : {client}"

    if action_key == "N":
        if "Phishing" in template_name:
            return (
                f"=== PHISHING INVESTIGATION ===\n"
                f"Date       : {date}\nAnalyst    : \nIncident ID: INC-\n"
                f"Severity   : HIGH\nStatus     : OPEN\n{client_line}\n\n"
                f"--- DESCRIPTION ---\n\n"
                f"--- INDICATORS OF COMPROMISE ---\n"
                f"Sender Emails:\n- \n\nPhishing Domains:\n- \n\nPhishing URLs:\n- \n\nSource IPs:\n- \n\n"
                f"--- TIMELINE ---\n[{date} HH:MM]  \n\n"
                f"--- REMEDIATION ---\n[ ] 1. Block domains at DNS\n[ ] 2. Block sender at email gateway\n[ ] 3. Reset affected credentials\n"
            )
        elif "Ransomware" in template_name:
            return (
                f"=== RANSOMWARE RESPONSE ===\n"
                f"Date       : {date}\nAnalyst    : \nIncident ID: INC-\n"
                f"Severity   : CRITICAL\nStatus     : OPEN\n{client_line}\n\n"
                f"--- DESCRIPTION ---\n\n"
                f"--- INDICATORS OF COMPROMISE ---\n"
                f"C2 IPs:\n- \n\nC2 Domains:\n- \n\nHashes (MD5/SHA256):\n- \n\n"
                f"--- AFFECTED SYSTEMS ---\n- \n\n"
                f"--- TIMELINE ---\n[{date} HH:MM]  \n\n"
                f"--- REMEDIATION ---\n[ ] 1. Isolate affected hosts\n[ ] 2. Block C2 IOCs\n[ ] 3. Restore from backup\n"
            )
        elif "Malware" in template_name:
            return (
                f"=== MALWARE ANALYSIS ===\n"
                f"Date       : {date}\nAnalyst    : \nIncident ID: INC-\n"
                f"Severity   : HIGH\nStatus     : OPEN\n{client_line}\n\n"
                f"--- SAMPLE ---\nFilename : \nMD5      : \nSHA1     : \nSHA256   : \n\n"
                f"--- BEHAVIOUR ---\n\n"
                f"--- NETWORK IOCs ---\n\n"
                f"--- MITRE TTPS ---\n\n"
            )
        else:
            # Standard Incident / Generic
            return (
                f"=== INCIDENT ANALYSIS ===\n"
                f"Date       : {date}\nAnalyst    : \nIncident ID: INC-\n"
                f"Severity   : [LOW/MEDIUM/HIGH/CRITICAL]\nStatus     : OPEN\n{client_line}\n\n"
                f"--- DESCRIPTION ---\n\n"
                f"--- INDICATORS OF COMPROMISE ---\nIPs:\n- \n\nDomains:\n- \n\nHashes:\n- \n\n"
                f"--- TIMELINE ---\n[{date} HH:MM]  \n\n"
                f"--- REMEDIATION ---\n[ ] 1. \n[ ] 2. \n[ ] 3. \n"
            )

    elif action_key == "P":
        label = template_name
        return (
            f"=== {label.upper()} ===\n"
            f"Date     : {date}\nTime     : {datetime.now().strftime('%H:%M')}\n"
            f"Analyst  : \n{client_line}\n"
            f"With     : \nRe       : \n\n"
            f"--- NOTES ---\n\n"
            f"--- ACTION ITEMS ---\n[ ] \n"
        )

    elif action_key == "M":
        label = template_name
        return (
            f"=== {label.upper()} ===\n"
            f"Date      : {date}\nTime      : {datetime.now().strftime('%H:%M')}\n"
            f"Analyst   : \n{client_line}\n"
            f"Attendees : \nTopic     : \n\n"
            f"--- DISCUSSION ---\n\n"
            f"--- DECISIONS ---\n\n"
            f"--- ACTION ITEMS ---\n[ ] \n"
        )

    return f"=== NEW NOTE ===\nDate: {date}\n{client_line}\n\n"


ESCALATION_TEMPLATE = """\
=== ESCALATION NOTE ===
Date       : {date}
Analyst    :
Incident ID: INC-
Severity   :
Client     :

--- REASON FOR ESCALATION ---

--- ESCALATED TO ---

--- INITIAL FINDINGS (see closure note below) ---
────────────────────────────────────────────────
{first_note}
────────────────────────────────────────────────
"""


# ─────────────────────────────────────────────────────────────────────────────
# NOTE HISTORY
# ─────────────────────────────────────────────────────────────────────────────

class NoteHistory:
    """Persist the last MAX_HISTORY notes (title + content) for quick reopening."""

    def __init__(self):
        self.entries = []
        self._load()

    def _load(self):
        try:
            if os.path.exists(NOTE_HISTORY_FILE):
                with open(NOTE_HISTORY_FILE, "r") as f:
                    self.entries = json.load(f)
        except Exception:
            self.entries = []

    def save(self, title: str, content: str, client: str = ""):
        entry = {
            "title":     title,
            "client":    client,
            "content":   content,
            "saved_at":  _now(),
        }
        # Remove any existing entry with same title+client to avoid duplication
        self.entries = [e for e in self.entries
                        if not (e["title"] == title and e["client"] == client)]
        self.entries.insert(0, entry)
        self.entries = self.entries[:MAX_HISTORY]
        try:
            with open(NOTE_HISTORY_FILE, "w") as f:
                json.dump(self.entries, f, indent=2)
        except Exception as e:
            print(f"[ascii_menu] NoteHistory save error: {e}")

    def get_all(self):
        self._load()
        return self.entries


# ─────────────────────────────────────────────────────────────────────────────
# MENU CONFIG
# ─────────────────────────────────────────────────────────────────────────────

class MenuConfig:
    def __init__(self):
        self.data = dict(DEFAULT_CONFIG)
        self._load()

    def _load(self):
        # Primary source: ThreatPad's app_settings.json (single source of truth)
        try:
            if os.path.exists("app_settings.json"):
                with open("app_settings.json", "r") as f:
                    settings = json.load(f)
                    if "clients" in settings and settings["clients"]:
                        self.data["clients"] = settings["clients"]
                        return   # clients loaded — no need to check fallback
        except Exception:
            pass
        # Fallback: ascii_menu_config.json (used if app_settings.json has no clients yet)
        try:
            if os.path.exists(MENU_CONFIG_FILE):
                with open(MENU_CONFIG_FILE, "r") as f:
                    loaded = json.load(f)
                    self.data.update(loaded)
        except Exception:
            pass

    def clients(self):
        return self.data.get("clients", DEFAULT_CONFIG["clients"])

    def templates(self, action_key: str):
        return self.data.get("templates", DEFAULT_CONFIG["templates"]).get(
            action_key, DEFAULT_CONFIG["templates"].get(action_key, [])
        )


# ─────────────────────────────────────────────────────────────────────────────
# ASCII MENU WINDOW
# ─────────────────────────────────────────────────────────────────────────────

_ACTION_LABELS = {
    "N": "New Incident",
    "O": "Open Incident",
    "P": "Phone Call",
    "M": "Meeting Notes",
}

_BOX_W = 46   # inner content width (chars)


def _pad(text: str, width: int) -> str:
    return text.ljust(width)


class ASCIIMenuWindow:
    """
    3-level keyboard-driven modal window.
    Destroyed when a selection is made or ESC is pressed at level 1.
    """

    def __init__(self, parent_root: tk.Tk, integration: "ASCIIMenuIntegration"):
        self.root_ref    = parent_root
        self.integration = integration
        self.config      = integration.config
        self.history     = integration.history

        self.level      = 1
        self.action     = None   # "N" / "O" / "P" / "M"
        self.template   = None   # index into template list
        self.client     = None   # index into client list

        # For Open-incident flow the second level is client, not template
        self._open_client = None

        self._build()

    # ── window skeleton ──────────────────────────────────────────────────────

    def _build(self):
        self.win = tk.Toplevel(self.root_ref)
        self.win.title("ThreatPad")
        self.win.resizable(False, False)
        self.win.configure(bg=BG)
        self.win.attributes("-topmost", True)

        # Outer frame for the ASCII border feel
        outer = tk.Frame(self.win, bg=FG_FRAME, bd=0)
        outer.pack(padx=2, pady=2)

        inner = tk.Frame(outer, bg=BG, bd=0)
        inner.pack(padx=1, pady=1)

        # Title bar row
        self.title_var = tk.StringVar()
        tk.Label(inner, textvariable=self.title_var,
                 font=FONT_B, bg=BG, fg=FG_FRAME,
                 anchor="center", padx=16, pady=6).pack(fill="x")

        # Separator
        tk.Frame(inner, bg=FG_FRAME, height=1).pack(fill="x")

        # Items area
        self.items_frame = tk.Frame(inner, bg=BG)
        self.items_frame.pack(fill="both", expand=True, padx=0, pady=4)

        # Separator
        tk.Frame(inner, bg=FG_FRAME, height=1).pack(fill="x")

        # Footer
        self.footer_var = tk.StringVar()
        tk.Label(inner, textvariable=self.footer_var,
                 font=("Consolas", 10), bg=BG, fg=FG_DIM,
                 anchor="center", pady=4).pack(fill="x")

        # Center on screen
        self.win.update_idletasks()
        self._center()

        # Key + close bindings
        self.win.bind("<Key>", self._on_key)
        self.win.bind("<Escape>", lambda e: self._go_back())
        self.win.protocol("WM_DELETE_WINDOW", self._close)

        self.win.grab_set()
        self.win.focus_set()

        self._render()

    def _center(self):
        w = self.win.winfo_reqwidth()
        h = self.win.winfo_reqheight()
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        x = (sw - w) // 2
        y = max(0, (sh - h) // 2 - 40)
        self.win.geometry(f"+{x}+{y}")

    # ── rendering ────────────────────────────────────────────────────────────

    def _clear_items(self):
        for w in self.items_frame.winfo_children():
            w.destroy()

    def _render(self):
        self._clear_items()
        if self.level == 1:
            self._render_level1()
        elif self.level == 2:
            self._render_level2()
        elif self.level == 3:
            self._render_level3()
        elif self.level == 4:
            self._render_level4()
        # Re-center in case size changed
        self.win.update_idletasks()
        self._center()

    def _make_item(self, parent, key_char: str, label_text: str,
                   callback, row: int):
        """One clickable menu row:  [K]  Label text"""
        row_frame = tk.Frame(parent, bg=BG, cursor="hand2")
        row_frame.grid(row=row, column=0, sticky="w", padx=20, pady=2)

        lbracket = tk.Label(row_frame, text="[", font=FONT, bg=BG, fg=FG_DIM)
        lbracket.pack(side="left")

        key_lbl = tk.Label(row_frame, text=key_char, font=FONT_B,
                           bg=BG, fg=FG_KEY)
        key_lbl.pack(side="left")

        rbracket = tk.Label(row_frame, text="]  ", font=FONT, bg=BG, fg=FG_DIM)
        rbracket.pack(side="left")

        txt_lbl = tk.Label(row_frame, text=label_text, font=FONT,
                           bg=BG, fg=FG_ITEM, anchor="w")
        txt_lbl.pack(side="left")

        # Hover highlight
        def on_enter(_):
            for w in (row_frame, lbracket, key_lbl, rbracket, txt_lbl):
                w.configure(bg=BG_HOVER)
            txt_lbl.configure(fg=FG_HOVER)

        def on_leave(_):
            for w in (row_frame, lbracket, key_lbl, rbracket, txt_lbl):
                w.configure(bg=BG)
            txt_lbl.configure(fg=FG_ITEM)

        for widget in (row_frame, lbracket, key_lbl, rbracket, txt_lbl):
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", lambda e, cb=callback: cb())

    # -- level 1: action picker -----------------------------------------------

    def _render_level1(self):
        self.title_var.set("  T H R E A T P A D   Q U I C K   M E N U  ")
        self.footer_var.set("press key or click  •  [ESC] close")
        tk.Frame(self.items_frame, bg=BG, height=6).grid(row=0, column=0)
        for i, (key, label) in enumerate(_ACTION_LABELS.items()):
            self._make_item(self.items_frame, key, label,
                            lambda k=key: self._pick_action(k), row=i + 1)
        tk.Frame(self.items_frame, bg=BG, height=6).grid(
            row=len(_ACTION_LABELS) + 1, column=0)

    def _pick_action(self, key: str):
        self.action = key
        self.level = 2
        self._render()

    # -- level 2: template picker (or client picker for Open) -----------------

    def _render_level2(self):
        action_label = _ACTION_LABELS[self.action]

        if self.action == "O":
            # Open Incident: level 2 = client picker
            self.title_var.set(f"  OPEN INCIDENT  ›  Select Client  ")
            self.footer_var.set("press number or click  •  [ESC] back")
            clients = self.config.clients()
            tk.Frame(self.items_frame, bg=BG, height=6).grid(row=0, column=0)
            for i, client in enumerate(clients):
                self._make_item(self.items_frame, str(i + 1), client,
                                lambda idx=i: self._pick_open_client(idx),
                                row=i + 1)
            tk.Frame(self.items_frame, bg=BG, height=6).grid(
                row=len(clients) + 1, column=0)
        else:
            self.title_var.set(f"  {action_label.upper()}  ›  Select Template  ")
            self.footer_var.set("press number or click  •  [ESC] back")
            templates = self.config.templates(self.action)
            tk.Frame(self.items_frame, bg=BG, height=6).grid(row=0, column=0)
            for i, name in enumerate(templates):
                self._make_item(self.items_frame, str(i + 1), name,
                                lambda idx=i: self._pick_template(idx),
                                row=i + 1)
            tk.Frame(self.items_frame, bg=BG, height=6).grid(
                row=len(templates) + 1, column=0)

    def _pick_template(self, idx: int):
        self.template = idx
        self.level = 3
        self._render()

    def _pick_open_client(self, idx: int):
        self._open_client = idx
        self.level = 3
        self._render()

    # -- level 3: client picker (new notes) or note list (open) ---------------

    def _render_level3(self):
        action_label = _ACTION_LABELS[self.action]

        if self.action == "O":
            # Show recent notes for the selected client
            client_name = self.config.clients()[self._open_client]
            self.title_var.set(f"  OPEN  ›  {client_name}  ›  Recent Notes  ")
            self.footer_var.set("press number or click  •  [ESC] back")
            entries = [e for e in self.history.get_all()
                       if e.get("client") == client_name]
            if not entries:
                # also show entries with no client assigned
                entries = self.history.get_all()
            tk.Frame(self.items_frame, bg=BG, height=6).grid(row=0, column=0)
            if not entries:
                tk.Label(self.items_frame,
                         text="  No saved notes yet.  Use Ctrl+1 to save.",
                         font=FONT, bg=BG, fg=FG_DIM).grid(
                    row=1, column=0, padx=20, pady=10)
            else:
                for i, entry in enumerate(entries[:9]):
                    label = f"{entry['saved_at'][:16]}  {entry['title']}"
                    self._make_item(self.items_frame, str(i + 1), label,
                                    lambda e=entry: self._open_note(e),
                                    row=i + 1)
            tk.Frame(self.items_frame, bg=BG, height=6).grid(
                row=11, column=0)

        else:
            # Client selector for new note
            templates  = self.config.templates(self.action)
            tmpl_name  = templates[self.template]
            self.title_var.set(f"  {action_label.upper()}  ›  Select Client  ")
            self.footer_var.set("press number or click  •  [ESC] back")
            clients = self.config.clients()
            tk.Frame(self.items_frame, bg=BG, height=6).grid(row=0, column=0)
            for i, client in enumerate(clients):
                self._make_item(self.items_frame, str(i + 1), client,
                                lambda idx=i: self._create_note(idx),
                                row=i + 1)
            tk.Frame(self.items_frame, bg=BG, height=6).grid(
                row=len(clients) + 1, column=0)

    def _create_note(self, client_idx: int):
        templates   = self.config.templates(self.action)
        tmpl_name   = templates[self.template]
        client_name = self.config.clients()[client_idx]
        tab_title   = f"{client_name} – {tmpl_name}"
        content     = _make_template(self.action, tmpl_name, client_name)
        self.integration.app.new_tab(tab_title, content)
        # Store the client on the integration for Ctrl+1
        self.integration.current_client = client_name
        self._close()

    def _open_note(self, entry: dict):
        self.integration.app.new_tab(entry["title"], entry["content"])
        self.integration.current_client = entry.get("client", "")
        self._close()

    # -- key handler ----------------------------------------------------------

    def _on_key(self, event):
        key = event.char.upper() if event.char else ""
        if not key:
            return

        if self.level == 1:
            if key in _ACTION_LABELS:
                self._pick_action(key)

        elif self.level == 2:
            if self.action == "O":
                # number → client
                if key.isdigit():
                    idx = int(key) - 1
                    if 0 <= idx < len(self.config.clients()):
                        self._pick_open_client(idx)
            else:
                templates = self.config.templates(self.action)
                if key.isdigit():
                    idx = int(key) - 1
                    if 0 <= idx < len(templates):
                        self._pick_template(idx)

        elif self.level == 3:
            if self.action == "O":
                entries = [e for e in self.history.get_all()
                           if e.get("client") ==
                           self.config.clients()[self._open_client]]
                if not entries:
                    entries = self.history.get_all()
                if key.isdigit():
                    idx = int(key) - 1
                    if 0 <= idx < len(entries[:9]):
                        self._open_note(entries[idx])
            else:
                clients = self.config.clients()
                if key.isdigit():
                    idx = int(key) - 1
                    if 0 <= idx < len(clients):
                        self._create_note(idx)

    # -- navigation -----------------------------------------------------------

    def _go_back(self):
        if self.level == 1:
            self._close()
        elif self.level == 2:
            self.level = 1
            self.action = None
            self._render()
        elif self.level == 3:
            self.level = 2
            self.template = None
            self._open_client = None
            self._render()

    def _close(self):
        try:
            self.win.grab_release()
            self.win.destroy()
        except Exception:
            pass
        self.integration.menu_window = None


# ─────────────────────────────────────────────────────────────────────────────
# INTEGRATION  –  hooks into SOCNotesApp
# ─────────────────────────────────────────────────────────────────────────────

class ASCIIMenuIntegration:
    """
    Attach to a SOCNotesApp instance.
    Call .bind_keys() once after the app's own keybindings are set up.
    """

    def __init__(self, app):
        self.app            = app          # SOCNotesApp instance
        self.config         = MenuConfig()
        self.history        = NoteHistory()
        self.menu_window    = None
        self.current_client = ""           # set when a note is created/opened

    # ── public API ───────────────────────────────────────────────────────────

    def bind_keys(self):
        root = self.app.root
        # Ctrl+` (grave accent) → toggle menu
        root.bind("<Control-grave>", lambda e: self.show_menu())
        # Ctrl+1 → defang + safe-copy + save + reopen menu
        root.bind("<Control-Key-1>", lambda e: self.ctrl_1())
        # Ctrl+2 → escalation note
        root.bind("<Control-Key-2>", lambda e: self.ctrl_2())

    def show_menu(self):
        if self.menu_window is not None:
            try:
                self.menu_window.win.focus_set()
                return
            except Exception:
                self.menu_window = None
        self.menu_window = ASCIIMenuWindow(self.app.root, self)

    # ── Ctrl+1 ───────────────────────────────────────────────────────────────

    def ctrl_1(self):
        """Defang → check clean → copy → save history → reopen menu."""
        app = self.app

        current = app.notebook.select()
        if not current:
            return

        frame       = app.notebook.nametowidget(current)
        text_widget = app.get_text_widget(frame)

        # 1. Defang
        app.defang_text()
        text = text_widget.get("1.0", "end-1c")

        # 2. Check for remaining undefanged IOCs
        unsafe_patterns = [
            r'https?://',
            r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            r'\b[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?'
            r'(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}\b',
        ]
        still_unsafe = any(re.search(p, text, re.IGNORECASE)
                           for p in unsafe_patterns)

        if still_unsafe:
            self._warn_popup(
                "Unsafe IOCs Remain",
                "Defang completed but undefanged IOCs were still detected.\n"
                "Review the note before copying."
            )
            return

        # 3. Copy to clipboard silently (already defanged — no dialog needed)
        app.root.clipboard_clear()
        app.root.clipboard_append(text)

        # 4. Update status bar
        try:
            app.update_status("Ctrl+1: Defanged, copied & saved  ✔")
            app.validation_label.config(text="Copied Safely", fg="green")
        except Exception:
            pass

        # 5. Save to history
        title = app.notebook.tab(current, "text")
        self.history.save(title, text, self.current_client)

        # 6. Save the tab
        app.save_file()

        # 7. Reopen the quick menu after a short delay
        app.root.after(300, self.show_menu)

    # ── Ctrl+2 ───────────────────────────────────────────────────────────────

    def ctrl_2(self):
        """Copy current note into an Escalation Note template → new tab."""
        app = self.app

        current = app.notebook.select()
        if not current:
            return

        frame       = app.notebook.nametowidget(current)
        text_widget = app.get_text_widget(frame)
        first_note  = text_widget.get("1.0", "end-1c")

        content = ESCALATION_TEMPLATE.format(
            date=_ts(),
            first_note=first_note,
        )

        tab_title = f"{self.current_client} – Escalation Note" \
                    if self.current_client else "Escalation Note"
        app.new_tab(tab_title, content)

        try:
            app.update_status(
                "Ctrl+2: Escalation Note created — edit, then Ctrl+1 to copy & save"
            )
        except Exception:
            pass

    # ── helpers ──────────────────────────────────────────────────────────────

    def _warn_popup(self, title: str, message: str):
        popup = tk.Toplevel(self.app.root)
        popup.title(title)
        popup.configure(bg=BG)
        popup.attributes("-topmost", True)
        popup.resizable(False, False)

        tk.Label(popup, text=f"  ⚠  {title}  ",
                 font=FONT_B, bg=BG, fg=FG_WARN,
                 pady=10).pack(fill="x")
        tk.Frame(popup, bg=FG_WARN, height=1).pack(fill="x")
        tk.Label(popup, text=f"\n{message}\n",
                 font=FONT, bg=BG, fg=FG_ITEM,
                 justify="center", padx=20).pack()
        tk.Button(popup, text="  OK  ", font=FONT_B,
                  bg="#2a2a2a", fg=FG_ITEM,
                  activebackground=BG_HOVER, activeforeground=FG_HOVER,
                  bd=0, padx=10, pady=6,
                  command=popup.destroy).pack(pady=(0, 12))

        popup.update_idletasks()
        sw = popup.winfo_screenwidth()
        sh = popup.winfo_screenheight()
        x  = (sw - popup.winfo_reqwidth())  // 2
        y  = (sh - popup.winfo_reqheight()) // 2
        popup.geometry(f"+{x}+{y}")
        popup.grab_set()
        popup.focus_set()
        popup.bind("<Return>", lambda e: popup.destroy())
        popup.bind("<Escape>", lambda e: popup.destroy())
