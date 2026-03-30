#!/usr/bin/env python3
"""
ThreatPad Demo Launcher
=======================
Prepares a fully loaded demo environment and launches ThreatPad with
four realistic incident tabs, optimal display settings, and a built-in
walkthrough guide — ready to show to anyone in minutes.

Usage:
    python threatpad_demo.py
"""

import os
import sys
import json
import zipfile
import shutil
import subprocess
import platform
from pathlib import Path
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────────────────

SCRIPT_DIR    = Path(__file__).resolve().parent
ZIP_SOURCE    = SCRIPT_DIR / "Threatpad-v2-main.zip"
DEMO_DIR      = SCRIPT_DIR / "threatpad_demo_run"
INNER_DIR     = DEMO_DIR / "Threatpad-v2-main"   # what the zip extracts to
THREATPAD_PY  = INNER_DIR / "threatpad.py"
SESSION_FILE  = INNER_DIR / "session.json"
SETTINGS_FILE = INNER_DIR / "app_settings.json"
SNIPPETS_FILE = INNER_DIR / "copy_pasta_snippets.json"
ASCII_MENU_SRC = SCRIPT_DIR / "ascii_menu.py"
ASCII_MENU_DST = INNER_DIR / "ascii_menu.py"


# ─────────────────────────────────────────────────────────────────────────────
# DEMO SETTINGS  (dark mode, line numbers, syntax highlighting on for demo)
# ─────────────────────────────────────────────────────────────────────────────

DEMO_SETTINGS = {
    "dark_mode": True,
    "follow_system_theme": False,
    "line_numbers": True,
    "word_wrap": True,
    "font_size": 13,
    "font_family": "Consolas",
    "syntax_highlighting": True,
    "api_keys": {
        "virustotal": "",
        "abuseipdb": ""
    }
}


# ─────────────────────────────────────────────────────────────────────────────
# DEMO COPY-PASTA SNIPPETS  (extended for richer demo)
# ─────────────────────────────────────────────────────────────────────────────

DEMO_SNIPPETS = {
    "Incident Header": (
        "=== INCIDENT ANALYSIS ===\n"
        "Date       : {date}\n"
        "Analyst    : {analyst}\n"
        "Incident ID: INC-{id}\n"
        "Severity   : [LOW / MEDIUM / HIGH / CRITICAL]\n"
        "Status     : [OPEN / INVESTIGATING / CONTAINED / CLOSED]\n\n"
    ),
    "IOC Section": (
        "\n--- INDICATORS OF COMPROMISE (IOCs) ---\n"
        "IPs:\n- \n\n"
        "Domains:\n- \n\n"
        "URLs:\n- \n\n"
        "Hashes (MD5 / SHA1 / SHA256):\n- \n\n"
        "Emails:\n- \n\n"
    ),
    "Timeline": (
        "\n--- TIMELINE ---\n"
        "[YYYY-MM-DD HH:MM] Event description\n"
        "[YYYY-MM-DD HH:MM] Event description\n\n"
    ),
    "Remediation": (
        "\n--- REMEDIATION STEPS ---\n"
        "[ ] 1. Isolate affected host(s)\n"
        "[ ] 2. Block IOCs at perimeter\n"
        "[ ] 3. Reset compromised credentials\n"
        "[ ] 4. Preserve evidence / capture memory\n"
        "[ ] 5. Notify stakeholders\n\n"
    ),
    "Executive Summary": (
        "\n--- EXECUTIVE SUMMARY ---\n"
        "Threat Level        : \n"
        "Business Impact     : \n"
        "Affected Systems    : \n"
        "Recommended Actions : \n\n"
    ),
    "Escalation Note": (
        "\n--- ESCALATION NOTE ---\n"
        "Escalated To : \n"
        "Reason       : \n"
        "Time         : \n\n"
    )
}


# ─────────────────────────────────────────────────────────────────────────────
# DEMO TAB CONTENT
# Four realistic (but entirely fictional) incident scenarios
# ─────────────────────────────────────────────────────────────────────────────

TODAY = datetime.now().strftime("%Y-%m-%d")

TAB_GUIDE = f"""\
╔══════════════════════════════════════════════════════════════════════════════╗
║                      THREATPAD  –  DEMO WALKTHROUGH GUIDE                  ║
║                  (This tab is your presenter cheat-sheet)                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

Welcome!  This environment has been pre-loaded with three realistic incident
tabs so you can demo every major ThreatPad feature without any setup.

─── FEATURE CHECKLIST ────────────────────────────────────────────────────────

 1.  ASCII QUICK MENU  (Ctrl+`)
     • Press Ctrl+` (backtick) to pop up the Quick Action Menu — or use
       File → Quick Action Menu.
     • Level 1 — Action:    N=New Incident  O=Open Incident  P=Phone  M=Meeting
     • Level 2 — Template:  press the NUMBER shown (1–5) or click the label
     • Level 3 — Client:    press the NUMBER shown (1–3) or click
     • A new tab is created instantly with the right header pre-filled.
     • ESC goes back one level at any time.

     CTRL+1  (rapid close & send)
     • Defangs the current tab, checks no raw IOCs remain,
       silently copies the defanged note to clipboard,
       saves it to the Last-15 history,
       saves the file, then reopens the Quick Menu ready for the next call.

     CTRL+2  (escalation)
     • Wraps the current note inside an Escalation Note template
       as a new tab.  Then use Ctrl+1 on that tab to copy & send.

 2.  MULTI-TAB INCIDENT MANAGEMENT
     • Show the four tabs at the top (this guide + three incidents).
     • Ctrl+N opens a new blank tab.  Middle-click a tab to close it.
     • Each tab auto-saves to the session on close.

 2.  COPY-PASTA SNIPPETS  (Insert menu → Snippets, or toolbar button)
     • Demonstrate inserting "Incident Header", "IOC Section", "Timeline",
       "Remediation" and "Executive Summary" into a blank new tab.
     • Show how analysts build reports in seconds with pre-built templates.

 3.  IOC EXTRACTION  (Ctrl+I  or  Analysis menu → Extract IOCs)
     • Switch to "INC-2024-001 Phishing Campaign" tab.
     • Press Ctrl+I — a tree-view window shows all detected IOCs sorted by
       type: IPv4, Domain, URL, Email.
     • Repeat on "INC-2024-002 Ransomware" to show MD5/SHA1/SHA256 hashes.
     • Repeat on "INC-2024-003 APT Activity" to show IPv6 addresses.

 4.  DEFANG & REFANG  (Ctrl+D / Ctrl+R)
     • On the Phishing tab, select all (Ctrl+A) then press Ctrl+D.
     • Watch every IP, URL and domain get defanged for safe sharing
       (e.g.  http://  →  hxxp://   and   .  →  [.]  in domains).
     • Press Ctrl+R to refang back to working indicators instantly.
     • Partial selection also works — highlight just one IP and defang it.

 5.  IOC ENRICHMENT  (Ctrl+Shift+E  or  Analysis → Enrich IOCs)
     • ThreatPad queries ip-api.com (free, no key) for geolocation.
     • If VirusTotal / AbuseIPDB API keys are set in Settings, richer
       context (reputation scores, malware detections) appears automatically.
     • Demo the Settings dialog to show where keys are configured.

 6.  EXPORT IOCs  (Ctrl+E  or  Analysis menu → Export IOCs)
     • Export as  CSV  (for SIEM import / ticketing),
                  JSON (for automation pipelines),
                  TXT  (for quick sharing).

 7.  FIND & REPLACE  (Ctrl+F / Ctrl+H)
     • Great for bulk-updating analyst names, incident IDs, or severity tags.

 8.  APPEARANCE CUSTOMISATION  (View menu)
     • Toggle Dark / Light mode live.
     • Adjust font size with  Ctrl++  /  Ctrl+-
     • Toggle line numbers and word-wrap per analyst preference.

 9.  DRAG-AND-DROP FILE SUPPORT
     • Drag any  .txt / .log / .csv  file straight into ThreatPad to open it
       as a new tab — no file-picker needed.

10.  SPELL CHECK  (Edit menu, if pyspellchecker is installed)
     • Helps analysts catch typos in reports before forwarding to management.

─── KEYBOARD SHORTCUTS CHEAT SHEET ──────────────────────────────────────────

  Ctrl+`          Quick Action Menu       Ctrl+1   Defang+Copy+Save+Menu
  Ctrl+2          Escalation Note         Ctrl+D   Defang
  Ctrl+I          Extract IOCs            Ctrl+R   Refang
  Ctrl+E          Export IOCs             Ctrl+F   Find
  Ctrl+Shift+E    Enrich IOCs             Ctrl+H   Replace
  Ctrl+N          New tab                 Ctrl+S   Save
  Ctrl+O          Open file               Ctrl+Z/Y Undo / Redo

─── NOTES FOR THE PRESENTER ─────────────────────────────────────────────────

• All IOCs in this demo are FICTIONAL and used for demonstration only.
• No real malicious infrastructure is referenced.
• API keys are intentionally blank; enrich-feature still shows the UI flow.
• Generated: {TODAY}

"""

TAB_PHISHING = f"""\
=== INCIDENT ANALYSIS ===
Date       : {TODAY}
Analyst    : Demo Analyst
Incident ID: INC-2024-001
Severity   : HIGH
Status     : INVESTIGATING

--- EXECUTIVE SUMMARY ---
A targeted credential-phishing campaign was detected targeting the Finance
and HR departments.  Forty-seven employees received spear-phishing emails
impersonating the company's IT helpdesk.  Three users clicked the link and
entered credentials on the fake login portal.

Threat Level        : HIGH
Business Impact     : Potential credential compromise for 3 users
Affected Systems    : Corporate email gateway, 3 user workstations
Recommended Actions : Reset affected passwords, block IOCs, user awareness

--- INDICATORS OF COMPROMISE (IOCs) ---

IPs (C2 / hosting):
- 203.0.113.47
- 203.0.113.112
- 198.51.100.88

Phishing Domains:
- it-helpdesk-portal.example-phish.com
- secure-login.corp-verify.net
- account-reset.internal-itsupport.org

Phishing URLs:
- http://it-helpdesk-portal.example-phish.com/login?ref=corp
- https://secure-login.corp-verify.net/verify/reset?tok=Ab3xQ
- http://198.51.100.88/static/login.php

Sender Emails (spoofed):
- helpdesk@it-support-noreply.example-phish.com
- noreply@corp-verify.net
- security-alerts@internal-itsupport.org

Redirect Chain:
  http://bit.ly.example.co/redir1 → http://203.0.113.47/land → phishing page

--- TIMELINE ---
[{TODAY} 07:14]  First phishing email received by finance@victim-corp.example
[{TODAY} 07:31]  Email gateway flags burst of 47 identical messages
[{TODAY} 07:45]  First user clicks phishing link (workstation WS-FIN-004)
[{TODAY} 07:52]  Second user credential entry detected (WS-HR-011)
[{TODAY} 08:03]  SOC alerted via SIEM rule "Phishing URL Click"
[{TODAY} 08:15]  Analyst begins investigation — this note created
[{TODAY} 08:40]  Third user confirmed credential entry (WS-FIN-019)
[{TODAY} 09:00]  IT blocks phishing domains at DNS layer

--- REMEDIATION STEPS ---
[x] 1. Isolate WS-FIN-004, WS-HR-011, WS-FIN-019 from network
[x] 2. Block 203.0.113.47, 203.0.113.112, 198.51.100.88 at perimeter FW
[x] 3. Sinkhole phishing domains at internal DNS
[ ] 4. Force password reset for 3 affected users
[ ] 5. Notify HR and Finance managers
[ ] 6. Submit email headers to email gateway vendor for signature
[ ] 7. Close ticket once password resets confirmed

--- ADDITIONAL NOTES ---
Email headers show SPF FAIL and DKIM NONE — spoofed From address.
Phishing kit hosted on compromised shared-hosting server (CPanel panel spotted).
"""

TAB_RANSOMWARE = f"""\
=== INCIDENT ANALYSIS ===
Date       : {TODAY}
Analyst    : Demo Analyst
Incident ID: INC-2024-002
Severity   : CRITICAL
Status     : CONTAINED

--- EXECUTIVE SUMMARY ---
LockBit 3.0 variant ransomware deployed on six servers in the production
environment after a threat actor moved laterally from a compromised VPN
account.  Files encrypted with .locked extension.  Ransom note dropped.

Threat Level        : CRITICAL
Business Impact     : Production database servers offline, estimated 4h downtime
Affected Systems    : DB-PROD-01 through DB-PROD-06, FILE-SERVER-02
Recommended Actions : Restore from clean backup, patch VPN, rotate all creds

--- MALWARE FILE HASHES ---

Ransomware dropper (lb3_dropper.exe):
  MD5    : a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4
  SHA1   : a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2
  SHA256 : a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2

Ransom encryptor payload (svc_update.dll):
  MD5    : dead0000beef1111cafe2222babe3333
  SHA1   : dead0000beef1111cafe2222babe3333dead0000
  SHA256 : dead0000beef1111cafe2222babe3333dead0000beef1111cafe2222babe33334444

Persistence tool (task_sched_helper.exe):
  MD5    : 0f1e2d3c4b5a6978a8b7c6d5e4f3a2b1
  SHA1   : 0f1e2d3c4b5a6978a8b7c6d5e4f3a2b10f1e2d3c
  SHA256 : 0f1e2d3c4b5a6978a8b7c6d5e4f3a2b10f1e2d3c4b5a6978a8b7c6d5e4f3a2b1ff

--- C2 INFRASTRUCTURE ---

Command & Control IPs:
- 192.0.2.201
- 192.0.2.202
- 198.51.100.200

C2 Domains:
- c2-updates.lockb-panel.example.net
- telemetry-cdn.svc-update.example.com

C2 URLs (beacon callbacks):
- https://c2-updates.lockb-panel.example.net/api/v1/beacon
- https://192.0.2.201:8443/check-in

Tor Leak Site (defanged):
- hxxp://lockbit3example[.]onion/victim/INC-DEMO-2024

--- INITIAL ACCESS ---
Compromised VPN account: jsmith_vpn (Finance dept)
Source IP of malicious VPN login: 198.51.100.55
Time of initial access: {TODAY} 02:17 UTC

--- LATERAL MOVEMENT PATH ---
VPN Gateway → WS-FINANCE-022 → ADMIN-JUMP-01 → DB-PROD-01 (PSExec)
DB-PROD-01 spread to DB-PROD-02 through DB-PROD-06 via SMB (EternalBlue variant)

--- TIMELINE ---
[{TODAY} 02:17]  Malicious VPN login from 198.51.100.55 (jsmith_vpn)
[{TODAY} 02:34]  Attacker drops lb3_dropper.exe on WS-FINANCE-022
[{TODAY} 02:51]  Lateral movement begins — PSExec to ADMIN-JUMP-01
[{TODAY} 03:15]  Ransomware propagates to DB-PROD-01 → 06
[{TODAY} 03:22]  File encryption begins; .locked extension observed
[{TODAY} 03:40]  SIEM fires "Mass File Rename" alert — SOC paged
[{TODAY} 03:55]  On-call analyst confirms ransomware; IR plan activated
[{TODAY} 04:10]  Affected servers isolated from network
[{TODAY} 04:30]  Incident declared CONTAINED

--- REMEDIATION STEPS ---
[x] 1. Isolate DB-PROD-01 through DB-PROD-06 and FILE-SERVER-02
[x] 2. Disable compromised VPN account jsmith_vpn
[x] 3. Block C2 IPs and domains at perimeter
[ ] 4. Restore DB servers from last clean snapshot (T-12h)
[ ] 5. Emergency patch for EternalBlue vulnerability on all Windows servers
[ ] 6. Rotate all service account passwords
[ ] 7. Forensic imaging of affected hosts before restore
[ ] 8. Executive briefing at 09:00

"""

TAB_APT = f"""\
=== INCIDENT ANALYSIS ===
Date       : {TODAY}
Analyst    : Demo Analyst
Incident ID: INC-2024-003
Severity   : HIGH
Status     : OPEN

--- EXECUTIVE SUMMARY ---
Suspected nation-state APT activity detected.  Attacker accessed engineering
workstations over several weeks using a custom implant communicating over IPv6
to evade IPv4-only firewall rules.  Exfiltration of source code suspected.

Threat Level        : HIGH
Business Impact     : Potential IP theft (source code repository)
Affected Systems    : ENG-WS-007, ENG-WS-014, ENG-WS-031, GIT-SERVER-01
Recommended Actions : Full forensic investigation, network re-segmentation

--- INDICATORS OF COMPROMISE (IOCs) ─ DEFANGED FOR SAFE SHARING ---

NOTE: The IOCs below are defanged.  Use Ctrl+R (Refang) to restore them
for ingestion into your SIEM, EDR, or firewall blocklist.

IPv6 C2 Addresses (defanged):
- 2001[:]0db8[:]85a3[:]0000[:]0000[:]8a2e[:]0370[:]7334
- 2001[:]0db8[:]0000[:]0000[:]0000[:]0000[:]0000[:]0001
- fe80[:]0000[:]0000[:]0000[:]0204[:]61ff[:]fe9d[:]f156

IPv4 C2 Addresses (defanged):
- 192[.]0[.]2[.]99
- 198[.]51[.]100[.]77

Malicious Domains (defanged):
- update-telemetry[.]eng-cdn[.]example-apt[.]net
- git-sync[.]internal-tools[.]example-threat[.]com
- cdn-static[.]assets-update[.]example-c2[.]org

Malicious URLs (defanged):
- hxxps[:]//update-telemetry[.]eng-cdn[.]example-apt[.]net/delta/push
- hxxps[:]//198[.]51[.]100[.]77[:]4443/implant/beacon

Implant Contact Emails (actor infrastructure):
- operator1@secure-mail.example-apt.net
- drops@exfil-collector.example-threat.com

--- IMPLANT / MALWARE HASHES ---

Custom implant (eng_updater.exe):
  MD5    : cafebabe0000111122223333444455aa
  SHA1   : cafebabe0000111122223333444455aacafebabe
  SHA256 : cafebabe0000111122223333444455aacafebabe0000111122223333444455aabb00

Loader (msvc_runtime_helper.dll):
  MD5    : 11223344556677889900aabbccddeeff
  SHA256 : 11223344556677889900aabbccddeeff11223344556677889900aabbccddeeffaa

--- NETWORK INDICATORS ---

Beacon interval  : 300 seconds (jitter ±60s)
Protocol         : HTTPS over port 4443 (non-standard)
User-Agent       : Mozilla/5.0 (compatible; MSIE 9.0; custom)
DNS over HTTPS   : Queries routed via Cloudflare DoH (1.1.1.1) to bypass DNS logging
IPv6 tunnelling  : Used to evade perimeter IPv4-only controls

--- TTPS (MITRE ATT&CK) ---

T1566.001  Spear-phishing attachment (initial access)
T1059.001  PowerShell (execution)
T1071.001  Application layer protocol: Web (C2)
T1048.003  Exfiltration over alternative protocol: DNS
T1027      Obfuscated files or information
T1090.003  Multi-hop proxy (Tor + IPv6)
T1560.001  Archive collected data: zip encryption

--- TIMELINE ---
[2024-01-15 ~02:00]  Suspected initial phishing delivery (reconstructed)
[2024-01-15 ~03:00]  First implant beacon observed in NetFlow logs (retroactive)
[{TODAY} 09:12]       EDR alert: unusual IPv6 outbound on ENG-WS-007
[{TODAY} 09:35]       Analyst pivots — finds 3-week-old beaconing pattern
[{TODAY} 10:00]       ENG-WS-014 and ENG-WS-031 identified as also compromised
[{TODAY} 10:30]       GIT-SERVER-01 access from ENG-WS-007 service account confirmed
[{TODAY} 11:00]       IR team assembled; full forensics initiated

--- REMEDIATION STEPS ---
[x] 1. Block IPv6 egress at perimeter (emergency change)
[x] 2. Isolate ENG-WS-007, ENG-WS-014, ENG-WS-031 from network
[ ] 3. Forensic imaging of all four affected systems (in progress)
[ ] 4. Review GIT-SERVER-01 access logs for exfiltrated repos
[ ] 5. Rotate all engineering service account credentials
[ ] 6. Audit and tighten IPv6 firewall policy network-wide
[ ] 7. Engage external IR firm for threat-actor attribution
[ ] 8. Notify legal / executive team re: potential IP theft
[ ] 9. Implement DNS logging and DoH blocking

--- ESCALATION NOTE ---
Escalated To : CISO, Legal Counsel
Reason       : Suspected nation-state actor; potential IP theft
Time         : {TODAY} 11:30

"""


DEMO_SESSION = {
    "tabs": [
        {"title": "DEMO GUIDE",                  "content": TAB_GUIDE,       "filepath": None},
        {"title": "INC-2024-001 Phishing",        "content": TAB_PHISHING,    "filepath": None},
        {"title": "INC-2024-002 Ransomware",      "content": TAB_RANSOMWARE,  "filepath": None},
        {"title": "INC-2024-003 APT Activity",    "content": TAB_APT,         "filepath": None},
    ]
}


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def banner(msg: str):
    width = 70
    print("\n" + "═" * width)
    print(f"  {msg}")
    print("═" * width)

def step(msg: str):
    print(f"  ▶  {msg}")

def ok(msg: str):
    print(f"  ✔  {msg}")

def err(msg: str):
    print(f"  ✘  {msg}")
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# SETUP
# ─────────────────────────────────────────────────────────────────────────────

def extract_threatpad():
    """Extract ThreatPad from zip into demo_run directory."""
    if not ZIP_SOURCE.exists():
        err(f"Cannot find {ZIP_SOURCE.name} — make sure this script is in the "
             "same folder as Threatpad-v2-main.zip")

    step(f"Extracting {ZIP_SOURCE.name} → {DEMO_DIR.name}/")

    # Fresh extract every time so settings are always written cleanly
    if DEMO_DIR.exists():
        shutil.rmtree(DEMO_DIR)
    DEMO_DIR.mkdir(parents=True)

    with zipfile.ZipFile(ZIP_SOURCE, "r") as zf:
        zf.extractall(DEMO_DIR)

    if not THREATPAD_PY.exists():
        err(f"Extracted OK but cannot find threatpad.py at expected path:\n  {THREATPAD_PY}")

    ok("ThreatPad extracted")


def write_settings():
    """Write demo-optimised app_settings.json."""
    step("Writing demo app_settings.json (dark mode, line numbers, syntax highlighting)")
    with open(SETTINGS_FILE, "w") as f:
        json.dump(DEMO_SETTINGS, f, indent=2)
    ok("Settings written")


def write_session():
    """Pre-load all four demo tabs into session.json."""
    step("Pre-loading 4 demo incident tabs into session.json")
    with open(SESSION_FILE, "w") as f:
        json.dump(DEMO_SESSION, f, indent=2)
    ok(f"Session written ({len(DEMO_SESSION['tabs'])} tabs)")


def write_snippets():
    """Write enriched copy-pasta snippets."""
    step("Writing extended copy-pasta snippets")
    with open(SNIPPETS_FILE, "w") as f:
        json.dump(DEMO_SNIPPETS, f, indent=2)
    ok("Snippets written")


def check_dependencies():
    """Check for required Python packages and warn if missing."""
    step("Checking Python dependencies")
    missing = []
    for pkg in ("tkinter", "tkinterdnd2"):
        try:
            if pkg == "tkinter":
                import tkinter  # noqa: F401
            elif pkg == "tkinterdnd2":
                import tkinterdnd2  # noqa: F401
        except ImportError:
            missing.append(pkg)

    optional_missing = []
    for pkg in ("spellchecker", "requests"):
        try:
            __import__(pkg)
        except ImportError:
            optional_missing.append(pkg)

    if missing:
        print()
        print("  ! Missing required package(s):", ", ".join(missing))
        print("    Install with:  pip install", " ".join(
            ["tkinterdnd2"] if "tkinterdnd2" in missing else missing))
        print()
    if optional_missing:
        print(f"  ℹ  Optional package(s) not installed: {', '.join(optional_missing)}")
        print("     IOC enrichment requires: pip install requests")
        print("     Spell check requires   : pip install pyspellchecker")

    if not missing:
        ok("Core dependencies OK")

    return not missing  # True = safe to launch


def install_ascii_menu():
    """Copy ascii_menu.py into the extracted ThreatPad directory and patch threatpad.py."""

    # ── 1. Copy the module ────────────────────────────────────────────────────
    if not ASCII_MENU_SRC.exists():
        print("  ⚠  ascii_menu.py not found — ASCII Quick Menu will be skipped.")
        return
    step("Copying ascii_menu.py into ThreatPad directory")
    shutil.copy2(ASCII_MENU_SRC, ASCII_MENU_DST)
    ok("ascii_menu.py copied")

    # ── 2. Patch threatpad.py ─────────────────────────────────────────────────
    step("Patching threatpad.py to enable ASCII Quick Menu")
    src = THREATPAD_PY.read_text(encoding="utf-8")

    # Guard: skip if already patched
    if "ascii_menu" in src:
        ok("threatpad.py already patched — skipping")
        return

    # Patch A: add import after the ioc_enrichment import block
    import_patch = (
        "try:\n"
        "    from ioc_enrichment import IOCEnrichment\n"
        "    IOC_ENRICHMENT_AVAILABLE = True\n"
        "except ImportError:\n"
        "    IOC_ENRICHMENT_AVAILABLE = False\n"
        "    IOCEnrichment = None"
    )
    import_addition = (
        "\ntry:\n"
        "    from ascii_menu import ASCIIMenuIntegration\n"
        "    ASCII_MENU_AVAILABLE = True\n"
        "except ImportError:\n"
        "    ASCII_MENU_AVAILABLE = False\n"
        "    ASCIIMenuIntegration = None"
    )
    if import_patch in src:
        src = src.replace(import_patch, import_patch + import_addition)

    # Patch B: initialise integration after load_templates_data()
    init_anchor = "        self.load_templates_data()"
    init_addition = (
        "\n\n        # ASCII Quick Menu integration\n"
        "        self.ascii_menu_integration = None\n"
        "        if ASCII_MENU_AVAILABLE:\n"
        "            self.ascii_menu_integration = ASCIIMenuIntegration(self)"
    )
    if init_anchor in src and "ascii_menu_integration" not in src:
        src = src.replace(init_anchor, init_anchor + init_addition)

    # Patch C: bind keys (after existing keybinding block)
    kb_anchor = "        self.root.bind('<Control-minus>', lambda e: self.decrease_font_size())"
    kb_addition = (
        "\n        # ASCII Quick Menu keybindings\n"
        "        if self.ascii_menu_integration:\n"
        "            self.ascii_menu_integration.bind_keys()"
    )
    if kb_anchor in src and "ascii_menu_integration.bind_keys" not in src:
        src = src.replace(kb_anchor, kb_anchor + kb_addition)

    # Patch D: add menu entry in File menu (before "Close Tab")
    menu_anchor = '        file_menu.add_command(label="Close Tab"'
    menu_addition = (
        '        file_menu.add_command(\n'
        '            label="Quick Action Menu  Ctrl+`",\n'
        '            command=lambda: self.ascii_menu_integration.show_menu()\n'
        '                    if self.ascii_menu_integration else None)\n'
        '        file_menu.add_separator()\n'
        '        '
    )
    if menu_anchor in src and "Quick Action Menu" not in src:
        src = src.replace(menu_anchor, menu_addition + 'file_menu.add_command(label="Close Tab"')

    # Patch E: add CLIENTS to Config class (after API_KEYS block)
    clients_anchor = "    API_KEYS = {\n        'virustotal': '',\n        'abuseipdb': ''\n    }"
    clients_addition = (
        "\n    CLIENTS = [\"Client Alpha\", \"Client Beta\", \"Client Gamma\"]"
    )
    if clients_anchor in src and "CLIENTS = [" not in src:
        src = src.replace(clients_anchor, clients_anchor + clients_addition)

    # Patch F: load clients in load_settings
    load_anchor = "                    self.config.API_KEYS = settings.get('api_keys', {'virustotal': '', 'abuseipdb': ''})"
    load_addition = (
        "\n                    self.config.CLIENTS = settings.get('clients', self.config.CLIENTS)"
    )
    if load_anchor in src and "settings.get('clients'" not in src:
        src = src.replace(load_anchor, load_anchor + load_addition)

    # Patch G: save clients in save_settings
    save_anchor = "                'api_keys': self.config.API_KEYS"
    save_addition = ",\n                'clients': self.config.CLIENTS"
    if save_anchor in src and "'clients': self.config.CLIENTS" not in src:
        src = src.replace(save_anchor, save_anchor + save_addition)

    # Patch H: add Clients tab in show_settings_window (before General tab)
    clients_tab_anchor = "        # General tab\n        general_frame = ttk.Frame(notebook)"
    clients_tab_addition = (
        "        # Clients tab\n"
        "        clients_frame = ttk.Frame(notebook)\n"
        "        notebook.add(clients_frame, text=\"Clients\")\n"
        "        self.create_clients_tab(clients_frame)\n\n        "
    )
    if clients_tab_anchor in src and "create_clients_tab" not in src:
        src = src.replace(clients_tab_anchor,
                          clients_tab_addition + "# General tab\n        general_frame = ttk.Frame(notebook)")

    # Patch I: save clients in apply_settings_changes (before self.save_settings())
    apply_anchor = "        self.save_settings()\n        self.save_snippets()"
    apply_addition = (
        "        if hasattr(self, 'clients_listbox'):\n"
        "            self.config.CLIENTS = list(self.clients_listbox.get(0, tk.END))\n"
        "            if self.ascii_menu_integration:\n"
        "                self.ascii_menu_integration.config.reload()\n"
        "        "
    )
    if apply_anchor in src and "clients_listbox" not in src:
        src = src.replace(apply_anchor, apply_addition + apply_anchor)

    # Patch J: add create_clients_tab method (before apply_settings_changes)
    method_anchor = "    def apply_settings_changes(self):"
    clients_method = '''\
    def create_clients_tab(self, parent):
        """Manage the client list used by the ASCII Quick Menu."""
        ttk.Label(parent, text="Clients shown in the Quick Action Menu (Ctrl+`):").pack(
            anchor="w", padx=10, pady=(10, 2))

        list_frame = ttk.Frame(parent)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.clients_listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE)
        self.clients_listbox.pack(side="left", fill="both", expand=True)
        for c in self.config.CLIENTS:
            self.clients_listbox.insert(tk.END, c)

        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(side="right", fill="y", padx=(8, 0))

        self._client_name_var = tk.StringVar()
        ttk.Label(btn_frame, text="Name:").pack(anchor="w", pady=(0, 2))
        name_entry = ttk.Entry(btn_frame, textvariable=self._client_name_var, width=22)
        name_entry.pack(anchor="w", pady=(0, 8))

        def _add_client():
            name = self._client_name_var.get().strip()
            if name:
                self.clients_listbox.insert(tk.END, name)
                self._client_name_var.set("")
                name_entry.focus_set()

        def _update_client():
            sel = self.clients_listbox.curselection()
            name = self._client_name_var.get().strip()
            if sel and name:
                self.clients_listbox.delete(sel[0])
                self.clients_listbox.insert(sel[0], name)
                self.clients_listbox.selection_set(sel[0])

        def _delete_client():
            sel = self.clients_listbox.curselection()
            if sel:
                self.clients_listbox.delete(sel[0])
                self._client_name_var.set("")

        def _on_select(_event=None):
            sel = self.clients_listbox.curselection()
            if sel:
                self._client_name_var.set(self.clients_listbox.get(sel[0]))

        self.clients_listbox.bind("<<ListboxSelect>>", _on_select)

        ttk.Button(btn_frame, text="Add",    command=_add_client,    width=10).pack(pady=2)
        ttk.Button(btn_frame, text="Update", command=_update_client, width=10).pack(pady=2)
        ttk.Button(btn_frame, text="Delete", command=_delete_client, width=10).pack(pady=2)

        ttk.Label(parent,
                  text="Changes take effect when you click Apply or OK.",
                  foreground="gray").pack(anchor="w", padx=10, pady=(4, 0))

'''
    if method_anchor in src and "def create_clients_tab" not in src:
        src = src.replace(method_anchor, clients_method + method_anchor)

    THREATPAD_PY.write_text(src, encoding="utf-8")
    ok("threatpad.py patched (ASCII Quick Menu + Clients tab enabled)")


def launch_threatpad():
    """Launch ThreatPad from the demo directory."""
    python = sys.executable
    step(f"Launching ThreatPad with {python}")
    print()

    try:
        subprocess.run(
            [python, str(THREATPAD_PY)],
            cwd=str(INNER_DIR),
            check=False
        )
    except KeyboardInterrupt:
        pass
    except FileNotFoundError:
        err(f"Python interpreter not found: {python}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    banner("ThreatPad Demo Launcher")
    print(f"  Date : {TODAY}")
    print(f"  Dir  : {SCRIPT_DIR}")
    print()

    extract_threatpad()
    write_settings()
    write_session()
    write_snippets()
    install_ascii_menu()
    deps_ok = check_dependencies()

    print()
    banner("Demo ready — launching ThreatPad")
    print()
    print("  Tabs pre-loaded:")
    for tab in DEMO_SESSION["tabs"]:
        print(f"    •  {tab['title']}")
    print()
    print("  Tip: Open the DEMO GUIDE tab first for a full feature walkthrough.")
    print()

    if not deps_ok:
        print("  ⚠  Required dependencies missing. Fix them then re-run this script.")
        sys.exit(1)

    launch_threatpad()

    print()
    banner("ThreatPad closed — demo session ended")


if __name__ == "__main__":
    main()
