#!/usr/bin/env python3
"""
ThreatPad Demo Launcher
=======================
Loads four pre-built incident tabs and launches ThreatPad from src/.

Usage:
    python threatpad_demo.py
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

SCRIPT_DIR    = Path(__file__).resolve().parent
SRC_DIR       = SCRIPT_DIR / "src"
THREATPAD_PY  = SRC_DIR / "threatpad.py"
SESSION_FILE  = SRC_DIR / "session.json"
SETTINGS_FILE = SRC_DIR / "app_settings.json"
SNIPPETS_FILE = SRC_DIR / "copy_pasta_snippets.json"

TODAY = datetime.now().strftime("%Y-%m-%d")


# ─────────────────────────────────────────────────────────────────────────────
# DEMO SETTINGS
# ─────────────────────────────────────────────────────────────────────────────

DEMO_SETTINGS = {
    "dark_mode": True,
    "follow_system_theme": False,
    "line_numbers": True,
    "word_wrap": True,
    "font_size": 13,
    "font_family": "Consolas",
    "syntax_highlighting": True,
    "api_keys": {"virustotal": "", "abuseipdb": ""},
    "clients": ["Client Alpha", "Client Beta", "Client Gamma"],
}

DEMO_SNIPPETS = {
    "Incident Header": (
        "=== INCIDENT ANALYSIS ===\n"
        "Date       : {date}\nAnalyst    : \nIncident ID: INC-\n"
        "Severity   : [LOW/MEDIUM/HIGH/CRITICAL]\nStatus     : OPEN\n\n"
    ),
    "IOC Section": (
        "\n--- INDICATORS OF COMPROMISE ---\n"
        "IPs:\n- \n\nDomains:\n- \n\nURLs:\n- \n\nHashes:\n- \n\nEmails:\n- \n\n"
    ),
    "Timeline":      "\n--- TIMELINE ---\n[{date} HH:MM]  \n\n",
    "Remediation":   "\n--- REMEDIATION ---\n[ ] 1. \n[ ] 2. \n[ ] 3. \n\n",
    "Executive Summary": (
        "\n--- EXECUTIVE SUMMARY ---\n"
        "Threat Level : \nImpact       : \nRecommended  : \n\n"
    ),
    "Escalation Note": (
        "\n--- ESCALATION NOTE ---\nEscalated To : \nReason       : \nTime         : \n\n"
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# DEMO TAB CONTENT
# ─────────────────────────────────────────────────────────────────────────────

TAB_GUIDE = f"""\
╔══════════════════════════════════════════════════════════════════════════════╗
║                      THREATPAD  –  DEMO WALKTHROUGH GUIDE                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

 1.  ASCII QUICK MENU  (Ctrl+`)
     • Ctrl+` pops the 3-level keyboard menu:
         Level 1  N=New Incident  O=Open  P=Phone Call  M=Meeting Notes
         Level 2  1-5 to pick template
         Level 3  1-3 to pick client  (ESC goes back)
     • Ctrl+1  Defang → copy to clipboard → save to history → reopen menu
     • Ctrl+2  Wrap current note in Escalation Note template

 2.  MULTI-TAB MANAGEMENT
     • Ctrl+N new tab  •  middle-click to close  •  session auto-saved

 3.  IOC EXTRACTION  (Ctrl+I)
     • Try on each incident tab — tree view groups IOCs by type

 4.  DEFANG / REFANG  (Ctrl+D / Ctrl+R)
     • Select all (Ctrl+A) then Ctrl+D to defang everything
     • Ctrl+R to restore — partial selection also works

 5.  IOC ENRICHMENT  (Ctrl+Shift+E)
     • Free geolocation via ip-api.com (no key needed)
     • Add VirusTotal / AbuseIPDB keys in Tools → Settings → API Keys

 6.  EXPORT IOCs  (Ctrl+E)  →  CSV / JSON / TXT

 7.  CLIENT LIST  (Tools → Settings → Clients)
     • Add/edit/delete clients — instantly reflected in Ctrl+` menu

─── SHORTCUTS ────────────────────────────────────────────────────────────────
  Ctrl+`        Quick Action Menu     Ctrl+1   Defang+Copy+Save+Menu
  Ctrl+2        Escalation Note       Ctrl+D   Defang
  Ctrl+I        Extract IOCs          Ctrl+R   Refang
  Ctrl+E        Export IOCs           Ctrl+F   Find
  Ctrl+Shift+E  Enrich IOCs           Ctrl+S   Save

Generated: {TODAY}
"""

TAB_PHISHING = f"""\
=== INCIDENT ANALYSIS ===
Date       : {TODAY}
Analyst    :
Incident ID: INC-2024-001
Severity   : HIGH
Status     : INVESTIGATING
Client     : Client Alpha

--- DESCRIPTION ---
Targeted credential-phishing campaign against Finance and HR.
47 employees received spear-phishing emails impersonating IT helpdesk.
3 users clicked and entered credentials on the fake portal.

--- INDICATORS OF COMPROMISE ---
Source IPs:
- 203.0.113.47
- 203.0.113.112

Phishing Domains:
- it-helpdesk-portal.example-phish.com
- secure-login.corp-verify.net

Phishing URLs:
- http://it-helpdesk-portal.example-phish.com/login?ref=corp
- https://secure-login.corp-verify.net/verify/reset?tok=Ab3xQ

Sender Emails:
- helpdesk@it-support-noreply.example-phish.com
- noreply@corp-verify.net

--- TIMELINE ---
[{TODAY} 07:14]  First phishing email received
[{TODAY} 07:45]  First user clicks link (WS-FIN-004)
[{TODAY} 08:03]  SOC alerted via SIEM
[{TODAY} 09:00]  Domains blocked at DNS

--- REMEDIATION ---
[x] 1. Isolate WS-FIN-004, WS-HR-011, WS-FIN-019
[x] 2. Block IPs at perimeter
[ ] 3. Force password reset for 3 affected users
[ ] 4. Submit headers to email gateway vendor
"""

TAB_RANSOMWARE = f"""\
=== RANSOMWARE RESPONSE ===
Date       : {TODAY}
Analyst    :
Incident ID: INC-2024-002
Severity   : CRITICAL
Status     : CONTAINED
Client     : Client Beta

--- DESCRIPTION ---
LockBit 3.0 variant deployed on six production servers after lateral
movement from a compromised VPN account.

--- MALWARE HASHES ---
Dropper (lb3_dropper.exe):
  MD5    : a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4
  SHA1   : a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2
  SHA256 : a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2

Encryptor (svc_update.dll):
  MD5    : dead0000beef1111cafe2222babe3333
  SHA256 : dead0000beef1111cafe2222babe3333dead0000beef1111cafe2222babe33334444

--- C2 INFRASTRUCTURE ---
IPs:
- 192.0.2.201
- 192.0.2.202

Domains:
- c2-updates.lockb-panel.example.net

URLs:
- https://c2-updates.lockb-panel.example.net/api/v1/beacon
- https://192.0.2.201:8443/check-in

--- TIMELINE ---
[{TODAY} 02:17]  Malicious VPN login from 198.51.100.55
[{TODAY} 03:22]  File encryption begins (.locked extension)
[{TODAY} 03:55]  On-call analyst confirms ransomware
[{TODAY} 04:30]  Servers isolated — CONTAINED

--- REMEDIATION ---
[x] 1. Isolate DB-PROD-01 through DB-PROD-06
[x] 2. Disable compromised VPN account
[ ] 3. Restore from last clean snapshot
[ ] 4. Emergency patch EternalBlue vulnerability
"""

TAB_APT = f"""\
=== APT INVESTIGATION ===
Date       : {TODAY}
Analyst    :
Incident ID: INC-2024-003
Severity   : HIGH
Status     : OPEN
Client     : Client Gamma

--- DESCRIPTION ---
Suspected nation-state actor. Custom implant communicating over IPv6
to evade IPv4-only firewall rules. Source code exfiltration suspected.

--- IOCs (DEFANGED — use Ctrl+R to refang) ---
IPv6 C2:
- 2001[:]0db8[:]85a3[:]0000[:]0000[:]8a2e[:]0370[:]7334
- fe80[:]0000[:]0000[:]0000[:]0204[:]61ff[:]fe9d[:]f156

IPv4 C2 (defanged):
- 192[.]0[.]2[.]99
- 198[.]51[.]100[.]77

Domains (defanged):
- update-telemetry[.]eng-cdn[.]example-apt[.]net
- git-sync[.]internal-tools[.]example-threat[.]com

Implant hash:
  SHA256 : cafebabe0000111122223333444455aacafebabe0000111122223333444455aabb00

--- MITRE TTPs ---
T1566.001  Spear-phishing attachment
T1071.001  C2 over HTTPS
T1048.003  Exfiltration via DNS
T1027      Obfuscated files

--- TIMELINE ---
[2024-01-15 ~02:00]  Suspected initial phishing (reconstructed)
[{TODAY} 09:12]       EDR alert: unusual IPv6 outbound on ENG-WS-007
[{TODAY} 10:30]       GIT-SERVER-01 access confirmed from implant account

--- REMEDIATION ---
[x] 1. Block IPv6 egress at perimeter (emergency change)
[x] 2. Isolate ENG-WS-007, ENG-WS-014, ENG-WS-031
[ ] 3. Forensic imaging of affected hosts
[ ] 4. Review GIT-SERVER-01 for exfiltrated repos
[ ] 5. Engage external IR for attribution
"""

DEMO_SESSION = {
    "tabs": [
        {"title": "DEMO GUIDE",              "content": TAB_GUIDE,       "filepath": None},
        {"title": "INC-2024-001 Phishing",   "content": TAB_PHISHING,    "filepath": None},
        {"title": "INC-2024-002 Ransomware", "content": TAB_RANSOMWARE,  "filepath": None},
        {"title": "INC-2024-003 APT",        "content": TAB_APT,         "filepath": None},
    ]
}


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def banner(msg):
    print("\n" + "═" * 68)
    print(f"  {msg}")
    print("═" * 68)

def step(msg):  print(f"  ▶  {msg}")
def ok(msg):    print(f"  ✔  {msg}")
def err(msg):   print(f"  ✘  {msg}"); sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# SETUP
# ─────────────────────────────────────────────────────────────────────────────

def check_src():
    if not THREATPAD_PY.exists():
        err(f"src/threatpad.py not found — make sure this script is next to the src/ folder.")
    ok("src/threatpad.py found")

def write_settings():
    step("Writing demo settings")
    with open(SETTINGS_FILE, "w") as f:
        json.dump(DEMO_SETTINGS, f, indent=2)
    ok("Settings written")

def write_session():
    step("Writing demo session (4 tabs)")
    with open(SESSION_FILE, "w") as f:
        json.dump(DEMO_SESSION, f, indent=2)
    ok("Session written")

def write_snippets():
    step("Writing snippets")
    with open(SNIPPETS_FILE, "w") as f:
        json.dump(DEMO_SNIPPETS, f, indent=2)
    ok("Snippets written")

def check_deps():
    step("Checking dependencies")
    missing, optional = [], []
    for pkg in ("tkinter", "tkinterdnd2"):
        try:
            __import__("tkinter" if pkg == "tkinter" else pkg)
        except ImportError:
            missing.append(pkg)
    for pkg in ("spellchecker", "requests"):
        try:
            __import__(pkg)
        except ImportError:
            optional.append(pkg)
    if missing:
        print(f"\n  ! Missing required: {', '.join(missing)}")
        print(f"    pip install tkinterdnd2")
    if optional:
        print(f"  ℹ  Optional not installed: {', '.join(optional)}")
        print(f"     pip install requests pyspellchecker")
    if not missing:
        ok("Core dependencies OK")
    return not missing

def launch():
    step(f"Launching ThreatPad from src/")
    print()
    try:
        subprocess.run([sys.executable, str(THREATPAD_PY)],
                       cwd=str(SRC_DIR), check=False)
    except KeyboardInterrupt:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    banner("ThreatPad Demo Launcher")
    print(f"  Date : {TODAY}")
    print(f"  Src  : {SRC_DIR}")
    print()

    check_src()
    write_settings()
    write_session()
    write_snippets()
    deps_ok = check_deps()

    print()
    banner("Demo ready — launching ThreatPad")
    print()
    for tab in DEMO_SESSION["tabs"]:
        print(f"    •  {tab['title']}")
    print()
    print("  Open the DEMO GUIDE tab first for the full walkthrough.")
    print()

    if not deps_ok:
        print("  ⚠  Fix missing dependencies then re-run.")
        sys.exit(1)

    launch()
    print()
    banner("ThreatPad closed")


if __name__ == "__main__":
    main()
