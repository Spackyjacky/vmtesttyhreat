"""
Command Center — Personal Performance System
Tkinter rebuild — black/orange terminal aesthetic
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import json, csv, os, sys, sqlite3, threading, webbrowser
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
PROGRAMS_JSON  = DATA_DIR / "programs.json"
WINS_JSON      = DATA_DIR / "wins.json"
KPIS_JSON      = DATA_DIR / "kpis.json"
INCIDENTS_JSON  = DATA_DIR / "incidents.json"
WEEKLY_JSON     = DATA_DIR / "weekly_plans.json"
WINSTATE_JSON   = DATA_DIR / "window_state.json"
DEV_PLANS_JSON  = DATA_DIR / "dev_plans.json"

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

FONT_MONO   = ("Consolas", 12)
FONT_MONO_S = ("Consolas", 11)
FONT_MONO_L = ("Consolas", 13)
FONT_BOLD   = ("Consolas", 12, "bold")
FONT_BOLD_L = ("Consolas", 15, "bold")
FONT_TITLE  = ("Consolas", 19, "bold")

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

def load_dev_plans():
    if not DEV_PLANS_JSON.exists():
        return []
    try:
        return json.loads(DEV_PLANS_JSON.read_text()) or []
    except Exception:
        return []

def save_dev_plans(plans):
    DEV_PLANS_JSON.write_text(json.dumps(plans, indent=2))

def _soc_dev_plan():
    """Returns the pre-built SOC L1→L3 development plan seed data."""
    return {
        "id": 1,
        "name": "SOC Career Development: L1 → L3",
        "description": (
            "A structured roadmap from L1 SOC Analyst to L3 Senior SOC Analyst, covering "
            "the full skill stack required for progression in a modern Microsoft-stack Security "
            "Operations Centre. Each milestone builds on the last — complete them in order for "
            "maximum impact. Completing milestones here logs wins and tracks your career KPIs."
        ),
        "current_level": "L1",
        "target_level": "L3",
        "created_date": "2026-04-06",
        "target_date": "2027-10-01",
        "status": "active",
        "milestones": [
            {"id":1,"phase":"Phase 1: Solidify L1 Core","title":"Master KQL and Microsoft Sentinel Fundamentals","description":"Build fluency in Kusto Query Language (KQL) to query logs across Microsoft Sentinel workspaces. Learn to write queries against SecurityEvent, SigninLogs, CommonSecurityLog, and AuditLogs tables. This is the foundation of all triage and investigation work in a Microsoft-stack SOC.","skills":["KQL query writing","Log table navigation","Sentinel workspace management","Alert rule anatomy"],"resources":["https://learn.microsoft.com/en-us/azure/data-explorer/kusto/query/","https://learn.microsoft.com/en-us/training/paths/sc-200-utilize-kql-for-azure-sentinel/","https://github.com/reprise99/Sentinel-Queries"],"estimated_weeks":3,"level":"L1→L2","status":"not_started","completed_date":None,"notes":""},
            {"id":2,"phase":"Phase 1: Solidify L1 Core","title":"SC-200 Certification — Microsoft Security Operations Analyst","description":"Complete the SC-200 exam to validate skills across Microsoft Defender XDR, Sentinel, and cloud security operations. This certification is already in progress and provides structured coverage of the full Microsoft security stack used daily in the SOC. Passing this cert signals readiness for expanded L1 responsibilities and L2 shadowing.","skills":["Microsoft Defender XDR","Sentinel incident management","Threat intelligence integration","SOAR playbook basics"],"resources":["https://learn.microsoft.com/en-us/certifications/exams/sc-200/","https://learn.microsoft.com/en-us/training/courses/sc-200t00","https://github.com/MicrosoftLearning/SC-200T00A-Microsoft-Security-Operations-Analyst"],"estimated_weeks":4,"level":"L1→L2","status":"in_progress","completed_date":None,"notes":"Already in progress via Courses tab — sync progress there."},
            {"id":3,"phase":"Phase 1: Solidify L1 Core","title":"MITRE ATT&CK Framework — Practical Mapping","description":"Go beyond reading the ATT&CK matrix — practice mapping real alerts to specific techniques and sub-techniques. Use ATT&CK Navigator to build adversary emulation layers and understand which techniques your SIEM detects vs. has blind spots for. This skill transforms alert triage from reactive to contextual.","skills":["Technique-to-alert mapping","ATT&CK Navigator","Tactic chain reasoning","Detection gap identification"],"resources":["https://attack.mitre.org/","https://mitre-attack.github.io/attack-navigator/","https://www.sans.org/blog/mitre-attack-framework-complete-guide/"],"estimated_weeks":2,"level":"L1→L2","status":"not_started","completed_date":None,"notes":""},
            {"id":4,"phase":"Phase 1: Solidify L1 Core","title":"Phishing and Email Threat Analysis","description":"Develop a repeatable methodology for triaging phishing emails: header analysis, URL detonation, attachment sandboxing, and sender reputation checks. Learn to pivot from an email IOC into a broader campaign investigation using URLScan, VirusTotal, and MXToolbox. This is the most common L1 task and speed and accuracy here is the key L2 differentiator.","skills":["Email header parsing","URL analysis and detonation","Attachment sandboxing","Phishing IOC extraction"],"resources":["https://urlscan.io/","https://www.virustotal.com/","https://mxtoolbox.com/EmailHeaders.aspx","https://learn.microsoft.com/en-us/microsoft-365/security/office-365-security/anti-phishing-policies-about"],"estimated_weeks":2,"level":"L1→L2","status":"not_started","completed_date":None,"notes":""},
            {"id":5,"phase":"Phase 1: Solidify L1 Core","title":"Network Forensics Fundamentals","description":"Learn to read and analyze packet captures (PCAPs) to reconstruct attacker activity, identify C2 communication patterns, and detect data exfiltration. Practice with Wireshark on known-malicious capture files from malware-traffic-analysis.net to develop pattern recognition for DNS tunneling, HTTP beaconing, and SMB lateral movement.","skills":["Wireshark packet analysis","DNS/HTTP/SMB protocol analysis","C2 beacon identification","PCAP-based IOC extraction"],"resources":["https://www.wireshark.org/docs/wsug_html_chunked/","https://www.malware-traffic-analysis.net/","https://unit42.paloaltonetworks.com/using-wireshark-identifying-hosts-and-users/"],"estimated_weeks":3,"level":"L1→L2","status":"not_started","completed_date":None,"notes":""},
            {"id":6,"phase":"Phase 1: Solidify L1 Core","title":"Endpoint Investigation with Microsoft Defender XDR","description":"Build proficiency in Defender XDR's device timeline, advanced hunting, and incident graph to reconstruct endpoint-based attack chains. Learn to trace process trees, review file and registry events, and identify persistence mechanisms from the Defender console. Understanding what happened on a single endpoint separates strong L1 from weak.","skills":["Defender device timeline analysis","Process tree investigation","Advanced Hunting in Defender XDR","Persistence mechanism identification"],"resources":["https://learn.microsoft.com/en-us/microsoft-365/security/defender/advanced-hunting-overview","https://learn.microsoft.com/en-us/microsoft-365/security/defender-endpoint/investigate-machines","https://github.com/microsoft/Microsoft-365-Defender-Hunting-Queries"],"estimated_weeks":3,"level":"L1→L2","status":"not_started","completed_date":None,"notes":""},
            {"id":7,"phase":"Phase 1: Solidify L1 Core","title":"Incident Response Process and Documentation","description":"Internalize the IR lifecycle (Preparation, Detection, Containment, Eradication, Recovery, Lessons Learned) and practice writing clear, evidence-backed incident tickets. Learn to document timelines, chain of custody, and recommended actions so a senior analyst can act without asking clarifying questions. Poor documentation is the most common reason L1 analysts stall.","skills":["IR lifecycle phases","Incident ticket writing","Evidence chain of custody","Timeline reconstruction"],"resources":["https://www.nist.gov/publications/computer-security-incident-handling-guide","https://www.sans.org/white-papers/33901/","https://github.com/certsocietegenerale/IRM"],"estimated_weeks":2,"level":"L1→L2","status":"not_started","completed_date":None,"notes":""},
            {"id":8,"phase":"Phase 1: Solidify L1 Core","title":"PowerShell for SOC Analysts","description":"Learn PowerShell fundamentals with a security focus: parsing event logs, querying Active Directory, automating repetitive triage steps, and reading malicious PowerShell. Practice decoding base64-encoded commands, understanding execution policy bypasses, and recognising LOLBin abuse patterns — attackers use PowerShell constantly.","skills":["PowerShell scripting basics","Event log parsing","PowerShell deobfuscation","AD querying with PowerShell"],"resources":["https://learn.microsoft.com/en-us/powershell/scripting/learn/ps101/00-introduction","https://github.com/danielbohannon/Invoke-Obfuscation","https://www.sans.org/blog/powershell-for-incident-response/"],"estimated_weeks":3,"level":"L1→L2","status":"not_started","completed_date":None,"notes":""},
            {"id":9,"phase":"Phase 1: Solidify L1 Core","title":"Threat Intelligence Consumption and IOC Management","description":"Learn to ingest, evaluate, and operationalise threat intelligence feeds — distinguishing high-fidelity IOCs from noise. Practice enriching alerts with context from MISP, VirusTotal, and open-source threat reports. Understanding how to age out stale IOCs and prioritise high-confidence indicators prevents alert fatigue.","skills":["IOC enrichment workflow","Threat feed evaluation","MISP basics","Intel-to-alert correlation"],"resources":["https://www.misp-project.org/documentation/","https://otx.alienvault.com/","https://learn.microsoft.com/en-us/azure/sentinel/understand-threat-intelligence"],"estimated_weeks":2,"level":"L1→L2","status":"not_started","completed_date":None,"notes":""},
            {"id":10,"phase":"Phase 1: Solidify L1 Core","title":"CompTIA CySA+ Certification","description":"Earn CySA+ to validate broad SOC analyst competencies including threat and vulnerability management, software and systems security, compliance, incident response, and security architecture. This vendor-neutral cert is frequently listed as a requirement for L2 roles and provides a strong conceptual foundation before specialised GIAC certifications.","skills":["Vulnerability management","Threat hunting concepts","Compliance frameworks","Behavioral analytics"],"resources":["https://www.comptia.org/certifications/cybersecurity-analyst","https://www.professormesser.com/cybersecurity-analyst-plus/","https://www.examcompass.com/comptia/cysa-plus-practice-tests/"],"estimated_weeks":5,"level":"L1→L2","status":"not_started","completed_date":None,"notes":""},
            {"id":11,"phase":"Phase 2: L2 Analyst Depth","title":"Advanced KQL — Correlation Rules and Custom Detections","description":"Move from querying known tables to building multi-table join queries, time-window correlations, and custom scheduled analytics rules in Sentinel. Learn to write detections that reduce false positives through behavioural baselines and entity enrichment. L2 analysts own detection quality, not just consume alerts others built.","skills":["Multi-table KQL joins","Time-series anomaly queries","Sentinel analytics rule authoring","False positive tuning"],"resources":["https://learn.microsoft.com/en-us/azure/sentinel/detect-threats-custom","https://github.com/Azure/Azure-Sentinel/tree/master/Detections","https://www.kqlsearch.com/"],"estimated_weeks":3,"level":"L2→L3","status":"not_started","completed_date":None,"notes":""},
            {"id":12,"phase":"Phase 2: L2 Analyst Depth","title":"Malware Analysis Basics — Static and Dynamic","description":"Learn first-pass malware analysis: static analysis (strings, PE header inspection, YARA rules) and dynamic analysis (sandboxed detonation, behavioural monitoring). The goal is to extract IOCs, understand capabilities, and classify malware families accurately enough to escalate with full context — not to become a full reverse engineer.","skills":["PE file static analysis","Strings and hash analysis","Sandbox detonation","YARA rule basics"],"resources":["https://any.run/","https://www.hybrid-analysis.com/","https://github.com/VirusTotal/yara","https://malware.training/"],"estimated_weeks":4,"level":"L2→L3","status":"not_started","completed_date":None,"notes":""},
            {"id":13,"phase":"Phase 2: L2 Analyst Depth","title":"SOAR Playbook Development with Sentinel Logic Apps","description":"Design and build automation playbooks in Microsoft Sentinel using Azure Logic Apps to automate enrichment, containment, and notification workflows. Start with simple enrichment (auto-add VirusTotal reputation to alerts) then progress to response actions (isolate endpoint, disable user account). Automation is the primary force multiplier for L2 analysts.","skills":["Azure Logic Apps authoring","Sentinel playbook triggers","API-based enrichment automation","Automated containment actions"],"resources":["https://learn.microsoft.com/en-us/azure/sentinel/automate-responses-with-playbooks","https://github.com/Azure/Azure-Sentinel/tree/master/Playbooks","https://techcommunity.microsoft.com/t5/microsoft-sentinel-blog/"],"estimated_weeks":3,"level":"L2→L3","status":"not_started","completed_date":None,"notes":""},
            {"id":14,"phase":"Phase 2: L2 Analyst Depth","title":"Python Scripting for Security Automation","description":"Develop Python scripting skills focused on security tasks: automating IOC enrichment via REST APIs (VirusTotal, Shodan, Sentinel), parsing large log files, and building lightweight investigation tools. Python scripting is increasingly expected at L2 level and is the primary language for custom tooling in most SOC environments.","skills":["Python REST API integration","Log parsing with Python","VirusTotal/Shodan API automation","pandas for log analysis"],"resources":["https://docs.python.org/3/tutorial/","https://developers.virustotal.com/reference/overview","https://github.com/Te-k/harpoon"],"estimated_weeks":4,"level":"L2→L3","status":"not_started","completed_date":None,"notes":""},
            {"id":15,"phase":"Phase 2: L2 Analyst Depth","title":"Advanced Network Forensics — Encrypted Traffic and DNS","description":"Deepen network forensics skills to cover full packet capture analysis for lateral movement scenarios, encrypted traffic analysis (JA3/JA3S fingerprinting), and DNS-based attack detection (DGA domains, tunnelling). Practice reconstructing complete attack chains from Zeek/Bro logs and NetFlow data.","skills":["JA3/JA3S fingerprinting","DGA domain detection","Zeek/Bro log analysis","NetFlow analysis"],"resources":["https://github.com/salesforce/ja3","https://zeek.org/documentation/","https://www.malware-traffic-analysis.net/"],"estimated_weeks":3,"level":"L2→L3","status":"not_started","completed_date":None,"notes":""},
            {"id":16,"phase":"Phase 2: L2 Analyst Depth","title":"Threat Hunting — Hypothesis-Driven Investigations","description":"Learn structured threat hunting methodologies: develop hypotheses from ATT&CK techniques or threat intelligence, operationalise them as KQL hunts in Sentinel, and document findings positive or negative. Practice hunting for LOLBins, unusual scheduled tasks, and abnormal authentication patterns. Proactive hunting defines the L2 mindset.","skills":["Hunt hypothesis development","LOLBin detection hunting","Behavioural anomaly identification","Hunt documentation"],"resources":["https://github.com/OTRF/ThreatHunter-Playbook","https://www.activecountermeasures.com/threat-hunting-using-flow-data/","https://www.sans.org/white-papers/38700/"],"estimated_weeks":3,"level":"L2→L3","status":"not_started","completed_date":None,"notes":""},
            {"id":17,"phase":"Phase 2: L2 Analyst Depth","title":"Cloud Security Operations — Azure and M365","description":"Develop competency in investigating cloud-native attacks: Azure AD compromise (token theft, MFA bypass, OAuth abuse), Azure resource abuse (cryptomining, data exfiltration), and M365 attacks (mailbox delegation abuse, eDiscovery exfiltration). Cloud incidents require different investigation techniques than on-prem and are increasingly common.","skills":["Azure AD attack patterns","OAuth and token abuse","M365 security investigation","Azure activity log analysis"],"resources":["https://learn.microsoft.com/en-us/azure/active-directory/identity-protection/overview-identity-protection","https://learn.microsoft.com/en-us/microsoft-365/security/defender/microsoft-secure-score","https://github.com/dafthack/GraphRunner"],"estimated_weeks":4,"level":"L2→L3","status":"not_started","completed_date":None,"notes":""},
            {"id":18,"phase":"Phase 2: L2 Analyst Depth","title":"Detection Engineering — Writing and Tuning Detections","description":"Own the full detection lifecycle: identify coverage gaps using ATT&CK, write Sentinel analytics rules, test with Atomic Red Team simulations, measure false positive rates, and iterate based on real-world performance. Detection engineering is a core L2 expectation — analysts who only consume detections others built never reach L3.","skills":["Detection gap analysis","Atomic Red Team testing","Sigma rule writing","Detection performance metrics"],"resources":["https://github.com/redcanaryco/atomic-red-team","https://github.com/SigmaHQ/sigma","https://github.com/palantir/alerting-detection-strategy-framework","https://detectionlab.network/"],"estimated_weeks":4,"level":"L2→L3","status":"not_started","completed_date":None,"notes":""},
            {"id":19,"phase":"Phase 2: L2 Analyst Depth","title":"GIAC GCIH — Incident Handler Certification","description":"Pursue GIAC GCIH to formally validate incident handling skills across the full IR lifecycle including computer crime law, incident handling steps, network investigations, and malware analysis. GCIH is widely recognised as the gold standard for hands-on IR practitioners and is a common requirement for L3 and senior analyst roles.","skills":["Formal IR methodology","Evidence handling","Network attack response","Malware incident containment"],"resources":["https://www.giac.org/certifications/certified-incident-handler-gcih/","https://www.sans.org/cyber-security-courses/hacker-techniques-incident-handling/"],"estimated_weeks":8,"level":"L2→L3","status":"not_started","completed_date":None,"notes":""},
            {"id":20,"phase":"Phase 2: L2 Analyst Depth","title":"Digital Forensics and Incident Response (DFIR) Fundamentals","description":"Build hands-on DFIR skills: forensic disk imaging, memory acquisition and analysis with Volatility, Windows artifact analysis (MFT, prefetch, shimcache, registry hives), and timeline super-analysis. DFIR capability is what allows L2/L3 analysts to definitively answer 'what happened' rather than 'we think this happened'.","skills":["Memory forensics with Volatility","Windows artifact analysis","Forensic imaging and preservation","Timeline super-analysis"],"resources":["https://github.com/volatilityfoundation/volatility3","https://github.com/EricZimmerman/","https://dfir.training/","https://cyberdefenders.org/"],"estimated_weeks":5,"level":"L2→L3","status":"not_started","completed_date":None,"notes":""},
            {"id":21,"phase":"Phase 2: L2 Analyst Depth","title":"Advanced Malware Analysis — Behavioural and Code-Level","description":"Progress beyond sandbox detonation to manual behavioural analysis and introductory static code analysis using x64dbg or Ghidra. Understand common malware families (Emotet, QakBot, Cobalt Strike) well enough to identify them from behavioural patterns alone. Advanced malware analysis makes L3 analysts the final escalation point for complex cases.","skills":["x64dbg dynamic analysis","Ghidra static analysis basics","Packer identification and unpacking","Cobalt Strike beacon analysis"],"resources":["https://ghidra-sre.org/","https://github.com/x64dbg/x64dbg","https://github.com/HuskyHacks/PMAT-labs","https://bazaar.abuse.ch/"],"estimated_weeks":6,"level":"L2→L3","status":"not_started","completed_date":None,"notes":""},
            {"id":22,"phase":"Phase 2: L2 Analyst Depth","title":"Purple Team Operations — Adversary Emulation","description":"Lead or participate in purple team exercises where red team techniques are run in a controlled environment and blue team detections are validated in real time. Use Caldera or Atomic Red Team to emulate specific ATT&CK techniques, measure detection coverage, and feed gaps back into the detection engineering pipeline.","skills":["MITRE Caldera operation authoring","Detection validation methodology","Coverage gap reporting","Blue/red collaboration"],"resources":["https://github.com/mitre/caldera","https://github.com/redcanaryco/atomic-red-team","https://www.sans.org/blog/how-to-build-a-purple-team/"],"estimated_weeks":4,"level":"L2→L3","status":"not_started","completed_date":None,"notes":""},
            {"id":23,"phase":"Phase 2: L2 Analyst Depth","title":"Incident Response Leadership and Stakeholder Communication","description":"Develop skills for leading incident response calls: structured communication under pressure, technical-to-executive translation, running post-incident reviews, and coordinating across IT, legal, and leadership. L3 analysts are expected to own major incidents end-to-end and communicate findings clearly to non-technical stakeholders.","skills":["IR call leadership","Executive briefing writing","Post-incident review facilitation","Cross-team coordination"],"resources":["https://csrc.nist.gov/publications/detail/sp/800-61/rev-2/final","https://github.com/meirwah/awesome-incident-response","https://www.cisa.gov/sites/default/files/publications/Federal_Government_Cybersecurity_Incident_and_Vulnerability_Response_Playbooks_508C.pdf"],"estimated_weeks":3,"level":"L2→L3","status":"not_started","completed_date":None,"notes":""},
            {"id":24,"phase":"Phase 2: L2 Analyst Depth","title":"Mentoring and Knowledge Transfer","description":"Formalise mentoring skills by creating runbooks, triage guides, and onboarding materials for L1 analysts. Practice explaining complex investigations clearly and reviewing junior analysts' work with constructive, specific feedback. Multiplying team capability through others is a non-negotiable L3 competency — you cannot teach what you do not deeply understand.","skills":["Runbook and playbook writing","Technical documentation","L1 analyst coaching","Knowledge base maintenance"],"resources":["https://github.com/certsocietegenerale/IRM","https://github.com/counteractive/incident-response-plan-template","https://www.atlassian.com/incident-management/runbook"],"estimated_weeks":3,"level":"L2→L3","status":"not_started","completed_date":None,"notes":""},
            {"id":25,"phase":"Phase 2: L2 Analyst Depth","title":"GIAC GCIA — Intrusion Analyst Certification","description":"Earn GIAC GCIA to validate deep network traffic analysis and intrusion detection skills, including protocol analysis, signature writing for Snort/Suricata, and network forensic investigation. Combined with GCIH and CySA+, this certification portfolio demonstrates a complete L3-level competency profile to hiring managers and peers.","skills":["Snort/Suricata rule writing","Deep protocol analysis","Network intrusion detection","Traffic-based threat hunting"],"resources":["https://www.giac.org/certifications/certified-intrusion-analyst-gcia/","https://www.sans.org/cyber-security-courses/network-monitoring-threat-detection/","https://suricata.io/documentation/"],"estimated_weeks":8,"level":"L2→L3","status":"not_started","completed_date":None,"notes":""},
        ]
    }

def _json_load(path):
    if not path.exists(): return []
    try: return json.loads(path.read_text()) or []
    except: return []

def _json_save(path, data):
    path.write_text(json.dumps(data, indent=2))

def load_wins():    return _json_load(WINS_JSON)
def save_wins(d):   _json_save(WINS_JSON, d)
def load_kpis():
    if not KPIS_JSON.exists():
        return {"metrics": [], "entries": []}
    try:
        data = json.loads(KPIS_JSON.read_text())
        if not isinstance(data, dict):
            return {"metrics": [], "entries": []}
        data.setdefault("metrics", [])
        data.setdefault("entries", [])
        return data
    except Exception:
        return {"metrics": [], "entries": []}

def save_kpis(d):   _json_save(KPIS_JSON, d)
def load_incidents():   return _json_load(INCIDENTS_JSON)
def save_incidents(d):  _json_save(INCIDENTS_JSON, d)
def load_weekly():      return _json_load(WEEKLY_JSON)
def save_weekly(d):     _json_save(WEEKLY_JSON, d)

def load_window_state():
    try: return json.loads(WINSTATE_JSON.read_text())
    except: return {}

def save_window_state(geometry):
    WINSTATE_JSON.write_text(json.dumps({"geometry": geometry}))

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
        font=FONT_MONO_S, rowheight=26, borderwidth=0)
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

        # Stats row — keep references for auto-refresh
        self._stat_frame = tk.Frame(self, bg=PANEL)
        self._stat_frame.pack(fill="x", padx=20, pady=4)
        self._stat_boxes = {}
        self._draw_stats()
        self._schedule_refresh()

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

    def _draw_stats(self):
        for w in self._stat_frame.winfo_children():
            w.destroy()
        open_t   = len([t for t in load_tasks() if t.get("status") not in ("resolved",)])
        overdue  = len([t for t in load_tasks()
                        if t.get("due_date","") and t.get("due_date","") < today_str()
                        and t.get("status") != "resolved"])
        flagged  = len(get_flagged())
        wins_n   = len(load_wins())
        inc_open = len([i for i in load_incidents() if i.get("status") not in ("resolved","closed")])
        stats = [
            ("OPEN TASKS",    str(open_t),           open_t > 0 and not overdue),
            ("OVERDUE TASKS", str(overdue),           overdue > 0),
            ("REVIEW DUE",    str(flagged),           flagged > 0),
            ("WINS LOGGED",   str(wins_n),            False),
            ("OPEN INCIDENTS",str(inc_open),          inc_open > 0),
        ]
        for label, value, alert in stats:
            box = tk.Frame(self._stat_frame, bg=BG3,
                           highlightbackground=ORANGE3, highlightthickness=1)
            box.pack(side="left", expand=True, fill="x", padx=4, ipady=6)
            tk.Label(box, text=label, bg=BG3, fg=ORANGE_DIM, font=FONT_MONO_S).pack(pady=(4,0))
            tk.Label(box, text=value,  bg=BG3,
                     fg=RED if alert else GREEN,
                     font=FONT_BOLD_L).pack(pady=(0,4))

    def _refresh_stats(self):
        try:
            self._draw_stats()
        except Exception:
            pass

    def _schedule_refresh(self):
        try:
            self._draw_stats()
            self.after(30000, self._schedule_refresh)
        except Exception:
            pass

    def _open_tasks(self):
        return str(len([t for t in load_tasks() if t.get("status") not in ("resolved",)]))

    def _panel_quick(self, parent):
        f = tk.Frame(parent, bg=BG3, highlightbackground=ORANGE3, highlightthickness=1)
        f.grid(row=0, column=0, sticky="nsew", padx=6, pady=4)
        tk.Label(f, text="◆ QUICK ACTIONS", bg=BG3, fg=ORANGE, font=FONT_BOLD).pack(pady=(10,6))
        tk.Frame(f, bg=ORANGE3, height=1).pack(fill="x", padx=6)
        actions = [
            (" Memory Manager",  lambda: self.app.show("memory")),
            (" Decision Log",    lambda: self.app.show("decisions")),
            (" Task Manager",    lambda: self.app.show("tasks")),
            (" Daily Log",       lambda: self.app.show("log")),
            (" Wins & Achievmts",lambda: self.app.show("wins")),
            (" Weekly Planner",  lambda: self.app.show("planner")),
            (" KPI Tracker",     lambda: self.app.show("kpis")),
            (" Incident Timeline",lambda: self.app.show("incidents")),
            (" Courses",         lambda: self.app.show("courses")),
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
        self.geometry("520x360")
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

        # Due date
        tk.Label(form, text="Due Date:", bg=PANEL, fg=ORANGE_DIM,
                 font=FONT_MONO_S, width=12, anchor="e").grid(row=3, column=0, pady=6, sticky="e")
        due_row = tk.Frame(form, bg=PANEL)
        due_row.grid(row=3, column=1, padx=8, sticky="w")
        self.due_var = tk.StringVar(value=self.task.get("due_date","") if self.task else "")
        styled_entry(due_row, textvariable=self.due_var, width=14).pack(side="left")
        tk.Label(due_row, text="  YYYY-MM-DD  (optional)", bg=PANEL,
                 fg=ORANGE_DIM, font=("Consolas",8)).pack(side="left")

        btn_row = tk.Frame(self, bg=PANEL)
        btn_row.pack(pady=10)
        styled_button(btn_row, "Save", self._save, width=12, bg=ORANGE3, colour=BG).pack(side="left", padx=8)
        styled_button(btn_row, "Cancel", self.destroy, width=12).pack(side="left", padx=8)

    def _save(self):
        title = self.title_var.get().strip()
        if not title:
            messagebox.showwarning("Required", "Title is required.", parent=self)
            return
        due = self.due_var.get().strip()
        if due:
            try: datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                messagebox.showwarning("Format", "Due date must be YYYY-MM-DD.", parent=self)
                return
        self.result = {
            "title":       title,
            "description": self.desc_text.get("1.0","end").strip(),
            "priority":    self.prio_var.get(),
            "due_date":    due,
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
        cols = ("ID","Priority","Title","Description","Due","Status","Created")
        self.tree = make_treeview(self, cols, heights=14)
        self.tree.column("ID",          width=36,  stretch=False)
        self.tree.column("Priority",    width=76,  stretch=False)
        self.tree.column("Title",       width=180, stretch=True)
        self.tree.column("Description", width=160, stretch=True)
        self.tree.column("Due",         width=86,  stretch=False)
        self.tree.column("Status",      width=80,  stretch=False)
        self.tree.column("Created",     width=82,  stretch=False)
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
        today = today_str()
        for t in self._get_tasks():
            p    = t.get("priority","low")
            stat = t.get("status","open")
            due  = t.get("due_date","") or ""
            overdue = due and due < today and stat != "resolved"
            if stat == "resolved":   tag = "resolved_tag"
            elif overdue:            tag = "overdue"
            else:                    tag = p
            self.tree.insert("", "end", iid=str(t["id"]), values=(
                t.get("id",""),
                p.upper(),
                t.get("title","")[:38],
                t.get("description","")[:38],
                due if due else "—",
                stat,
                t.get("created","")[:10],
            ), tags=(tag,))
        for p in PRIORITIES:
            self.tree.tag_configure(p, foreground=PRIORITY_COLOUR[p])
        self.tree.tag_configure("resolved_tag", foreground=GREEN)
        self.tree.tag_configure("overdue",      foreground=RED)
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
                "due_date": result.get("due_date",""),
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
                    t["due_date"]    = result.get("due_date","")
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
        styled_button(bar, "Paste Course",  self._paste_course,  width=14).pack(side="left", padx=4)
        styled_button(bar, "Open",          self._open_program,  width=10).pack(side="left", padx=4)
        styled_button(bar, "Edit JSON",     self._edit_course,   width=10).pack(side="left", padx=4)
        styled_button(bar, "Delete",        self._delete_program, width=10).pack(side="left", padx=4)
        styled_button(bar, "Refresh",       self._refresh,        width=10).pack(side="right", padx=4)

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

        self.stats_label = tk.Label(self, text="", bg=PANEL, fg=ORANGE_DIM, font=FONT_MONO_S)
        self.stats_label.pack(padx=10, pady=4, anchor="w")
        self._refresh()

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

    def _paste_course(self):
        hint = (
            'Ask Claude to create a course/program and paste the JSON here.\n'
            'Required fields: "name", "type" (certification|course|book|project), "modules" (array).\n'
            'Each module needs: "id", "title", "description", "estimated_hours", "resources" (list), "notes" (str).'
        )
        def on_save(data):
            if not isinstance(data, dict):
                return "Must be a JSON object {…}"
            if "name" not in data:
                return "Missing required field: name"
            if "modules" not in data or not isinstance(data["modules"], list):
                return "Missing or invalid 'modules' array"
            programs = load_programs()
            data["id"] = max((p["id"] for p in programs), default=0) + 1
            data.setdefault("status", "active")
            data.setdefault("start_date", today_str())
            data.setdefault("type", "course")
            # Ensure module fields
            for i, m in enumerate(data["modules"]):
                m.setdefault("id", i + 1)
                m.setdefault("status", "not_started")
                m.setdefault("notes", "")
                m.setdefault("resources", [])
            programs.append(data)
            save_programs(programs)
            self._refresh()
            self.app.status(f"Course '{data['name']}' imported ({len(data['modules'])} modules).")
            return True
        PasteJSONModal(self, self.app, title="Paste Course JSON", hint=hint, on_save=on_save)

    def _edit_course(self):
        pid = self._selected_id()
        if pid is None:
            return
        programs = load_programs()
        prog = next((p for p in programs if p["id"] == pid), None)
        if not prog:
            return
        hint = "Edit the course JSON below, then click Validate & Import to save."
        def on_save(data):
            if not isinstance(data, dict):
                return "Must be a JSON object {…}"
            data["id"] = pid
            new_programs = [data if p["id"] == pid else p for p in programs]
            save_programs(new_programs)
            self._refresh()
            self.app.status(f"Course '{data.get('name','')}' updated.")
            return True
        modal = PasteJSONModal(self, self.app, title="Edit Course JSON", hint=hint, on_save=on_save)
        modal.txt.insert("1.0", json.dumps(prog, indent=2))


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

        # ── Pomodoro timer (bottom-anchored) ──
        pom_frame = tk.Frame(self, bg=BG3, highlightbackground=ORANGE3, highlightthickness=1)
        pom_frame.pack(side="bottom", fill="x", padx=10, pady=(0,4))
        tk.Label(pom_frame, text="◈ STUDY TIMER", bg=BG3, fg=ORANGE,
                 font=FONT_BOLD).pack(side="left", padx=10, pady=6)
        self._pom_running   = False
        self._pom_seconds   = 25 * 60
        self._pom_remaining = self._pom_seconds
        self._pom_job       = None
        self.pom_label = tk.Label(pom_frame, text="25:00", bg=BG3, fg=GREEN,
                                   font=("Consolas", 14, "bold"))
        self.pom_label.pack(side="left", padx=12)
        styled_button(pom_frame, "▶ Start",  self._pom_start,  width=9).pack(side="left", padx=4)
        styled_button(pom_frame, "⏸ Pause",  self._pom_pause,  width=9).pack(side="left", padx=4)
        styled_button(pom_frame, "↺ Reset",  self._pom_reset,  width=9).pack(side="left", padx=4)
        for mins in [25, 50, 5]:
            styled_button(pom_frame, f"{mins}m",
                          lambda m=mins: self._pom_set(m), width=5).pack(side="left", padx=2)
        self.pom_session_label = tk.Label(pom_frame, text="", bg=BG3,
                                           fg=ORANGE_DIM, font=FONT_MONO_S)
        self.pom_session_label.pack(side="right", padx=10)

        # ── Stats bar (bottom-anchored) ──
        stats_bar = tk.Frame(self, bg=BG3, highlightbackground=ORANGE3, highlightthickness=1)
        stats_bar.pack(side="bottom", fill="x", padx=10, pady=(0,4))
        self.stat_labels = {}
        for key in ("Total Hours","Completed","Remaining","Progress"):
            col = tk.Frame(stats_bar, bg=BG3)
            col.pack(side="left", expand=True, fill="x", ipadx=4, ipady=4)
            tk.Label(col, text=key, bg=BG3, fg=ORANGE_DIM, font=FONT_MONO_S).pack()
            lbl = tk.Label(col, text="—", bg=BG3, fg=ORANGE, font=FONT_BOLD)
            lbl.pack()
            self.stat_labels[key] = lbl

        # ── Two-pane (fills remaining middle space) ──
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

        res_hdr = tk.Frame(right, bg=BG3)
        res_hdr.pack(fill="x", padx=10, pady=(2,1))
        tk.Label(res_hdr, text="Resources:", bg=BG3, fg=ORANGE_DIM,
                 font=FONT_MONO_S).pack(side="left")
        styled_button(res_hdr, "Open in Browser", self._open_resource, width=16).pack(side="right")
        self.res_lb = tk.Listbox(right, bg=BG2, fg=ORANGE2, font=("Consolas", 8),
                                  selectbackground=ORANGE3, selectforeground=BG,
                                  relief="flat", bd=0, height=3, activestyle="none")
        self.res_lb.pack(fill="x", padx=10, pady=(0,4))
        self.res_lb.bind("<Double-1>", lambda e: self._open_resource())

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
        self._pom_pause()  # stop timer on navigate away
        self.app.show("courses")

    def _open_resource(self):
        sel = self.res_lb.curselection()
        if not sel:
            return
        url = self.res_lb.get(sel[0]).strip()
        if url.startswith("http"):
            webbrowser.open(url)
        else:
            messagebox.showinfo("Resource", url, parent=self)

    # ── Pomodoro ──
    def _pom_tick(self):
        if not self._pom_running:
            return
        self._pom_remaining -= 1
        mins, secs = divmod(self._pom_remaining, 60)
        colour = RED if self._pom_remaining < 60 else (ORANGE if self._pom_remaining < 300 else GREEN)
        self.pom_label.config(text=f"{mins:02d}:{secs:02d}", fg=colour)
        if self._pom_remaining <= 0:
            self._pom_running = False
            self.pom_label.config(text="DONE!", fg=GREEN)
            self.pom_session_label.config(text="✓ session logged")
            append_daily_log(f"[study] Completed {self._pom_seconds//60}min Pomodoro on: {self.program.get('name','')}")
            messagebox.showinfo("Pomodoro Complete",
                f"Session complete!\n{self._pom_seconds//60} minutes of focused study logged.",
                parent=self)
        else:
            self._pom_job = self.after(1000, self._pom_tick)

    def _pom_start(self):
        if self._pom_running:
            return
        self._pom_running = True
        self.pom_session_label.config(text="● studying...")
        self._pom_tick()

    def _pom_pause(self):
        self._pom_running = False
        if self._pom_job:
            self.after_cancel(self._pom_job)
            self._pom_job = None
        self.pom_session_label.config(text="paused")

    def _pom_reset(self):
        self._pom_pause()
        self._pom_remaining = self._pom_seconds
        mins, secs = divmod(self._pom_remaining, 60)
        self.pom_label.config(text=f"{mins:02d}:{secs:02d}", fg=GREEN)
        self.pom_session_label.config(text="")

    def _pom_set(self, minutes):
        self._pom_pause()
        self._pom_seconds   = minutes * 60
        self._pom_remaining = self._pom_seconds
        self.pom_label.config(text=f"{minutes:02d}:00", fg=GREEN)
        self.pom_session_label.config(text="")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ══════════════════════════════════════════════════════════════════════════════

class WinsScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=PANEL)
        self.app = app
        self._build()

    def _build(self):
        section_title(self, "WINS & ACHIEVEMENTS")
        tk.Label(self, text="  Log every win, compliment, and achievement — your performance review fuel.",
                 bg=PANEL, fg=ORANGE_DIM, font=FONT_MONO_S).pack(anchor="w", padx=10, pady=(0,4))

        # Add form
        form_frame = tk.Frame(self, bg=BG3, highlightbackground=ORANGE3, highlightthickness=1)
        form_frame.pack(fill="x", padx=10, pady=4)
        tk.Label(form_frame, text="LOG A WIN", bg=BG3, fg=ORANGE, font=FONT_BOLD).pack(pady=(8,4))
        tk.Frame(form_frame, bg=ORANGE3, height=1).pack(fill="x", padx=6)

        inner = tk.Frame(form_frame, bg=BG3)
        inner.pack(fill="x", padx=14, pady=8)
        inner.columnconfigure(1, weight=1)

        tk.Label(inner, text="Category:", bg=BG3, fg=ORANGE_DIM,
                 font=FONT_MONO_S, width=12, anchor="e").grid(row=0, column=0, pady=4, sticky="e")
        self.cat_var = tk.StringVar(value="Achievement")
        cat_cb = ttk.Combobox(inner, textvariable=self.cat_var, values=WIN_CATS,
                               state="readonly", width=18, font=FONT_MONO_S)
        cat_cb.grid(row=0, column=1, padx=8, sticky="w")

        tk.Label(inner, text="Description:", bg=BG3, fg=ORANGE_DIM,
                 font=FONT_MONO_S, width=12, anchor="ne").grid(row=1, column=0, pady=4, sticky="ne")
        self.desc_box = styled_text(inner, height=3, width=55)
        self.desc_box.grid(row=1, column=1, padx=8, pady=4, sticky="ew")

        tk.Label(inner, text="Impact:", bg=BG3, fg=ORANGE_DIM,
                 font=FONT_MONO_S, width=12, anchor="e").grid(row=2, column=0, pady=4, sticky="e")
        self.impact_var = tk.StringVar()
        styled_entry(inner, textvariable=self.impact_var, width=55).grid(row=2, column=1, padx=8, sticky="ew")
        tk.Label(inner, text="  e.g. 'Reduced MTTR by 30%'", bg=BG3,
                 fg=ORANGE_DIM, font=("Consolas",8)).grid(row=3, column=1, sticky="w", padx=8)

        styled_button(form_frame, "Log This Win ★", self._log_win, width=20,
                      bg=ORANGE3, colour=BG).pack(pady=(0,10))

        # Table
        section_title(self, "WIN LOG")
        cols = ("Date","Category","Description","Impact")
        self.tree = make_treeview(self, cols, heights=10)
        self.tree.column("Date",        width=90,  stretch=False)
        self.tree.column("Category",    width=110, stretch=False)
        self.tree.column("Description", width=280, stretch=True)
        self.tree.column("Impact",      width=200, stretch=True)
        for c in cols: self.tree.heading(c, text=c)
        self._refresh()

        btn_row = tk.Frame(self, bg=PANEL)
        btn_row.pack(pady=4)
        styled_button(btn_row, "Delete Selected", self._delete, width=16).pack(side="left", padx=6)
        styled_button(btn_row, "Export to Markdown", self._export, width=20).pack(side="left", padx=6)

    def _refresh(self):
        for row in self.tree.get_children(): self.tree.delete(row)
        for w in reversed(load_wins()):
            cat = w.get("category","")
            self.tree.insert("", "end", iid=str(w["id"]), values=(
                w.get("date",""), cat,
                w.get("description","")[:60], w.get("impact","")[:50]
            ))

    def _log_win(self):
        desc = self.desc_box.get("1.0","end").strip()
        if not desc:
            messagebox.showwarning("Required", "Description is required.", parent=self)
            return
        wins = load_wins()
        new_id = max((w.get("id",0) for w in wins), default=0) + 1
        wins.append({"id": new_id, "date": today_str(),
                     "category": self.cat_var.get(),
                     "description": desc,
                     "impact": self.impact_var.get().strip()})
        save_wins(wins)
        append_daily_log(f"[win] {self.cat_var.get()}: {desc[:80]}")
        index_memory("win", f"{self.cat_var.get()}: {desc}")
        self.desc_box.delete("1.0","end")
        self.impact_var.set("")
        self._refresh()
        self.app.status("Win logged! ★")

    def _delete(self):
        sel = self.tree.selection()
        if not sel: messagebox.showinfo("Select","Select a win first.", parent=self); return
        if not messagebox.askyesno("Confirm","Delete this win?", parent=self): return
        wid = int(sel[0])
        save_wins([w for w in load_wins() if w["id"] != wid])
        self._refresh()

    def _export(self):
        wins = load_wins()
        if not wins: messagebox.showinfo("Empty","No wins to export.", parent=self); return
        path = filedialog.asksaveasfilename(defaultextension=".md",
               filetypes=[("Markdown","*.md"),("Text","*.txt")],
               initialfile="wins_export.md")
        if not path: return
        lines = ["# Wins & Achievements\n\n"]
        for w in wins:
            lines.append(f"## {w['date']} — {w['category']}\n")
            lines.append(f"{w['description']}\n")
            if w.get("impact"):
                lines.append(f"**Impact:** {w['impact']}\n")
            lines.append("\n")
        Path(path).write_text("".join(lines))
        self.app.status(f"Exported to {Path(path).name}")


# ── Weekly Planner Screen ──────────────────────────────────────────────────────
DAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday"]

class WeeklyPlannerScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=PANEL)
        self.app = app
        # compute this week's Monday
        today = datetime.now()
        self._week_start = today - timedelta(days=today.weekday())
        self._build()

    def _week_key(self):
        return self._week_start.strftime("%Y-%m-%d")

    def _build(self):
        section_title(self, "WEEKLY PLANNER")

        # Navigation
        nav = tk.Frame(self, bg=PANEL)
        nav.pack(fill="x", padx=10, pady=4)
        styled_button(nav, "◀ Prev Week", self._prev_week, width=12).pack(side="left", padx=4)
        styled_button(nav, "This Week",   self._this_week, width=12).pack(side="left", padx=4)
        styled_button(nav, "Next Week ▶", self._next_week, width=12).pack(side="left", padx=4)
        self.week_label = tk.Label(nav, text="", bg=PANEL, fg=ORANGE, font=FONT_BOLD)
        self.week_label.pack(side="left", padx=16)
        styled_button(nav, "Save Plan", self._save_plan, width=12,
                      bg=ORANGE3, colour=BG).pack(side="right", padx=4)

        # Day grid
        grid_frame = tk.Frame(self, bg=PANEL)
        grid_frame.pack(fill="both", expand=True, padx=10, pady=4)
        for i in range(5):
            grid_frame.columnconfigure(i, weight=1)

        self.day_boxes = {}
        for i, day in enumerate(DAYS):
            col = tk.Frame(grid_frame, bg=BG3, highlightbackground=ORANGE3, highlightthickness=1)
            col.grid(row=0, column=i, sticky="nsew", padx=3, pady=2)
            tk.Label(col, text=day, bg=BG3, fg=ORANGE, font=FONT_BOLD).pack(pady=(6,2))
            self.date_labels = getattr(self, "date_labels", {})
            dl = tk.Label(col, text="", bg=BG3, fg=ORANGE_DIM, font=FONT_MONO_S)
            dl.pack()
            self.date_labels[day] = dl
            tk.Frame(col, bg=ORANGE3, height=1).pack(fill="x", padx=4)
            tb = tk.Text(col, bg=BG2, fg=ORANGE, insertbackground=ORANGE,
                         font=FONT_MONO_S, relief="flat", bd=4, wrap="word",
                         selectbackground=ORANGE3, selectforeground=BG)
            tb.pack(fill="both", expand=True, padx=4, pady=4)
            self.day_boxes[day] = tb

        self._load_week()

    def _load_week(self):
        key = self._week_key()
        self.week_label.config(text=f"Week of {key}")
        plans = {p["week"]: p for p in load_weekly()}
        week_data = plans.get(key, {})
        for i, day in enumerate(DAYS):
            day_date = (self._week_start + timedelta(days=i)).strftime("%m/%d")
            self.date_labels[day].config(text=day_date)
            tb = self.day_boxes[day]
            tb.delete("1.0","end")
            tb.insert("1.0", week_data.get(day, ""))
        # Highlight today
        today_name = datetime.now().strftime("%A")
        for day, tb in self.day_boxes.items():
            tb.config(bg=BG2 if day != today_name else "#1a0f00")

    def _save_plan(self):
        key = self._week_key()
        all_plans = {p["week"]: p for p in load_weekly()}
        entry = {"week": key}
        for day in DAYS:
            entry[day] = self.day_boxes[day].get("1.0","end").strip()
        all_plans[key] = entry
        save_weekly(list(all_plans.values()))
        self.app.status(f"Week of {key} saved.")

    def _prev_week(self):
        self._save_plan()
        self._week_start -= timedelta(days=7)
        self._load_week()

    def _next_week(self):
        self._save_plan()
        self._week_start += timedelta(days=7)
        self._load_week()

    def _this_week(self):
        self._save_plan()
        today = datetime.now()
        self._week_start = today - timedelta(days=today.weekday())
        self._load_week()


# ── KPI / Metrics Tracker Screen ───────────────────────────────────────────────
class KPIScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=PANEL)
        self.app = app
        self._build()

    def _build(self):
        section_title(self, "KPI & METRICS TRACKER")

        panes = tk.Frame(self, bg=PANEL)
        panes.pack(fill="both", expand=True, padx=10, pady=4)
        panes.columnconfigure(0, weight=1)
        panes.columnconfigure(1, weight=2)

        # Left — define metrics
        left = tk.Frame(panes, bg=BG3, highlightbackground=ORANGE3, highlightthickness=1)
        left.grid(row=0, column=0, sticky="nsew", padx=(0,4))
        tk.Label(left, text="METRICS", bg=BG3, fg=ORANGE, font=FONT_BOLD).pack(pady=(8,4))
        tk.Frame(left, bg=ORANGE3, height=1).pack(fill="x", padx=6)

        self.metric_lb = tk.Listbox(left, bg=BG2, fg=ORANGE, font=FONT_MONO,
                                     selectbackground=ORANGE3, selectforeground=BG,
                                     relief="flat", bd=0, height=8, activestyle="none")
        self.metric_lb.pack(fill="x", padx=6, pady=4)
        self.metric_lb.bind("<<ListboxSelect>>", self._on_metric_select)

        add_frame = tk.Frame(left, bg=BG3)
        add_frame.pack(fill="x", padx=6, pady=4)
        tk.Label(add_frame, text="Name:", bg=BG3, fg=ORANGE_DIM, font=FONT_MONO_S).pack(anchor="w")
        self.metric_name_var = tk.StringVar()
        styled_entry(add_frame, textvariable=self.metric_name_var, width=20).pack(fill="x")
        tk.Label(add_frame, text="Unit:", bg=BG3, fg=ORANGE_DIM, font=FONT_MONO_S).pack(anchor="w", pady=(4,0))
        self.metric_unit_var = tk.StringVar()
        styled_entry(add_frame, textvariable=self.metric_unit_var, width=14).pack(fill="x")
        tk.Label(add_frame, text="Target:", bg=BG3, fg=ORANGE_DIM, font=FONT_MONO_S).pack(anchor="w", pady=(4,0))
        self.metric_target_var = tk.StringVar()
        styled_entry(add_frame, textvariable=self.metric_target_var, width=10).pack(fill="x")
        btn_r = tk.Frame(left, bg=BG3)
        btn_r.pack(pady=6)
        styled_button(btn_r, "Add Metric", self._add_metric, width=14,
                      bg=ORANGE3, colour=BG).pack(side="left", padx=4)
        styled_button(btn_r, "Delete", self._delete_metric, width=10).pack(side="left", padx=4)

        # Right — log entries
        right = tk.Frame(panes, bg=BG3, highlightbackground=ORANGE3, highlightthickness=1)
        right.grid(row=0, column=1, sticky="nsew")
        tk.Label(right, text="LOG ENTRY", bg=BG3, fg=ORANGE, font=FONT_BOLD).pack(pady=(8,4))
        tk.Frame(right, bg=ORANGE3, height=1).pack(fill="x", padx=6)

        log_form = tk.Frame(right, bg=BG3)
        log_form.pack(fill="x", padx=10, pady=8)
        log_form.columnconfigure(1, weight=1)
        tk.Label(log_form, text="Value:", bg=BG3, fg=ORANGE_DIM,
                 font=FONT_MONO_S, width=8, anchor="e").grid(row=0, column=0, pady=4, sticky="e")
        self.val_var = tk.StringVar()
        styled_entry(log_form, textvariable=self.val_var, width=14).grid(row=0, column=1, padx=8, sticky="w")
        tk.Label(log_form, text="Notes:", bg=BG3, fg=ORANGE_DIM,
                 font=FONT_MONO_S, width=8, anchor="e").grid(row=1, column=0, pady=4, sticky="e")
        self.kpi_note_var = tk.StringVar()
        styled_entry(log_form, textvariable=self.kpi_note_var, width=35).grid(row=1, column=1, padx=8, sticky="ew")
        styled_button(right, "Log Entry", self._log_entry, width=14,
                      bg=ORANGE3, colour=BG).pack(pady=(0,8))

        # History table
        section_title(self, "ENTRY HISTORY")
        cols = ("Date","Metric","Value","Unit","Target","Notes")
        self.tree = make_treeview(self, cols, heights=10)
        self.tree.column("Date",   width=90,  stretch=False)
        self.tree.column("Metric", width=150, stretch=True)
        self.tree.column("Value",  width=70,  stretch=False)
        self.tree.column("Unit",   width=70,  stretch=False)
        self.tree.column("Target", width=70,  stretch=False)
        self.tree.column("Notes",  width=200, stretch=True)
        for c in cols: self.tree.heading(c, text=c)
        styled_button(self, "Delete Selected Entry", self._delete_entry, width=22).pack(pady=4)

        self._refresh_metrics()
        self._refresh_table()

    def _refresh_metrics(self):
        self.metric_lb.delete(0,"end")
        for m in load_kpis().get("metrics",[]):
            self.metric_lb.insert("end", f"  {m['name']}  [{m.get('unit','')}]")

    def _refresh_table(self):
        for row in self.tree.get_children(): self.tree.delete(row)
        data = load_kpis()
        metrics = {m["id"]: m for m in data.get("metrics",[])}
        for e in reversed(data.get("entries",[])):
            m = metrics.get(e.get("metric_id"), {})
            val  = float(e.get("value",0))
            tgt  = float(m.get("target",0)) if m.get("target") else None
            col  = GREEN if (tgt and val >= tgt) else ORANGE
            self.tree.insert("", "end", values=(
                e.get("date",""), m.get("name","?"),
                e.get("value",""), m.get("unit",""),
                m.get("target","—"), e.get("notes","")
            ), tags=("hit" if (tgt and val >= tgt) else "miss",))
        self.tree.tag_configure("hit",  foreground=GREEN)
        self.tree.tag_configure("miss", foreground=ORANGE)

    def _on_metric_select(self, event=None):
        pass  # just highlight

    def _selected_metric(self):
        sel = self.metric_lb.curselection()
        if not sel: return None
        data = load_kpis()
        metrics = data.get("metrics",[])
        if sel[0] < len(metrics):
            return metrics[sel[0]]
        return None

    def _add_metric(self):
        name = self.metric_name_var.get().strip()
        if not name: messagebox.showwarning("Required","Metric name required.", parent=self); return
        data = load_kpis()
        if "metrics" not in data: data["metrics"] = []
        if "entries" not in data: data["entries"] = []
        new_id = max((m.get("id",0) for m in data["metrics"]), default=0) + 1
        data["metrics"].append({
            "id": new_id, "name": name,
            "unit": self.metric_unit_var.get().strip(),
            "target": self.metric_target_var.get().strip()
        })
        save_kpis(data)
        self.metric_name_var.set(""); self.metric_unit_var.set(""); self.metric_target_var.set("")
        self._refresh_metrics()
        self.app.status(f"Metric '{name}' added.")

    def _delete_metric(self):
        m = self._selected_metric()
        if not m: messagebox.showinfo("Select","Select a metric first.", parent=self); return
        if not messagebox.askyesno("Confirm", f"Delete '{m['name']}'?", parent=self): return
        data = load_kpis()
        data["metrics"] = [x for x in data.get("metrics",[]) if x["id"] != m["id"]]
        save_kpis(data); self._refresh_metrics(); self._refresh_table()

    def _log_entry(self):
        m = self._selected_metric()
        if not m: messagebox.showinfo("Select","Select a metric first.", parent=self); return
        val = self.val_var.get().strip()
        if not val: messagebox.showwarning("Required","Value required.", parent=self); return
        data = load_kpis()
        if "entries" not in data: data["entries"] = []
        data["entries"].append({
            "date": today_str(), "metric_id": m["id"],
            "value": val, "notes": self.kpi_note_var.get().strip()
        })
        save_kpis(data)
        index_memory("kpi", f"{m['name']}: {val} {m.get('unit','')} — {self.kpi_note_var.get()}")
        self.val_var.set(""); self.kpi_note_var.set("")
        self._refresh_table()
        self.app.status(f"{m['name']}: {val} logged.")

    def _delete_entry(self):
        sel = self.tree.selection()
        if not sel: return
        vals = self.tree.item(sel[0],"values")
        data = load_kpis()
        metrics = {m["name"]: m["id"] for m in data.get("metrics",[])}
        mid = metrics.get(vals[1])
        data["entries"] = [e for e in data.get("entries",[])
                           if not (e["date"]==vals[0] and e["metric_id"]==mid and str(e["value"])==vals[2])]
        save_kpis(data); self._refresh_table()


# ── Incident Timeline Screen ───────────────────────────────────────────────────
SEV_COLOURS = {"P1":RED,"P2":ORANGE3,"P3":ORANGE,"P4":"#ffcc00","P5":GREY}
INC_STATUSES = ["open","investigating","contained","resolved","closed"]

class IncidentModal(tk.Toplevel):
    def __init__(self, parent, app, incident=None, on_save=None):
        super().__init__(parent)
        self.app = app; self.incident = incident; self.on_save = on_save
        self.title("Edit Incident" if incident else "Log Incident")
        self.configure(bg=PANEL)
        self.geometry("580x420")
        self.resizable(False, False)
        self.grab_set()
        self._build()

    def _build(self):
        tk.Label(self, text=f"◆ {'EDIT' if self.incident else 'LOG'} INCIDENT",
                 bg=PANEL, fg=ORANGE, font=FONT_BOLD_L).pack(pady=(10,4), padx=16, anchor="w")
        tk.Frame(self, bg=ORANGE3, height=1).pack(fill="x", padx=16)
        form = tk.Frame(self, bg=PANEL)
        form.pack(fill="x", padx=20, pady=8)
        form.columnconfigure(1, weight=1)
        inc = self.incident or {}

        fields = [
            ("Title:",     "title",    tk.StringVar(value=inc.get("title",""))),
            ("Date/Time:", "datetime", tk.StringVar(value=inc.get("datetime", now_str()))),
        ]
        self.vars = {}
        for i,(lbl,key,var) in enumerate(fields):
            tk.Label(form, text=lbl, bg=PANEL, fg=ORANGE_DIM,
                     font=FONT_MONO_S, width=12, anchor="e").grid(row=i, column=0, pady=4, sticky="e")
            styled_entry(form, textvariable=var, width=40).grid(row=i, column=1, padx=8, sticky="ew")
            self.vars[key] = var

        # Severity
        tk.Label(form, text="Severity:", bg=PANEL, fg=ORANGE_DIM,
                 font=FONT_MONO_S, width=12, anchor="e").grid(row=2, column=0, pady=4, sticky="e")
        self.sev_var = tk.StringVar(value=inc.get("severity","P3"))
        sev_frame = tk.Frame(form, bg=PANEL)
        sev_frame.grid(row=2, column=1, padx=8, sticky="w")
        for sev, col in SEV_COLOURS.items():
            tk.Radiobutton(sev_frame, text=sev, variable=self.sev_var, value=sev,
                           bg=PANEL, fg=col, selectcolor=BG3,
                           activebackground=PANEL, activeforeground=col,
                           font=FONT_BOLD).pack(side="left", padx=6)

        # Status
        tk.Label(form, text="Status:", bg=PANEL, fg=ORANGE_DIM,
                 font=FONT_MONO_S, width=12, anchor="e").grid(row=3, column=0, pady=4, sticky="e")
        self.status_var = tk.StringVar(value=inc.get("status","open"))
        status_cb = ttk.Combobox(form, textvariable=self.status_var, values=INC_STATUSES,
                                  state="readonly", width=16, font=FONT_MONO_S)
        status_cb.grid(row=3, column=1, padx=8, sticky="w")

        # Description
        tk.Label(form, text="Description:", bg=PANEL, fg=ORANGE_DIM,
                 font=FONT_MONO_S, width=12, anchor="ne").grid(row=4, column=0, pady=4, sticky="ne")
        self.desc_box = styled_text(form, height=3, width=40)
        self.desc_box.grid(row=4, column=1, padx=8, sticky="ew")
        if inc.get("description"): self.desc_box.insert("1.0", inc["description"])

        # Resolution
        tk.Label(form, text="Resolution:", bg=PANEL, fg=ORANGE_DIM,
                 font=FONT_MONO_S, width=12, anchor="ne").grid(row=5, column=0, pady=4, sticky="ne")
        self.res_box = styled_text(form, height=2, width=40)
        self.res_box.grid(row=5, column=1, padx=8, sticky="ew")
        if inc.get("resolution"): self.res_box.insert("1.0", inc["resolution"])

        btn_row = tk.Frame(self, bg=PANEL)
        btn_row.pack(pady=8)
        styled_button(btn_row, "Save", self._save, width=12,
                      bg=ORANGE3, colour=BG).pack(side="left", padx=8)
        styled_button(btn_row, "Cancel", self.destroy, width=12).pack(side="left", padx=8)

    def _save(self):
        title = self.vars["title"].get().strip()
        if not title:
            messagebox.showwarning("Required","Title is required.", parent=self); return
        result = {
            "title":       title,
            "datetime":    self.vars["datetime"].get().strip(),
            "severity":    self.sev_var.get(),
            "status":      self.status_var.get(),
            "description": self.desc_box.get("1.0","end").strip(),
            "resolution":  self.res_box.get("1.0","end").strip(),
        }
        if self.on_save: self.on_save(result)
        self.destroy()


class IncidentTimelineScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=PANEL)
        self.app = app
        self._build()

    def _build(self):
        section_title(self, "INCIDENT TIMELINE")
        tk.Label(self, text="  Track security incidents, outages, and critical events.",
                 bg=PANEL, fg=ORANGE_DIM, font=FONT_MONO_S).pack(anchor="w", padx=10, pady=(0,4))

        bar = tk.Frame(self, bg=PANEL)
        bar.pack(fill="x", padx=10, pady=4)
        styled_button(bar, "+ Log Incident", self._add, width=16,
                      bg=ORANGE3, colour=BG).pack(side="left", padx=4)
        styled_button(bar, "✎ Edit",   self._edit,   width=10).pack(side="left", padx=4)
        styled_button(bar, "✕ Delete", self._delete, width=10).pack(side="left", padx=4)
        styled_button(bar, "↺ Refresh",self._refresh, width=10).pack(side="right", padx=4)

        # Filter by severity
        filt = tk.Frame(self, bg=PANEL)
        filt.pack(fill="x", padx=10, pady=(0,4))
        tk.Label(filt, text="Severity:", bg=PANEL, fg=ORANGE_DIM, font=FONT_MONO_S).pack(side="left")
        self.sev_filter = tk.StringVar(value="all")
        for val, lbl in [("all","All"),("P1","P1"),("P2","P2"),("P3","P3"),("P4","P4"),("P5","P5")]:
            tk.Radiobutton(filt, text=lbl, variable=self.sev_filter, value=val,
                           command=self._refresh, bg=PANEL,
                           fg=SEV_COLOURS.get(val, ORANGE),
                           selectcolor=BG3, activebackground=PANEL,
                           activeforeground=SEV_COLOURS.get(val, ORANGE),
                           font=FONT_MONO_S).pack(side="left", padx=6)

        cols = ("Date/Time","Severity","Title","Status","Description","Resolution")
        self.tree = make_treeview(self, cols, heights=14)
        self.tree.column("Date/Time",   width=130, stretch=False)
        self.tree.column("Severity",    width=60,  stretch=False)
        self.tree.column("Title",       width=200, stretch=True)
        self.tree.column("Status",      width=100, stretch=False)
        self.tree.column("Description", width=200, stretch=True)
        self.tree.column("Resolution",  width=160, stretch=True)
        for c in cols: self.tree.heading(c, text=c)
        self.tree.bind("<Double-1>", lambda e: self._edit())

        # Stats
        self.stats_label = tk.Label(self, text="", bg=PANEL, fg=ORANGE_DIM, font=FONT_MONO_S)
        self.stats_label.pack(padx=10, pady=4, anchor="w")

        self._refresh()

    def _refresh(self):
        for row in self.tree.get_children(): self.tree.delete(row)
        incs = sorted(load_incidents(), key=lambda x: x.get("datetime",""), reverse=True)
        sf = self.sev_filter.get()
        if sf != "all": incs = [i for i in incs if i.get("severity") == sf]
        for inc in incs:
            sev = inc.get("severity","P3")
            self.tree.insert("", "end", iid=str(inc["id"]), values=(
                inc.get("datetime","")[:16],
                sev,
                inc.get("title","")[:45],
                inc.get("status","open"),
                inc.get("description","")[:50],
                inc.get("resolution","")[:40],
            ), tags=(sev,))
        for sev, col in SEV_COLOURS.items():
            self.tree.tag_configure(sev, foreground=col)
        all_incs = load_incidents()
        open_n = sum(1 for i in all_incs if i.get("status") not in ("resolved","closed"))
        self.stats_label.config(
            text=f"  Total: {len(all_incs)}   Open/Active: {open_n}   "
                 f"P1: {sum(1 for i in all_incs if i.get('severity')=='P1')}   "
                 f"P2: {sum(1 for i in all_incs if i.get('severity')=='P2')}")

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel: messagebox.showinfo("Select","Select an incident first.", parent=self); return None
        return int(sel[0])

    def _add(self):
        def on_save(result):
            incs = load_incidents()
            new_id = max((i.get("id",0) for i in incs), default=0) + 1
            incs.append({"id": new_id, **result})
            save_incidents(incs)
            index_memory("incident", f"{result['severity']} {result['title']}: {result['description'][:80]}")
            append_daily_log(f"[incident] {result['severity']} — {result['title']}")
            self._refresh()
            self.app.status(f"Incident logged: {result['title']}")
        IncidentModal(self, self.app, on_save=on_save)

    def _edit(self):
        iid = self._selected_id()
        if iid is None: return
        inc = next((i for i in load_incidents() if i["id"] == iid), None)
        if not inc: return
        def on_save(result):
            incs = load_incidents()
            for i in incs:
                if i["id"] == iid: i.update(result)
            save_incidents(incs)
            self._refresh()
            self.app.status(f"Incident #{iid} updated.")
        IncidentModal(self, self.app, incident=inc, on_save=on_save)

    def _delete(self):
        iid = self._selected_id()
        if iid is None: return
        if not messagebox.askyesno("Confirm","Delete this incident?", parent=self): return
        save_incidents([i for i in load_incidents() if i["id"] != iid])
        self._refresh()
        self.app.status(f"Incident #{iid} deleted.")

# ══════════════════════════════════════════════════════════════════════════════
# DEVELOPMENT PLANS — Loading screen, list, detail, import modal
# ══════════════════════════════════════════════════════════════════════════════

DEV_STATUS_COLOURS = {
    "not_started": "#555555",
    "in_progress": "#ff8c00",
    "complete":    "#00ff88",
}

class DevLoadingScreen(tk.Toplevel):
    """3-second ladder-fill loading animation shown before the dev plans screen."""
    def __init__(self, parent_win, callback):
        super().__init__(parent_win)
        self.callback = callback
        self.configure(bg=BG)
        self.overrideredirect(True)
        # Centre over parent
        pw = parent_win.winfo_width()  or 1280
        ph = parent_win.winfo_height() or 800
        px = parent_win.winfo_rootx()
        py = parent_win.winfo_rooty()
        w, h = 400, 440
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.lift()
        self.grab_set()
        self._build()

    def _build(self):
        tk.Label(self, text="COMMAND CENTER", bg=BG, fg=ORANGE,
                 font=("Consolas", 18, "bold")).pack(pady=(28, 4))
        tk.Label(self, text="DEVELOPMENT PLANS", bg=BG, fg=ORANGE_DIM,
                 font=("Consolas", 11)).pack(pady=(0, 16))

        self._canvas = tk.Canvas(self, bg=BG, width=200, height=240,
                                  highlightthickness=0)
        self._canvas.pack()

        self._status = tk.Label(self, text="Initialising...", bg=BG,
                                 fg=ORANGE_DIM, font=FONT_MONO_S)
        self._status.pack(pady=14)

        self._draw_rails()
        self.after(200, lambda: self._animate(0))

    # ── rails (static) ──
    def _draw_rails(self):
        c = self._canvas
        lx, rx = 55, 145
        self._top_y, self._bot_y = 15, 225
        self._lx, self._rx = lx, rx
        c.create_line(lx, self._top_y, lx, self._bot_y, fill=GREY, width=5)
        c.create_line(rx, self._top_y, rx, self._bot_y, fill=GREY, width=5)
        # pre-draw dim rungs
        n = 10
        gap = (self._bot_y - self._top_y) / (n + 1)
        self._rung_ids = []
        for i in range(n):
            y = int(self._bot_y - gap * (i + 1))
            rid = c.create_line(lx, y, rx, y, fill=GREY, width=4, capstyle="round")
            self._rung_ids.append(rid)

    def _animate(self, step):
        n = len(self._rung_ids)
        if step >= n:
            self._status.config(text="Ready.", fg=GREEN)
            self.after(350, self._done)
            return
        rid = self._rung_ids[step]
        t = (step + 1) / n          # 0..1
        # orange → bright white-orange
        r = 255
        g = int(140 + t * 115)
        b = int(t * 200)
        colour = f"#{r:02x}{min(255,g):02x}{min(255,b):02x}"
        self._canvas.itemconfig(rid, fill=colour, width=5)
        # also brighten the rail section
        rail_col = f"#{r:02x}{min(255, int(70 + t*80)):02x}00"
        # status dots
        dots = "." * ((step % 3) + 1)
        msgs = ["Loading plan data", "Building milestones", "Mapping career path",
                "Linking wins & KPIs", "Preparing timeline"]
        self._status.config(text=f"{msgs[step % len(msgs)]}{dots}")
        self.after(280, lambda: self._animate(step + 1))

    def _done(self):
        self.grab_release()
        self.destroy()
        self.callback()


# ── Paste-in JSON import modal (shared by dev plans AND courses) ──────────────
class PasteJSONModal(tk.Toplevel):
    """Generic modal for pasting JSON and importing it."""
    def __init__(self, parent, app, title="Paste JSON", hint="", on_save=None):
        super().__init__(parent)
        self.app = app
        self.on_save = on_save
        self.configure(bg=BG)
        self.title(title)
        self.geometry("700x520")
        self.resizable(True, True)
        self.grab_set()
        self._build(title, hint)

    def _build(self, title, hint):
        tk.Label(self, text=title, bg=BG, fg=ORANGE,
                 font=FONT_BOLD_L).pack(pady=(14, 4))
        if hint:
            tk.Label(self, text=hint, bg=BG, fg=ORANGE_DIM,
                     font=FONT_MONO_S, wraplength=650, justify="left").pack(
                     padx=14, pady=(0, 8), anchor="w")
        tk.Frame(self, bg=ORANGE3, height=1).pack(fill="x", padx=10)

        self.txt = scrolledtext.ScrolledText(
            self, bg=BG3, fg=GREEN, insertbackground=GREEN,
            font=("Consolas", 10), relief="flat", bd=6,
            selectbackground=ORANGE3, selectforeground=BG, wrap="none")
        self.txt.pack(fill="both", expand=True, padx=10, pady=8)
        self.txt.insert("1.0", "")

        self._err = tk.Label(self, text="", bg=BG, fg=RED, font=FONT_MONO_S,
                              wraplength=650)
        self._err.pack(padx=10, pady=2)

        row = tk.Frame(self, bg=BG)
        row.pack(pady=(0, 12))
        styled_button(row, "✓ Validate & Import", self._do_import, width=22,
                      bg=ORANGE3, colour=BG).pack(side="left", padx=6)
        styled_button(row, "Cancel", self.destroy, width=12).pack(side="left", padx=6)

    def _do_import(self):
        raw = self.txt.get("1.0", "end").strip()
        if not raw:
            self._err.config(text="Nothing pasted.")
            return
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            self._err.config(text=f"JSON parse error: {e}")
            return
        if self.on_save:
            result = self.on_save(data)
            if result is True:
                self.destroy()
            elif isinstance(result, str):
                self._err.config(text=result)


# ── Dev Plan List ─────────────────────────────────────────────────────────────
class DevPlanListScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        # Show loading animation then build
        DevLoadingScreen(app, callback=self._after_load)

    def _after_load(self):
        self.configure(bg=PANEL)
        self._build()

    def _build(self):
        section_title(self, "DEVELOPMENT PLANS")
        tk.Label(self, text="  Your career roadmap — climb the ladder, log every win.",
                 bg=PANEL, fg=ORANGE_DIM, font=FONT_MONO_S).pack(anchor="w", padx=10, pady=(0, 4))

        bar = tk.Frame(self, bg=PANEL)
        bar.pack(fill="x", padx=10, pady=4)
        styled_button(bar, "+ New Plan",   self._new_plan,   width=13, bg=ORANGE3, colour=BG).pack(side="left", padx=4)
        styled_button(bar, "Paste JSON",   self._paste_plan, width=13).pack(side="left", padx=4)
        styled_button(bar, "Open",         self._open_plan,  width=10).pack(side="left", padx=4)
        styled_button(bar, "Edit JSON",    self._edit_plan,  width=10).pack(side="left", padx=4)
        styled_button(bar, "Delete",       self._delete_plan,width=10).pack(side="left", padx=4)
        styled_button(bar, "Refresh",      self._refresh,    width=10).pack(side="right", padx=4)

        cols = ("Name", "Level", "Progress", "Milestones", "Target Date", "Status")
        self.tree = make_treeview(self, cols, heights=12)
        self.tree.column("Name",        width=240, stretch=True)
        self.tree.column("Level",       width=90,  stretch=False)
        self.tree.column("Progress",    width=80,  stretch=False)
        self.tree.column("Milestones",  width=100, stretch=False)
        self.tree.column("Target Date", width=100, stretch=False)
        self.tree.column("Status",      width=80,  stretch=False)
        for c in cols:
            self.tree.heading(c, text=c)
        self.tree.bind("<Double-1>", lambda e: self._open_plan())
        self._refresh()

        self._stats = tk.Label(self, text="", bg=PANEL, fg=ORANGE_DIM, font=FONT_MONO_S)
        self._stats.pack(padx=10, pady=4, anchor="w")

    def _refresh(self):
        if not hasattr(self, "tree"):
            return
        for row in self.tree.get_children():
            self.tree.delete(row)
        plans = load_dev_plans()
        for p in plans:
            ms = p.get("milestones", [])
            total = len(ms)
            done  = sum(1 for m in ms if m.get("status") == "complete")
            pct   = int(done / total * 100) if total else 0
            lvl   = f"{p.get('current_level','?')} → {p.get('target_level','?')}"
            tag   = p.get("status", "active")
            self.tree.insert("", "end", iid=str(p["id"]), values=(
                p.get("name", ""),
                lvl,
                f"{pct}%",
                f"{done}/{total}",
                p.get("target_date", "—")[:10],
                p.get("status", "active").upper(),
            ), tags=(tag,))
        self.tree.tag_configure("active",    foreground=ORANGE)
        self.tree.tag_configure("completed", foreground=GREEN)
        self.tree.tag_configure("paused",    foreground=GREY)
        total = len(plans)
        active = sum(1 for p in plans if p.get("status") == "active")
        self._stats.config(text=f"  Plans: {total}   Active: {active}")

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Select a plan first.", parent=self)
            return None
        return int(sel[0])

    def _new_plan(self):
        hint = (
            'Ask Claude to create a development plan and paste the JSON here.\n'
            'Minimum required fields: "name", "current_level", "target_level", "milestones" (array).\n'
            'Each milestone needs: "id", "title", "phase", "description", "status" ("not_started"|"in_progress"|"complete").'
        )
        def on_save(data):
            if not isinstance(data, dict):
                return "Must be a JSON object {…}"
            if "name" not in data:
                return "Missing required field: name"
            if "milestones" not in data or not isinstance(data["milestones"], list):
                return "Missing or invalid 'milestones' array"
            plans = load_dev_plans()
            data["id"] = max((p["id"] for p in plans), default=0) + 1
            data.setdefault("status", "active")
            data.setdefault("created_date", today_str())
            plans.append(data)
            save_dev_plans(plans)
            self._refresh()
            self.app.status(f"Plan '{data['name']}' imported.")
            return True
        PasteJSONModal(self, self.app, title="Paste New Development Plan", hint=hint, on_save=on_save)

    def _paste_plan(self):
        self._new_plan()

    def _open_plan(self):
        pid = self._selected_id()
        if pid is None:
            return
        self.app.show_dev_plan(pid)

    def _edit_plan(self):
        pid = self._selected_id()
        if pid is None:
            return
        plans = load_dev_plans()
        plan  = next((p for p in plans if p["id"] == pid), None)
        if not plan:
            return
        hint = "Edit the JSON below, then click Validate & Import to save."
        def on_save(data):
            if not isinstance(data, dict):
                return "Must be a JSON object {…}"
            data["id"] = pid
            new_plans = [data if p["id"] == pid else p for p in plans]
            save_dev_plans(new_plans)
            self._refresh()
            self.app.status("Plan updated.")
            return True
        modal = PasteJSONModal(self, self.app, title="Edit Plan JSON", hint=hint, on_save=on_save)
        modal.txt.insert("1.0", json.dumps(plan, indent=2))

    def _delete_plan(self):
        pid = self._selected_id()
        if pid is None:
            return
        if not messagebox.askyesno("Confirm", "Delete this plan?", parent=self):
            return
        save_dev_plans([p for p in load_dev_plans() if p["id"] != pid])
        self._refresh()
        self.app.status("Plan deleted.")


# ── Dev Plan Detail (milestones) ──────────────────────────────────────────────
class DevPlanDetailScreen(tk.Frame):
    def __init__(self, parent, app, plan_id):
        super().__init__(parent, bg=PANEL)
        self.app      = app
        self.plan_id  = plan_id
        self._cur_mid = None
        self._load_plan()
        self._build()

    def _load_plan(self):
        plans = load_dev_plans()
        self.plan = next((p for p in plans if p["id"] == self.plan_id), {})

    # ── layout ──
    def _build(self):
        p = self.plan
        ms = p.get("milestones", [])

        # ── Header ──
        hdr = tk.Frame(self, bg=BG3, highlightbackground=ORANGE3, highlightthickness=1)
        hdr.pack(fill="x", padx=10, pady=(6, 2))
        styled_button(hdr, "◀ Back", lambda: self.app.show("develop"),
                      width=9).pack(side="left", padx=8, pady=6)
        tk.Label(hdr, text=p.get("name", "Development Plan"), bg=BG3,
                 fg=ORANGE, font=FONT_BOLD_L).pack(side="left", padx=10)
        lvl_txt = f"  {p.get('current_level','?')} ──▶ {p.get('target_level','?')}  "
        tk.Label(hdr, text=lvl_txt, bg=ORANGE3, fg=BG,
                 font=FONT_BOLD).pack(side="left", padx=6, pady=8)
        tk.Label(hdr, text=f"Target: {p.get('target_date','—')[:10]}",
                 bg=BG3, fg=ORANGE_DIM, font=FONT_MONO_S).pack(side="right", padx=12)

        # ── Progress bar ──
        done = sum(1 for m in ms if m.get("status") == "complete")
        total = len(ms) or 1
        pct   = int(done / total * 100)
        pf = tk.Frame(self, bg=BG3, highlightbackground=ORANGE3, highlightthickness=1)
        pf.pack(fill="x", padx=10, pady=(0, 4))
        self._prog_canvas = tk.Canvas(pf, bg=BG3, height=28, highlightthickness=0)
        self._prog_canvas.pack(fill="x", padx=10, pady=5)
        self._prog_canvas.bind("<Configure>", lambda e: self._draw_progress())

        # ── Stats bar (bottom-anchored) ──
        stats_bar = tk.Frame(self, bg=BG3, highlightbackground=ORANGE3, highlightthickness=1)
        stats_bar.pack(side="bottom", fill="x", padx=10, pady=(0, 6))
        self._stat_labels = {}
        in_prog = sum(1 for m in ms if m.get("status") == "in_progress")
        est_rem = sum(m.get("estimated_weeks", 0) for m in ms if m.get("status") != "complete")
        for key, val in [("Milestones", str(total)),
                         ("Complete",   str(done)),
                         ("In Progress",str(in_prog)),
                         ("Remaining",  str(total - done)),
                         ("Est Weeks Left", str(est_rem))]:
            col = tk.Frame(stats_bar, bg=BG3)
            col.pack(side="left", expand=True, fill="x", ipadx=4, ipady=4)
            tk.Label(col, text=key,  bg=BG3, fg=ORANGE_DIM, font=FONT_MONO_S).pack()
            lbl = tk.Label(col, text=val, bg=BG3, fg=ORANGE, font=FONT_BOLD)
            lbl.pack()
            self._stat_labels[key] = lbl

        # ── Two-pane ──
        panes = tk.Frame(self, bg=PANEL)
        panes.pack(fill="both", expand=True, padx=10, pady=4)
        panes.columnconfigure(0, weight=1)
        panes.columnconfigure(1, weight=2)
        panes.rowconfigure(0, weight=1)

        # Left: milestone list
        left = tk.Frame(panes, bg=BG3, highlightbackground=ORANGE3, highlightthickness=1)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        tk.Label(left, text="MILESTONES", bg=BG3, fg=ORANGE, font=FONT_BOLD).pack(pady=(6, 2))
        tk.Frame(left, bg=ORANGE3, height=1).pack(fill="x", padx=6)

        # Phase filter
        phases = sorted({m.get("phase","") for m in ms})
        fbar = tk.Frame(left, bg=BG3)
        fbar.pack(fill="x", padx=6, pady=(4, 2))
        tk.Label(fbar, text="Filter:", bg=BG3, fg=ORANGE_DIM, font=FONT_MONO_S).pack(side="left")
        self._phase_var = tk.StringVar(value="All")
        phase_cb = ttk.Combobox(fbar, textvariable=self._phase_var,
                                 values=["All"] + phases,
                                 state="readonly", width=20, font=FONT_MONO_S)
        phase_cb.pack(side="left", padx=4)
        phase_cb.bind("<<ComboboxSelected>>", lambda e: self._refresh_milestones())

        m_cols = ("#", "Title", "Status")
        self.m_tree = make_treeview(left, m_cols, heights=16)
        self.m_tree.column("#",      width=28,  stretch=False)
        self.m_tree.column("Title",  width=180, stretch=True)
        self.m_tree.column("Status", width=70,  stretch=False)
        for c in m_cols:
            self.m_tree.heading(c, text=c)
        self.m_tree.bind("<<TreeviewSelect>>", self._on_milestone_select)

        # Right: detail panel
        right = tk.Frame(panes, bg=BG3, highlightbackground=ORANGE3, highlightthickness=1)
        right.grid(row=0, column=1, sticky="nsew")

        self._detail_title = tk.Label(right, text="Select a milestone", bg=BG3,
                                       fg=ORANGE, font=FONT_BOLD_L,
                                       wraplength=380, justify="left", anchor="w")
        self._detail_title.pack(fill="x", padx=10, pady=(8, 2))

        self._level_badge = tk.Label(right, text="", bg=BG3, fg=ORANGE_DIM, font=FONT_MONO_S)
        self._level_badge.pack(anchor="w", padx=10, pady=(0, 4))
        tk.Frame(right, bg=ORANGE3, height=1).pack(fill="x", padx=8)

        tk.Label(right, text="Description:", bg=BG3, fg=ORANGE_DIM,
                 font=FONT_MONO_S).pack(anchor="w", padx=10, pady=(6, 1))
        self._detail_desc = scrolledtext.ScrolledText(right, bg=BG2, fg=ORANGE,
                                                       font=FONT_MONO_S, relief="flat",
                                                       bd=0, height=5, wrap="word",
                                                       state="disabled")
        self._detail_desc.pack(fill="x", padx=10, pady=(0, 4))

        # Skills
        skills_hdr = tk.Frame(right, bg=BG3)
        skills_hdr.pack(fill="x", padx=10, pady=(2, 1))
        tk.Label(skills_hdr, text="Skills:", bg=BG3, fg=ORANGE_DIM,
                 font=FONT_MONO_S).pack(side="left")
        self._skills_lbl = tk.Label(right, text="", bg=BG2, fg=ORANGE2,
                                     font=("Consolas", 9), wraplength=380,
                                     justify="left", anchor="w")
        self._skills_lbl.pack(fill="x", padx=10, pady=(0, 4))

        # Resources
        res_hdr = tk.Frame(right, bg=BG3)
        res_hdr.pack(fill="x", padx=10, pady=(2, 1))
        tk.Label(res_hdr, text="Resources:", bg=BG3, fg=ORANGE_DIM,
                 font=FONT_MONO_S).pack(side="left")
        styled_button(res_hdr, "Open in Browser", self._open_resource, width=16).pack(side="right")
        self._res_lb = tk.Listbox(right, bg=BG2, fg=ORANGE2, font=("Consolas", 8),
                                   selectbackground=ORANGE3, selectforeground=BG,
                                   relief="flat", bd=0, height=3, activestyle="none")
        self._res_lb.pack(fill="x", padx=10, pady=(0, 4))
        self._res_lb.bind("<Double-1>", lambda e: self._open_resource())

        tk.Label(right, text="Notes:", bg=BG3, fg=ORANGE_DIM,
                 font=FONT_MONO_S).pack(anchor="w", padx=10, pady=(2, 1))
        self._notes_box = styled_text(right, height=3, width=50)
        self._notes_box.pack(fill="x", padx=10, pady=(0, 4))
        self._notes_box.bind("<FocusOut>", lambda e: self._save_notes())

        btn_row = tk.Frame(right, bg=BG3)
        btn_row.pack(padx=10, pady=4, anchor="w")
        styled_button(btn_row, "✓ Complete",    self._mark_complete,     width=13,
                      bg=ORANGE3, colour=BG).pack(side="left", padx=(0, 4))
        styled_button(btn_row, "▶ In Progress", self._mark_in_progress,  width=14).pack(side="left", padx=4)
        styled_button(btn_row, "— Reset",       self._mark_not_started,  width=9).pack(side="left", padx=4)

        self._refresh_milestones()

    def _draw_progress(self):
        c = self._prog_canvas
        c.delete("all")
        ms    = self.plan.get("milestones", [])
        done  = sum(1 for m in ms if m.get("status") == "complete")
        total = len(ms) or 1
        pct   = done / total
        W     = c.winfo_width() or 400
        H     = 28
        c.create_rectangle(0, 0, W, H, fill=BG2, outline="")
        fill_w = int(W * pct)
        if fill_w > 0:
            c.create_rectangle(0, 0, fill_w, H, fill=ORANGE3, outline="")
        c.create_text(W // 2, H // 2, text=f"{int(pct*100)}%  ({done}/{total} milestones)",
                      fill=WHITE, font=FONT_BOLD)

    def _refresh_milestones(self):
        if not hasattr(self, "m_tree"):
            return
        for row in self.m_tree.get_children():
            self.m_tree.delete(row)
        phase_filter = self._phase_var.get() if hasattr(self, "_phase_var") else "All"
        ms = self.plan.get("milestones", [])
        for m in ms:
            if phase_filter != "All" and m.get("phase", "") != phase_filter:
                continue
            st  = m.get("status", "not_started")
            tag = st
            self.m_tree.insert("", "end", iid=str(m["id"]), values=(
                m["id"], m.get("title","")[:40], st.replace("_"," ").upper()
            ), tags=(tag,))
        self.m_tree.tag_configure("not_started", foreground=GREY)
        self.m_tree.tag_configure("in_progress", foreground=ORANGE)
        self.m_tree.tag_configure("complete",    foreground=GREEN)
        self._draw_progress()

    def _on_milestone_select(self, _=None):
        sel = self.m_tree.selection()
        if not sel:
            return
        mid = int(sel[0])
        self._cur_mid = mid
        m = next((x for x in self.plan.get("milestones",[]) if x["id"] == mid), None)
        if not m:
            return
        self._detail_title.config(text=m.get("title",""))
        self._level_badge.config(
            text=f"{m.get('phase','')}   ▪   {m.get('level','')}   ▪   Est {m.get('estimated_weeks',0)} weeks")
        # Description
        self._detail_desc.config(state="normal")
        self._detail_desc.delete("1.0","end")
        self._detail_desc.insert("1.0", m.get("description",""))
        self._detail_desc.config(state="disabled")
        # Skills
        skills = m.get("skills", [])
        self._skills_lbl.config(text="  •  ".join(skills) if skills else "—")
        # Resources
        self._res_lb.delete(0,"end")
        for r in m.get("resources", []):
            self._res_lb.insert("end", r)
        # Notes
        self._notes_box.delete("1.0","end")
        self._notes_box.insert("1.0", m.get("notes",""))

    def _cur_milestone(self):
        if self._cur_mid is None:
            messagebox.showinfo("Select", "Select a milestone first.", parent=self)
            return None
        return next((m for m in self.plan.get("milestones",[]) if m["id"]==self._cur_mid), None)

    def _set_status(self, new_status):
        m = self._cur_milestone()
        if not m:
            return
        m["status"] = new_status
        if new_status == "complete":
            m["completed_date"] = today_str()
        self._persist()
        self._refresh_milestones()
        self.app.status(f"'{m['title'][:40]}' → {new_status.replace('_',' ')}")

    def _mark_complete(self):
        m = self._cur_milestone()
        if not m:
            return
        m["status"] = "complete"
        m["completed_date"] = today_str()
        self._persist()
        self._refresh_milestones()
        title = m.get("title","")
        self.app.status(f"Milestone complete: {title[:40]}")
        # ── Log a Win ──
        if messagebox.askyesno("Log a Win?",
                f"Log completing:\n'{title}'\nas a Win in Wins & Achievements?",
                parent=self):
            wins = load_wins()
            new_id = max((w.get("id",0) for w in wins), default=0) + 1
            wins.append({
                "id":          new_id,
                "date":        today_str(),
                "category":    "Professional Development",
                "description": f"Completed SOC development milestone: {title}",
                "impact":      f"Progress towards {self.plan.get('target_level','L3')} SOC Analyst role — "
                               f"{m.get('level','')} track"
            })
            save_wins(wins)
            append_daily_log(f"[dev milestone] {title}")
            index_memory("dev_milestone", title)
            # ── Auto-log KPI if a SOC/Development metric exists ──
            kpi_data = load_kpis()
            for metric in kpi_data.get("metrics", []):
                mname = metric.get("name","").lower()
                if "soc" in mname or "development" in mname or "career" in mname:
                    ms    = self.plan.get("milestones",[])
                    done  = sum(1 for x in ms if x.get("status")=="complete")
                    total = len(ms) or 1
                    entry = {
                        "id":        max((e.get("id",0) for e in kpi_data.get("entries",[])), default=0)+1,
                        "metric_id": metric["id"],
                        "date":      today_str(),
                        "value":     round(done/total*100,1),
                        "note":      f"Milestone complete: {title[:50]}"
                    }
                    kpi_data["entries"].append(entry)
                    save_kpis(kpi_data)
                    break
            self.app.status(f"Win logged + milestone complete!")

    def _mark_in_progress(self):
        self._set_status("in_progress")

    def _mark_not_started(self):
        m = self._cur_milestone()
        if not m:
            return
        m["status"] = "not_started"
        m["completed_date"] = None
        self._persist()
        self._refresh_milestones()
        self.app.status(f"Milestone reset.")

    def _save_notes(self):
        m = self._cur_milestone()
        if not m:
            return
        m["notes"] = self._notes_box.get("1.0","end").strip()
        self._persist()

    def _open_resource(self):
        sel = self._res_lb.curselection()
        if not sel:
            messagebox.showinfo("Select", "Select a resource first.", parent=self)
            return
        url = self._res_lb.get(sel[0])
        if url.startswith("http"):
            webbrowser.open(url)

    def _persist(self):
        plans = load_dev_plans()
        new_plans = [self.plan if p["id"] == self.plan_id else p for p in plans]
        save_dev_plans(new_plans)
        # update stats
        ms    = self.plan.get("milestones",[])
        done  = sum(1 for m in ms if m.get("status")=="complete")
        in_p  = sum(1 for m in ms if m.get("status")=="in_progress")
        total = len(ms) or 1
        rem   = total - done
        est_r = sum(m.get("estimated_weeks",0) for m in ms if m.get("status")!="complete")
        if hasattr(self, "_stat_labels"):
            self._stat_labels["Milestones"].config(text=str(total))
            self._stat_labels["Complete"].config(text=str(done))
            self._stat_labels["In Progress"].config(text=str(in_p))
            self._stat_labels["Remaining"].config(text=str(rem))
            self._stat_labels["Est Weeks Left"].config(text=str(est_r))


class CommandCenterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("COMMAND CENTER — Personal Performance System")
        self.minsize(900, 600)
        self.configure(bg=BG)
        self._current_screen = "dashboard"
        self._setup_icon()
        self._restore_window_state()
        self._build_layout()
        self._bind_shortcuts()
        self._seed_defaults()
        self.show("dashboard")
        self.after(200, self._check_reviews_on_start)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_icon(self):
        try:
            self.iconbitmap(default="")
        except Exception:
            pass

    def _seed_defaults(self):
        """Ensure default data is always present, regardless of existing files."""
        # ── SC-200 course: add if not already present ──
        programs = load_programs()
        has_sc200 = any(
            "sc-200" in p.get("name","").lower() or "sc200" in p.get("name","").lower()
            for p in programs
        )
        if not has_sc200:
            prog = get_program_template("SC-200", "certification")
            prog["id"] = max((p.get("id", 0) for p in programs), default=0) + 1
            programs.append(prog)
            save_programs(programs)

        # ── SOC dev plan: add if not already present ──
        dev_plans = load_dev_plans()
        has_soc = any(
            "soc" in p.get("name","").lower() or "l1" in p.get("name","").lower()
            for p in dev_plans
        )
        if not has_soc:
            plan = _soc_dev_plan()
            plan["id"] = max((p.get("id", 0) for p in dev_plans), default=0) + 1
            dev_plans.append(plan)
            save_dev_plans(dev_plans)

    def _restore_window_state(self):
        state = load_window_state()
        geo = state.get("geometry", "1280x800")
        try:
            self.geometry(geo)
        except Exception:
            self.geometry("1280x800")

    def _on_close(self):
        save_window_state(self.geometry())
        self.destroy()

    def _bind_shortcuts(self):
        self.bind("<Control-h>",      lambda e: self.show("dashboard"))
        self.bind("<Control-m>",      lambda e: self.show("memory"))
        self.bind("<Control-d>",      lambda e: self.show("decisions"))
        self.bind("<Control-t>",      lambda e: self.show("tasks"))
        self.bind("<Control-l>",      lambda e: self.show("log"))
        self.bind("<Control-f>",      lambda e: self.show("search"))
        self.bind("<Control-w>",      lambda e: self.show("wins"))
        self.bind("<Control-p>",      lambda e: self.show("planner"))
        self.bind("<Control-k>",      lambda e: self.show("kpis"))
        self.bind("<Control-i>",      lambda e: self.show("incidents"))
        self.bind("<Control-r>",      lambda e: self.show("courses"))
        self.bind("<Control-g>",      lambda e: self.show("develop"))
        self.bind("<Control-n>",      lambda e: self._quick_focus())
        self.bind("<Escape>",         lambda e: self.show("dashboard"))

    def _quick_focus(self):
        try:
            self.quick_entry.focus_set()
            self.quick_entry.select_range(0,"end")
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

        # ── Quick capture bar ──
        qbar = tk.Frame(self, bg=BG2, height=32)
        qbar.pack(fill="x")
        qbar.pack_propagate(False)
        tk.Label(qbar, text="⚡ Quick Log:", bg=BG2, fg=ORANGE_DIM,
                 font=FONT_MONO_S).pack(side="left", padx=(12,4), pady=4)
        self.quick_var = tk.StringVar()
        self.quick_entry = tk.Entry(qbar, textvariable=self.quick_var, bg=BG3, fg=ORANGE,
                                    insertbackground=ORANGE, font=FONT_MONO_S,
                                    relief="flat", bd=3, width=60)
        self.quick_entry.pack(side="left", pady=3)
        self.quick_entry.bind("<Return>", self._quick_log)
        tk.Label(qbar, text="  Enter to log  |  Ctrl+N to focus  |  Ctrl+H=Home",
                 bg=BG2, fg=ORANGE_DIM, font=("Consolas",7)).pack(side="left", padx=10)
        tk.Frame(self, bg=ORANGE3, height=1).pack(fill="x")

        # ── Main area ──
        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True)
        self.sidebar = tk.Frame(main, bg=BG2, width=172)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        tk.Frame(main, bg=ORANGE3, width=1).pack(side="left", fill="y")
        self.content = tk.Frame(main, bg=PANEL)
        self.content.pack(side="left", fill="both", expand=True)

        # ── Status bar ──
        tk.Frame(self, bg=ORANGE3, height=1).pack(fill="x")
        self.status_bar = tk.Label(self, text="  Ready.  Ctrl+N = quick log", bg=BG,
                                   fg=ORANGE_DIM, font=FONT_MONO_S, anchor="w")
        self.status_bar.pack(fill="x", padx=10, pady=3)

        self._build_sidebar()

    def _quick_log(self, event=None):
        text = self.quick_var.get().strip()
        if not text:
            return
        append_daily_log(f"[quick] {text}")
        index_memory("quick", text)
        self.quick_var.set("")
        self.status(f"Logged: {text[:50]}")

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
            ("develop",    "▲  Development"),
            ("wins",       "★  Wins"),
            ("planner",    "⬛  Weekly Plan"),
            ("kpis",       "◈  KPI Tracker"),
            ("incidents",  "⚠  Incidents"),
        ]
        for key, label in nav_items:
            btn = tk.Button(
                self.sidebar, text=label,
                command=lambda k=key: self.show(k),
                bg=BG2, fg=ORANGE, font=FONT_MONO,
                relief="flat", anchor="w", padx=14, pady=6,
                activebackground=ORANGE3, activeforeground=BG,
                cursor="hand2", bd=0,
            )
            btn.pack(fill="x", pady=1)
            self.nav_buttons[key] = btn

        tk.Frame(self.sidebar, bg=ORANGE3, height=1).pack(fill="x", padx=8, pady=6)
        self.review_badge = tk.Label(self.sidebar, text="", bg=BG2, fg=RED,
                                     font=("Consolas", 8, "bold"), wraplength=152)
        self.review_badge.pack(padx=6, pady=2)
        tk.Frame(self.sidebar, bg=PANEL).pack(fill="both", expand=True)
        tk.Label(self.sidebar, text="v3.0  tkinter", bg=BG2,
                 fg=GREY, font=("Consolas", 7)).pack(pady=6)
        self._update_badge()
        self._schedule_badge_refresh()

    def _schedule_badge_refresh(self):
        """Auto-refresh badge and dashboard stats every 60 seconds."""
        self._update_badge()
        if self._current_screen == "dashboard":
            for w in self.content.winfo_children():
                if isinstance(w, DashboardScreen):
                    try:
                        w._refresh_stats()
                    except Exception:
                        pass
        self.after(60000, self._schedule_badge_refresh)

    def _update_badge(self):
        n = len(get_flagged())
        overdue_tasks = sum(1 for t in load_tasks()
                            if t.get("due_date","") and t.get("due_date","") < today_str()
                            and t.get("status") != "resolved")
        lines = []
        if n:           lines.append(f"⚠ {n} decision review(s)")
        if overdue_tasks: lines.append(f"⚠ {overdue_tasks} overdue task(s)")
        if lines:
            self.review_badge.config(text="\n".join(lines), fg=RED)
        else:
            self.review_badge.config(text="✓ all clear", fg=GREEN)

    def show(self, name):
        self._current_screen = name
        for k, btn in self.nav_buttons.items():
            btn.config(bg=ORANGE3 if k == name else BG2,
                       fg=BG if k == name else ORANGE)
        for w in self.content.winfo_children():
            w.destroy()
        screen_map = {
            "dashboard": DashboardScreen,
            "memory":    MemoryScreen,
            "decisions": DecisionScreen,
            "tasks":     TaskScreen,
            "develop":   DevPlanListScreen,
            "log":       DailyLogScreen,
            "search":    SearchScreen,
            "courses":   CoursesScreen,
            "wins":      WinsScreen,
            "planner":   WeeklyPlannerScreen,
            "kpis":      KPIScreen,
            "incidents": IncidentTimelineScreen,
        }
        cls = screen_map.get(name)
        if cls:
            cls(self.content, self).pack(fill="both", expand=True)
        self._update_badge()

    def show_dev_plan(self, plan_id: int):
        self._current_screen = "develop"
        for k, btn in self.nav_buttons.items():
            btn.config(bg=ORANGE3 if k == "develop" else BG2,
                       fg=BG if k == "develop" else ORANGE)
        for w in self.content.winfo_children():
            w.destroy()
        DevPlanDetailScreen(self.content, self, plan_id).pack(fill="both", expand=True)
        self._update_badge()

    def show_program(self, program_id: int):
        self._current_screen = "courses"
        for k, btn in self.nav_buttons.items():
            btn.config(bg=ORANGE3 if k == "courses" else BG2,
                       fg=BG if k == "courses" else ORANGE)
        for w in self.content.winfo_children():
            w.destroy()
        ProgramDetailScreen(self.content, self, program_id).pack(fill="both", expand=True)
        self._update_badge()

    def status(self, msg):
        self.status_bar.config(text=f"  ●  {msg}  —  {now_str()}")
        self.after(6000, lambda: self.status_bar.config(
            text="  Ready.  Ctrl+N = quick log"))

    def _tick(self):
        self.clock_label.config(text=datetime.now().strftime("  %A  %d %b %Y  %H:%M:%S  "))
        self.after(1000, self._tick)

    def _check_reviews_on_start(self):
        flagged = get_flagged()
        overdue = [t for t in load_tasks()
                   if t.get("due_date","") and t.get("due_date","") < today_str()
                   and t.get("status") != "resolved"]
        msgs = []
        if flagged:  msgs.append(f"• {len(flagged)} decision(s) due for review")
        if overdue:  msgs.append(f"• {len(overdue)} overdue task(s)")
        if msgs:
            messagebox.showwarning("Attention Required",
                "\n".join(msgs) + "\n\nCheck Decisions and Tasks.", parent=self)


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = CommandCenterApp()
    app.mainloop()

# ── Wins & Achievements Screen ─────────────────────────────────────────────────
WIN_CATS = ["Achievement","Compliment","Metric Hit","Recognition","Milestone","Other"]

