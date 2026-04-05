"""
Command Center — Personal Performance System
Tkinter rebuild — black/orange terminal aesthetic
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json, csv, os, sys, sqlite3, threading
from datetime import datetime, timedelta
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
# When frozen by PyInstaller the exe lives one level above the bundle temp dir,
# so we store all data next to the exe rather than inside the bundle.
if getattr(sys, "frozen", False):
    BASE = Path(sys.executable).parent
else:
    BASE = Path(__file__).parent
MEMORY_DIR = BASE / "memory"
DATA_DIR   = BASE / "data"
LOGS_DIR   = BASE / "logs"
DAILY_DIR  = MEMORY_DIR / "daily"

DECISIONS_CSV = DATA_DIR / "decisions.csv"
TASKS_JSON    = DATA_DIR / "tasks.json"
TASKS_LOG     = LOGS_DIR / "tasks.log"
MEMORY_DB     = DATA_DIR / "memory.db"
PROGRAMS_JSON = DATA_DIR / "programs.json"

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

def load_programs():
    if not PROGRAMS_JSON.exists():
        return []
    try:
        return json.loads(PROGRAMS_JSON.read_text()) or []
    except Exception:
        return []

def save_programs(programs):
    PROGRAMS_JSON.write_text(json.dumps(programs, indent=2))

def get_program_template(name: str, prog_type: str = "certification") -> dict:
    sc200_aliases = {"sc-200", "microsoft sc-200", "sc200"}
    existing = load_programs()
    new_id = max((p.get("id", 0) for p in existing), default=0) + 1
    skeleton = {
        "id": new_id, "name": name, "type": prog_type,
        "description": "", "start_date": today_str(), "target_date": "",
        "status": "active", "created": today_str(), "modules": []
    }
    if name.strip().lower() in sc200_aliases:
        skeleton["name"] = "Microsoft SC-200"
        skeleton["description"] = (
            "Microsoft Security Operations Analyst — prepares for the SC-200 exam. "
            "Covers Microsoft Defender XDR, Defender for Cloud, and Microsoft Sentinel."
        )
        skeleton["modules"] = _sc200_modules()
    return skeleton

def _sc200_modules() -> list:
    return [
        # ── LP1: Microsoft Defender XDR ───────────────────────────────────────
        {"id":1,"title":"Introduction to Microsoft 365 Threat Protection",
         "description":"Overview of the Microsoft Defender XDR suite. Learn how Defender for Endpoint, Defender for Office 365, Defender for Identity, and Defender for Cloud Apps integrate into a unified XDR platform. Understand the security operations model and the SOC analyst role.",
         "estimated_hours":1.5,"status":"not_started","completed_date":None,
         "resources":["https://learn.microsoft.com/en-us/training/modules/introduction-microsoft-365-threat-protection/"],"notes":""},
        {"id":2,"title":"Mitigate Incidents Using Microsoft Defender XDR",
         "description":"Deep dive into the Microsoft Defender portal. Triage and investigate incidents, manage alerts, use the attack story graph, and perform automated investigation and response (AIR). Practice the incident lifecycle from detection through remediation.",
         "estimated_hours":2.0,"status":"not_started","completed_date":None,
         "resources":["https://learn.microsoft.com/en-us/training/modules/mitigate-incidents-microsoft-365-defender/"],"notes":""},
        {"id":3,"title":"Protect Identities with Microsoft Entra ID Protection",
         "description":"Configure and interpret Microsoft Entra ID Protection risk policies. Understand sign-in risk and user risk, review risky users and sign-ins, remediate compromised accounts, and integrate with Conditional Access.",
         "estimated_hours":1.5,"status":"not_started","completed_date":None,
         "resources":["https://learn.microsoft.com/en-us/training/modules/protect-identities-with-aad-idp/"],"notes":""},
        {"id":4,"title":"Remediate Risks with Microsoft Defender for Office 365",
         "description":"Investigate and respond to email-based threats. Use Threat Explorer, SafeLinks, Safe Attachments, and anti-phishing policies. Understand how to hunt for compromised users and review campaign views.",
         "estimated_hours":2.0,"status":"not_started","completed_date":None,
         "resources":["https://learn.microsoft.com/en-us/training/modules/m365-threat-remediate/"],"notes":""},
        {"id":5,"title":"Safeguard Your Environment with Microsoft Defender for Identity",
         "description":"Deploy Defender for Identity sensors. Detect lateral movement, reconnaissance, and domain-dominance attacks. Investigate alerts and integrate with Microsoft Defender XDR for correlated incidents.",
         "estimated_hours":1.5,"status":"not_started","completed_date":None,
         "resources":["https://learn.microsoft.com/en-us/training/modules/m365-threat-safeguard/"],"notes":""},
        {"id":6,"title":"Secure Cloud Apps with Microsoft Defender for Cloud Apps",
         "description":"Connect apps via API and deploy the Cloud App Security proxy. Interpret the Cloud Discovery dashboard, configure session and access policies, detect shadow IT, and investigate alerts for data exfiltration or anomalous cloud behaviour.",
         "estimated_hours":2.0,"status":"not_started","completed_date":None,
         "resources":["https://learn.microsoft.com/en-us/training/modules/microsoft-cloud-app-security/"],"notes":""},
        {"id":7,"title":"Respond to Data Loss Prevention Alerts Using Microsoft 365",
         "description":"Understand how DLP policies generate alerts in Defender XDR. Triage DLP incidents, review matched sensitive information types, and take remediation actions. Covers the intersection of compliance and security operations.",
         "estimated_hours":1.5,"status":"not_started","completed_date":None,
         "resources":["https://learn.microsoft.com/en-us/training/modules/respond-to-data-loss-prevention-alerts/"],"notes":""},
        {"id":8,"title":"Manage Insider Risk in Microsoft Purview",
         "description":"Configure insider risk management policies in Microsoft Purview. Review risk indicators, investigate cases, and escalate to eDiscovery. Understand privacy controls and role separation in insider risk workflows.",
         "estimated_hours":2.0,"status":"not_started","completed_date":None,
         "resources":["https://learn.microsoft.com/en-us/training/modules/m365-compliance-insider-manage-insider-risk/"],"notes":""},
        # ── LP2: Microsoft Defender for Cloud ─────────────────────────────────
        {"id":9,"title":"Introduction to Microsoft Defender for Cloud",
         "description":"Overview of cloud security posture management (CSPM) and cloud workload protection (CWP). Understand Defender plans, Secure Score, regulatory compliance dashboards, and how Defender for Cloud spans Azure, AWS, and GCP.",
         "estimated_hours":1.5,"status":"not_started","completed_date":None,
         "resources":["https://learn.microsoft.com/en-us/training/modules/introduction-microsoft-defender-cloud/"],"notes":""},
        {"id":10,"title":"Cloud Security Posture Management with Defender for Cloud",
         "description":"Deep dive into Secure Score recommendations, hardening guidance, and governance rules. Understand attack path analysis, cloud security explorer, and how to prioritise remediation across hybrid and multi-cloud estates.",
         "estimated_hours":2.0,"status":"not_started","completed_date":None,
         "resources":["https://learn.microsoft.com/en-us/training/modules/defender-for-cloud-security-posture-management/"],"notes":""},
        {"id":11,"title":"Connect Azure Assets to Microsoft Defender for Cloud",
         "description":"Enable Defender plans for Azure subscriptions. Configure auto-provisioning of the Log Analytics agent and Azure Monitor Agent. Onboard Azure Arc-enabled servers and understand data collection rules.",
         "estimated_hours":2.0,"status":"not_started","completed_date":None,
         "resources":["https://learn.microsoft.com/en-us/training/modules/connect-azure-assets-microsoft-defender-cloud/"],"notes":""},
        {"id":12,"title":"Connect Non-Azure Resources to Microsoft Defender for Cloud",
         "description":"Onboard AWS accounts using the native connector and GCP projects via service principal. Extend coverage to on-premises machines via Azure Arc. Understand cross-cloud alert mapping and shared-responsibility posture.",
         "estimated_hours":2.0,"status":"not_started","completed_date":None,
         "resources":["https://learn.microsoft.com/en-us/training/modules/connect-non-azure-machines-to-microsoft-defender-cloud/"],"notes":""},
        {"id":13,"title":"Remediate Security Alerts Using Microsoft Defender for Cloud",
         "description":"Triage security alerts, apply manual and automatic remediation. Use workflow automation with Logic Apps, suppress false positives, export alerts to Sentinel, and track remediation through security recommendations.",
         "estimated_hours":2.5,"status":"not_started","completed_date":None,
         "resources":["https://learn.microsoft.com/en-us/training/modules/remediate-azure-defender-security-alerts/"],"notes":""},
        {"id":14,"title":"Threat Intelligence in Microsoft Defender for Cloud",
         "description":"Leverage the integrated threat intelligence map, review active alerts by geography, and use built-in threat intelligence reports. Understand how Defender for Cloud enriches alerts with Microsoft TI feeds.",
         "estimated_hours":1.5,"status":"not_started","completed_date":None,
         "resources":["https://learn.microsoft.com/en-us/training/modules/threat-intelligence-azure-security-center/"],"notes":""},
        # ── LP3: Microsoft Sentinel ────────────────────────────────────────────
        {"id":15,"title":"Introduction to Microsoft Sentinel",
         "description":"Architecture overview: workspaces, data connectors, analytics rules, incidents, and SOAR playbooks. Understand the Log Analytics foundation and how Sentinel differs from a traditional SIEM. Plan workspace design and cost considerations.",
         "estimated_hours":1.5,"status":"not_started","completed_date":None,
         "resources":["https://learn.microsoft.com/en-us/training/modules/intro-to-azure-sentinel/"],"notes":""},
        {"id":16,"title":"Create and Manage Microsoft Sentinel Workspaces",
         "description":"Deploy Sentinel on a Log Analytics workspace. Configure workspace settings, manage RBAC roles (Sentinel Reader, Responder, Contributor), set data retention policies, and implement multi-workspace and multi-tenant designs.",
         "estimated_hours":2.0,"status":"not_started","completed_date":None,
         "resources":["https://learn.microsoft.com/en-us/training/modules/create-manage-azure-sentinel-workspaces/"],"notes":""},
        {"id":17,"title":"Query Logs in Microsoft Sentinel Using KQL",
         "description":"Write KQL queries against SecurityEvent, SigninLogs, CommonSecurityLog, and other Sentinel tables. Master operators: where, project, summarize, join, union, extend, parse, render. Build queries for threat hunting and detection rule logic.",
         "estimated_hours":3.0,"status":"not_started","completed_date":None,
         "resources":["https://learn.microsoft.com/en-us/training/modules/query-logs-azure-sentinel/","https://aka.ms/lademo"],"notes":""},
        {"id":18,"title":"Use Watchlists in Microsoft Sentinel",
         "description":"Create and manage watchlists from CSV data. Reference watchlists in KQL analytics rules and hunting queries using _GetWatchlist(). Common use cases: VIP user lists, high-value asset lists, IP allowlists.",
         "estimated_hours":1.0,"status":"not_started","completed_date":None,
         "resources":["https://learn.microsoft.com/en-us/training/modules/use-watchlists-azure-sentinel/"],"notes":""},
        {"id":19,"title":"Utilize Threat Intelligence in Microsoft Sentinel",
         "description":"Ingest threat indicators via TAXII/STIX and the Microsoft TI Platforms connector. Use the ThreatIntelligenceIndicator table in KQL. Configure threat indicator analytics rules and review the Threat Intelligence workbook.",
         "estimated_hours":1.5,"status":"not_started","completed_date":None,
         "resources":["https://learn.microsoft.com/en-us/training/modules/utilize-threat-intelligence-azure-sentinel/"],"notes":""},
        {"id":20,"title":"Detect Threats with Microsoft Sentinel Analytics Rules",
         "description":"Create Scheduled, Near Real-Time (NRT), and Fusion analytics rules. Configure entity mapping, alert grouping, and suppression. Manage rule templates from Content Hub, tune thresholds, and review the MITRE ATT&CK coverage matrix.",
         "estimated_hours":2.5,"status":"not_started","completed_date":None,
         "resources":["https://learn.microsoft.com/en-us/training/modules/threat-detection-with-azure-sentinel-rules/"],"notes":""},
        {"id":21,"title":"Automate Incident Response with Microsoft Sentinel SOAR",
         "description":"Build automation rules and Logic Apps playbooks triggered on incident creation or update. Automate triage actions: assign owner, change status, add tags, run enrichment. Review the Microsoft Sentinel playbook gallery.",
         "estimated_hours":2.0,"status":"not_started","completed_date":None,
         "resources":["https://learn.microsoft.com/en-us/training/modules/security-orchestration-automation-response/"],"notes":""},
        {"id":22,"title":"Investigate and Manage Microsoft Sentinel Incidents",
         "description":"Work through the full incident lifecycle in Sentinel. Use the investigation graph, entity pages, timeline, and bookmarks. Apply triage, escalation, and closure workflows. Understand incident metrics and SLA tracking via workbooks.",
         "estimated_hours":2.5,"status":"not_started","completed_date":None,
         "resources":["https://learn.microsoft.com/en-us/training/modules/incident-management-sentinel/"],"notes":""},
        {"id":23,"title":"Threat Hunting with Microsoft Sentinel",
         "description":"Create and run hunting queries, promote findings to incidents or bookmarks. Use Livestream for real-time monitoring. Build hunting hypotheses from MITRE ATT&CK techniques, leverage community GitHub queries, and conduct hypothesis-driven hunts.",
         "estimated_hours":2.5,"status":"not_started","completed_date":None,
         "resources":["https://learn.microsoft.com/en-us/training/modules/hunt-threats-sentinel/","https://github.com/Azure/Azure-Sentinel/tree/master/Hunting%20Queries"],"notes":""},
        {"id":24,"title":"Use Notebooks for Advanced Threat Hunting in Sentinel",
         "description":"Launch Jupyter notebooks from Sentinel, use msticpy for data enrichment and threat intelligence lookups. Conduct advanced investigation workflows combining KQL data with Python analytics: IP geo-lookup, ML clustering, process tree analysis.",
         "estimated_hours":2.0,"status":"not_started","completed_date":None,
         "resources":["https://learn.microsoft.com/en-us/training/modules/hunt-threats-sentinel-notebooks/","https://github.com/microsoft/msticpy"],"notes":""},
        # ── Practice & Exam Prep ──────────────────────────────────────────────
        {"id":25,"title":"SC-200 Practice Labs — Hands-On Simulation",
         "description":"Complete the official Microsoft Learn interactive labs and MeasureUp SC-200 practice labs. Focus on Sentinel analytics rule creation, Defender XDR incident triage, and Defender for Cloud remediation. Document any knowledge gaps identified.",
         "estimated_hours":6.0,"status":"not_started","completed_date":None,
         "resources":["https://learn.microsoft.com/en-us/credentials/certifications/security-operations-analyst/","https://www.measureup.com/microsoft-sc-200-practice-test.html","https://github.com/MicrosoftLearning/SC-200T00A-Microsoft-Security-Operations-Analyst"],"notes":""},
        {"id":26,"title":"SC-200 Mock Exam and Final Review",
         "description":"Take two full MeasureUp or Whizlabs mock exams under timed conditions. Review all incorrect answers, revisit weak areas (KQL queries, Sentinel analytics tuning, Defender for Cloud plan mapping). Schedule the real exam when consistently scoring 80%+.",
         "estimated_hours":4.0,"status":"not_started","completed_date":None,
         "resources":["https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/sc-200","https://www.whizlabs.com/microsoft-azure-certification-sc-200/"],"notes":""},
    ]

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


# ── New Program Modal ─────────────────────────────────────────────────────────
class NewProgramModal(tk.Toplevel):
    def __init__(self, parent, app, on_save):
        super().__init__(parent)
        self.app     = app
        self.on_save = on_save
        self.title("New Program")
        self.configure(bg=PANEL)
        self.geometry("460x240")
        self.resizable(False, False)
        self.grab_set()
        self._build()

    def _build(self):
        tk.Label(self, text="◆ NEW PROGRAM", bg=PANEL, fg=ORANGE,
                 font=FONT_BOLD_L).pack(pady=(12,4), padx=16, anchor="w")
        tk.Frame(self, bg=ORANGE3, height=1).pack(fill="x", padx=16)

        form = tk.Frame(self, bg=PANEL)
        form.pack(fill="x", padx=20, pady=10)
        form.columnconfigure(1, weight=1)

        tk.Label(form, text="Name:", bg=PANEL, fg=ORANGE_DIM,
                 font=FONT_MONO_S, width=10, anchor="e").grid(row=0, column=0, pady=6, sticky="e")
        self.name_var = tk.StringVar()
        styled_entry(form, textvariable=self.name_var, width=36).grid(row=0, column=1, padx=8, sticky="ew")

        tk.Label(form, text="Type:", bg=PANEL, fg=ORANGE_DIM,
                 font=FONT_MONO_S, width=10, anchor="e").grid(row=1, column=0, pady=6, sticky="e")
        self.type_var = tk.StringVar(value="certification")
        type_cb = ttk.Combobox(form, textvariable=self.type_var, state="readonly", width=18,
                               values=["certification","course","learning_path","book"], font=FONT_MONO_S)
        type_cb.grid(row=1, column=1, padx=8, sticky="w")

        tk.Label(self, text="  Tip: name it 'SC-200' for auto-populated curriculum",
                 bg=PANEL, fg=ORANGE_DIM, font=("Consolas", 8)).pack(anchor="w", padx=20)

        btn_row = tk.Frame(self, bg=PANEL)
        btn_row.pack(pady=12)
        styled_button(btn_row, "Create", self._create, width=12,
                      bg=ORANGE3, colour=BG).pack(side="left", padx=8)
        styled_button(btn_row, "Cancel", self.destroy, width=12).pack(side="left", padx=8)

    def _create(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Required", "Program name is required.", parent=self)
            return
        self.on_save(name, self.type_var.get())
        self.destroy()


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


# ── Courses Screen ────────────────────────────────────────────────────────────
TYPE_DISPLAY = {"certification":"CERT","course":"COURSE","learning_path":"PATH","book":"BOOK"}

class CoursesScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=PANEL)
        self.app = app
        self._build()

    def _build(self):
        section_title(self, "PROGRAMS & COURSES")

        bar = tk.Frame(self, bg=PANEL)
        bar.pack(fill="x", padx=10, pady=4)
        styled_button(bar, "+ New Program", self._new_program, width=16,
                      bg=ORANGE3, colour=BG).pack(side="left", padx=4)
        styled_button(bar, "Open",    self._open_program,  width=10).pack(side="left", padx=4)
        styled_button(bar, "Delete",  self._delete_program, width=10).pack(side="left", padx=4)
        styled_button(bar, "Refresh", self._refresh,        width=10).pack(side="right", padx=4)

        cols = ("Name","Type","Progress","Start","Target","Status")
        self.tree = make_treeview(self, cols, heights=14)
        self.tree.column("Name",     width=220, stretch=True)
        self.tree.column("Type",     width=70,  stretch=False)
        self.tree.column("Progress", width=70,  stretch=False)
        self.tree.column("Start",    width=90,  stretch=False)
        self.tree.column("Target",   width=90,  stretch=False)
        self.tree.column("Status",   width=80,  stretch=False)
        for c in cols:
            self.tree.heading(c, text=c)
        self.tree.bind("<Double-1>", lambda e: self._open_program())
        self._refresh()

        self.stats_label = tk.Label(self, text="", bg=PANEL, fg=ORANGE_DIM, font=FONT_MONO_S)
        self.stats_label.pack(padx=10, pady=4, anchor="w")

    def _compute_progress(self, program):
        mods = program.get("modules", [])
        if not mods:
            return 0
        done = sum(1 for m in mods if m.get("status") == "complete")
        return int(done / len(mods) * 100)

    def _refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        programs = load_programs()
        for p in programs:
            pct    = self._compute_progress(p)
            status = p.get("status", "active")
            ptype  = TYPE_DISPLAY.get(p.get("type",""), p.get("type","").upper())
            tag    = status
            self.tree.insert("", "end", iid=str(p["id"]), values=(
                p.get("name",""),
                ptype,
                f"{pct}%",
                p.get("start_date","")[:10],
                p.get("target_date","")[:10] if p.get("target_date") else "—",
                status.upper(),
            ), tags=(tag,))
        self.tree.tag_configure("active",    foreground=ORANGE)
        self.tree.tag_configure("completed", foreground=GREEN)
        self.tree.tag_configure("paused",    foreground=GREY)
        self.tree.tag_configure("abandoned", foreground=RED)
        total     = len(programs)
        active    = sum(1 for p in programs if p.get("status") == "active")
        completed = sum(1 for p in programs if p.get("status") == "completed")
        self.stats_label.config(
            text=f"  Total: {total}   Active: {active}   Completed: {completed}")

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Select a program first.", parent=self)
            return None
        return int(sel[0])

    def _new_program(self):
        def on_save(name, ptype):
            prog = get_program_template(name, ptype)
            programs = load_programs()
            programs.append(prog)
            save_programs(programs)
            self._refresh()
            self.app.status(f"Program '{prog['name']}' created with {len(prog['modules'])} modules.")
        NewProgramModal(self, self.app, on_save)

    def _open_program(self):
        pid = self._selected_id()
        if pid is None:
            return
        self.app.show_program(pid)

    def _delete_program(self):
        pid = self._selected_id()
        if pid is None:
            return
        programs = load_programs()
        prog = next((p for p in programs if p["id"] == pid), None)
        if not prog:
            return
        if not messagebox.askyesno("Confirm", f"Delete '{prog['name']}'?", parent=self):
            return
        save_programs([p for p in programs if p["id"] != pid])
        self._refresh()
        self.app.status(f"Program '{prog['name']}' deleted.")


# ── Program Detail Screen ──────────────────────────────────────────────────────
class ProgramDetailScreen(tk.Frame):
    def __init__(self, parent, app, program_id: int):
        super().__init__(parent, bg=PANEL)
        self.app               = app
        self.program_id        = program_id
        self._current_module_id = None
        self.program           = None
        self._build()

    def _load_program(self):
        programs = load_programs()
        self.program = next((p for p in programs if p["id"] == self.program_id), None)

    def _build(self):
        self._load_program()
        if not self.program:
            tk.Label(self, text="Program not found.", bg=PANEL, fg=RED,
                     font=FONT_BOLD).pack(pady=20)
            styled_button(self, "← Back", self._back, width=10).pack()
            return

        p = self.program

        # ── Header ──
        hdr = tk.Frame(self, bg=BG3, highlightbackground=ORANGE3, highlightthickness=1)
        hdr.pack(fill="x", padx=10, pady=(8,4))

        left_hdr = tk.Frame(hdr, bg=BG3)
        left_hdr.pack(side="left", padx=8, pady=6)
        styled_button(left_hdr, "← Back", self._back, width=8).pack(side="left", padx=(0,10))
        tk.Label(left_hdr, text=p.get("name",""), bg=BG3, fg=ORANGE,
                 font=FONT_BOLD_L).pack(side="left")
        ptype = TYPE_DISPLAY.get(p.get("type",""), p.get("type","").upper())
        tk.Label(left_hdr, text=f"  [{ptype}]", bg=BG3, fg=ORANGE_DIM,
                 font=FONT_MONO_S).pack(side="left")

        right_hdr = tk.Frame(hdr, bg=BG3)
        right_hdr.pack(side="right", padx=8, pady=6)
        tk.Label(right_hdr, text="Start:", bg=BG3, fg=ORANGE_DIM,
                 font=FONT_MONO_S).pack(side="left")
        self.start_var = tk.StringVar(value=p.get("start_date",""))
        styled_entry(right_hdr, textvariable=self.start_var, width=11).pack(side="left", padx=4)
        tk.Label(right_hdr, text="Target:", bg=BG3, fg=ORANGE_DIM,
                 font=FONT_MONO_S).pack(side="left", padx=(6,0))
        self.target_var = tk.StringVar(value=p.get("target_date",""))
        styled_entry(right_hdr, textvariable=self.target_var, width=11).pack(side="left", padx=4)
        styled_button(right_hdr, "Save Dates", self._save_dates, width=11,
                      bg=ORANGE3, colour=BG).pack(side="left", padx=6)

        # ── Progress bar ──
        prog_frame = tk.Frame(self, bg=BG3, highlightbackground=ORANGE3, highlightthickness=1)
        prog_frame.pack(fill="x", padx=10, pady=(0,4))
        self.prog_canvas = tk.Canvas(prog_frame, bg=BG3, height=30, highlightthickness=0)
        self.prog_canvas.pack(fill="x", padx=10, pady=6)
        self.prog_canvas.bind("<Configure>", lambda e: self._draw_progress())

        # ── Two-pane ──
        panes = tk.Frame(self, bg=PANEL)
        panes.pack(fill="both", expand=True, padx=10, pady=4)
        panes.columnconfigure(0, weight=1)
        panes.columnconfigure(1, weight=2)
        panes.rowconfigure(0, weight=1)

        # Left: module list
        left = tk.Frame(panes, bg=BG3, highlightbackground=ORANGE3, highlightthickness=1)
        left.grid(row=0, column=0, sticky="nsew", padx=(0,4))
        tk.Label(left, text="MODULES", bg=BG3, fg=ORANGE, font=FONT_BOLD).pack(pady=(6,2))
        tk.Frame(left, bg=ORANGE3, height=1).pack(fill="x", padx=6)

        mod_cols = ("#","Title","Hrs","Status")
        self.mod_tree = make_treeview(left, mod_cols, heights=16)
        self.mod_tree.column("#",      width=28,  stretch=False)
        self.mod_tree.column("Title",  width=160, stretch=True)
        self.mod_tree.column("Hrs",    width=36,  stretch=False)
        self.mod_tree.column("Status", width=50,  stretch=False)
        for c in mod_cols:
            self.mod_tree.heading(c, text=c)
        self.mod_tree.bind("<<TreeviewSelect>>", self._on_module_select)

        # Right: detail panel
        right = tk.Frame(panes, bg=BG3, highlightbackground=ORANGE3, highlightthickness=1)
        right.grid(row=0, column=1, sticky="nsew")

        self.detail_title = tk.Label(right, text="Select a module", bg=BG3, fg=ORANGE,
                                      font=FONT_BOLD_L, wraplength=380, justify="left", anchor="w")
        self.detail_title.pack(fill="x", padx=10, pady=(8,4))
        tk.Frame(right, bg=ORANGE3, height=1).pack(fill="x", padx=8)

        tk.Label(right, text="Description:", bg=BG3, fg=ORANGE_DIM,
                 font=FONT_MONO_S).pack(anchor="w", padx=10, pady=(6,1))
        self.detail_desc = scrolledtext.ScrolledText(right, bg=BG2, fg=ORANGE, font=FONT_MONO_S,
                                                      relief="flat", bd=0, height=5,
                                                      wrap="word", state="disabled")
        self.detail_desc.pack(fill="x", padx=10, pady=(0,4))

        tk.Label(right, text="Resources:", bg=BG3, fg=ORANGE_DIM,
                 font=FONT_MONO_S).pack(anchor="w", padx=10, pady=(2,1))
        self.res_lb = tk.Listbox(right, bg=BG2, fg=ORANGE2, font=("Consolas", 8),
                                  selectbackground=ORANGE3, selectforeground=BG,
                                  relief="flat", bd=0, height=3, activestyle="none")
        self.res_lb.pack(fill="x", padx=10, pady=(0,4))

        tk.Label(right, text="Notes:", bg=BG3, fg=ORANGE_DIM,
                 font=FONT_MONO_S).pack(anchor="w", padx=10, pady=(2,1))
        self.notes_box = styled_text(right, height=3, width=50)
        self.notes_box.pack(fill="x", padx=10, pady=(0,4))
        self.notes_box.bind("<FocusOut>", lambda e: self._save_notes())

        btn_row = tk.Frame(right, bg=BG3)
        btn_row.pack(padx=10, pady=4, anchor="w")
        styled_button(btn_row, "✓ Mark Complete", self._mark_complete, width=16,
                      bg=ORANGE3, colour=BG).pack(side="left", padx=(0,4))
        styled_button(btn_row, "▶ In Progress", self._mark_in_progress, width=14).pack(side="left", padx=4)
        styled_button(btn_row, "— Reset", self._mark_not_started, width=10).pack(side="left", padx=4)

        # ── Stats bar ──
        stats_bar = tk.Frame(self, bg=BG3, highlightbackground=ORANGE3, highlightthickness=1)
        stats_bar.pack(fill="x", padx=10, pady=(0,8))
        self.stat_labels = {}
        for key in ("Total Hours","Completed","Remaining","Progress"):
            col = tk.Frame(stats_bar, bg=BG3)
            col.pack(side="left", expand=True, fill="x", ipadx=4, ipady=4)
            tk.Label(col, text=key, bg=BG3, fg=ORANGE_DIM, font=FONT_MONO_S).pack()
            lbl = tk.Label(col, text="—", bg=BG3, fg=ORANGE, font=FONT_BOLD)
            lbl.pack()
            self.stat_labels[key] = lbl

        self._refresh_modules()

    def _compute_stats(self):
        mods    = self.program.get("modules", [])
        total_h = sum(m.get("estimated_hours", 0) for m in mods)
        done_h  = sum(m.get("estimated_hours", 0) for m in mods if m.get("status") == "complete")
        pct     = int(done_h / total_h * 100) if total_h else 0
        done_n  = sum(1 for m in mods if m.get("status") == "complete")
        total_n = len(mods)
        return total_h, done_h, total_h - done_h, pct, done_n, total_n

    def _draw_progress(self):
        self._load_program()
        _, _, _, pct, done_n, total_n = self._compute_stats()
        self.prog_canvas.delete("all")
        w = self.prog_canvas.winfo_width() or 600
        bar_w = int(w * 0.72)
        filled = int(bar_w * pct / 100)
        self.prog_canvas.create_rectangle(0, 4, bar_w, 26, fill=BG2, outline=ORANGE3)
        if filled > 0:
            fill_col = GREEN if pct == 100 else ORANGE
            self.prog_canvas.create_rectangle(0, 4, filled, 26, fill=fill_col, outline="")
        self.prog_canvas.create_text(
            bar_w + 10, 15,
            text=f"{pct}%  ({done_n}/{total_n} modules)",
            fill=ORANGE, font=FONT_BOLD, anchor="w")

    def _refresh_modules(self):
        self._load_program()
        for row in self.mod_tree.get_children():
            self.mod_tree.delete(row)
        STATUS_SYM = {"not_started": "—", "in_progress": "▶", "complete": "✓"}
        for m in self.program.get("modules", []):
            sym = STATUS_SYM.get(m.get("status","not_started"), "—")
            tag = m.get("status","not_started")
            self.mod_tree.insert("", "end", iid=str(m["id"]), values=(
                m["id"], m.get("title","")[:32],
                m.get("estimated_hours",""), sym,
            ), tags=(tag,))
        self.mod_tree.tag_configure("complete",    foreground=GREEN)
        self.mod_tree.tag_configure("in_progress", foreground=ORANGE)
        self.mod_tree.tag_configure("not_started", foreground=GREY)
        # update stats bar
        total_h, done_h, rem_h, pct, _, _ = self._compute_stats()
        self.stat_labels["Total Hours"].config(text=f"{total_h:.1f}h")
        self.stat_labels["Completed"].config(text=f"{done_h:.1f}h")
        self.stat_labels["Remaining"].config(text=f"{rem_h:.1f}h")
        self.stat_labels["Progress"].config(text=f"{pct}%",
                                             fg=GREEN if pct == 100 else ORANGE)
        self.after(50, self._draw_progress)

    def _on_module_select(self, event=None):
        sel = self.mod_tree.selection()
        if not sel:
            return
        mid = int(sel[0])
        self._current_module_id = mid
        module = next((m for m in self.program.get("modules",[]) if m["id"] == mid), None)
        if module:
            self._show_module_detail(module)

    def _show_module_detail(self, module):
        self.detail_title.config(text=module.get("title",""))
        self.detail_desc.config(state="normal")
        self.detail_desc.delete("1.0","end")
        self.detail_desc.insert("1.0", module.get("description",""))
        self.detail_desc.config(state="disabled")
        self.res_lb.delete(0,"end")
        for r in module.get("resources",[]):
            self.res_lb.insert("end", f"  {r}")
        self.notes_box.delete("1.0","end")
        self.notes_box.insert("1.0", module.get("notes",""))

    def _get_current_module(self):
        if self._current_module_id is None:
            messagebox.showinfo("Select", "Select a module first.", parent=self)
            return None
        return next((m for m in self.program.get("modules",[])
                     if m["id"] == self._current_module_id), None)

    def _save_notes(self):
        if self._current_module_id is None:
            return
        programs = load_programs()
        for p in programs:
            if p["id"] == self.program_id:
                for m in p.get("modules",[]):
                    if m["id"] == self._current_module_id:
                        m["notes"] = self.notes_box.get("1.0","end").strip()
        save_programs(programs)
        self._load_program()

    def _set_module_status(self, status):
        mod = self._get_current_module()
        if not mod:
            return
        programs = load_programs()
        for p in programs:
            if p["id"] == self.program_id:
                for m in p.get("modules",[]):
                    if m["id"] == self._current_module_id:
                        m["status"] = status
                        m["completed_date"] = today_str() if status == "complete" else None
        save_programs(programs)
        self._refresh_modules()
        # re-select the same module
        try:
            self.mod_tree.selection_set(str(self._current_module_id))
            self._on_module_select()
        except Exception:
            pass
        self.app.status(f"Module {self._current_module_id} → {status}.")

    def _mark_complete(self):    self._set_module_status("complete")
    def _mark_in_progress(self): self._set_module_status("in_progress")
    def _mark_not_started(self): self._set_module_status("not_started")

    def _save_dates(self):
        start  = self.start_var.get().strip()
        target = self.target_var.get().strip()
        for val in [start, target]:
            if val:
                try:
                    datetime.strptime(val, "%Y-%m-%d")
                except ValueError:
                    messagebox.showwarning("Format", "Dates must be YYYY-MM-DD.", parent=self)
                    return
        programs = load_programs()
        for p in programs:
            if p["id"] == self.program_id:
                p["start_date"]  = start
                p["target_date"] = target
        save_programs(programs)
        self._load_program()
        self.app.status("Dates saved.")

    def _back(self):
        self.app.show("courses")


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
            ("courses",    "◉  Courses"),
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
            "courses":   CoursesScreen,
        }
        cls = screen_map.get(name)
        if cls:
            screen = cls(self.content, self)
            screen.pack(fill="both", expand=True)
        self._update_badge()

    def show_program(self, program_id: int):
        for k, btn in self.nav_buttons.items():
            btn.config(bg=ORANGE3 if k == "courses" else BG2,
                       fg=BG if k == "courses" else ORANGE)
        for w in self.content.winfo_children():
            w.destroy()
        ProgramDetailScreen(self.content, self, program_id).pack(fill="both", expand=True)
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
