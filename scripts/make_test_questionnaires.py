#!/usr/bin/env python
"""
Generate realistic Australian GRC questionnaire Excel files for import testing.

Covers the frameworks Australian GRC consultants actually work with:
  1. ASD Essential Eight Maturity Assessment (government/enterprise)
  2. Australian Privacy Act / NDB Vendor Assessment (financial services)
  3. APRA CPS 234 Technology Supplier Assessment (banking/insurance)
  4. ISO 27001 Vendor Security Assessment (AU context, not GDPR/HIPAA)
  5. Quick Security Check — 6 questions, 5-minute test

Usage (from project root):
    python scripts/make_test_questionnaires.py

Outputs to: test_questionnaires/
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill

OUTPUT_DIR = Path("test_questionnaires")

QUESTIONNAIRES = [

    # ── 1. ASD Essential Eight ───────────────────────────────────────────────
    {
        "filename": "AU_Gov_Essential_Eight_Assessment_2026.xlsx",
        "sheet": "Essential Eight",
        "customer": "Pacific State Government — Dept of Digital Economy",
        "questions": [
            "Do you implement the ASD Essential Eight mitigation strategies? Please state your current maturity level (ML0–ML3) for each of the eight controls.",
            "What is your current maturity level for Application Control, and how do you prevent unapproved applications from executing?",
            "How do you patch internet-facing applications? What is your target timeframe for critical vulnerabilities?",
            "How do you patch operating systems across your environment? What is your remediation SLA for critical patches?",
            "Describe your Multi-Factor Authentication (MFA) implementation. Which systems, accounts and access methods require MFA?",
            "How do you restrict and manage administrative privileges? Are privileged accounts separate from standard user accounts?",
            "How do you restrict Microsoft Office macros? Are macros blocked by default, and how are exceptions approved?",
            "Describe your user application hardening controls. How do you prevent web browsers from running Java and Flash from the internet?",
            "Describe your backup regime. How frequently are backups taken, where are they stored, and how often is restoration tested?",
            "Have you completed an ACSC Essential Eight assessment in the last 12 months? Please provide the assessment date and overall maturity result.",
            "Do you use an automated vulnerability scanner? How often do you scan, and what is your process for acting on results?",
            "How do you monitor for and detect execution of malicious or unsigned code in your environment?",
            "Describe your privileged access workstation (PAW) or jump server architecture for administrative tasks.",
            "How do you manage local administrator accounts on workstations? Do you use LAPS or an equivalent solution?",
            "Do you participate in the ACSC's Cyber Threat Intelligence Sharing (CTIS) program or any equivalent threat intel feed?",
            "How do you ensure software installed on endpoints is from an approved, authorised source?",
            "Describe your approach to network segmentation, particularly isolating privileged management networks.",
            "What logging and monitoring controls do you have in place? How long are logs retained and who reviews them?",
            "Have you experienced a cyber security incident in the past two years? If so, briefly describe the nature and remediation.",
            "Do you have a documented Cyber Security Incident Response Plan? When was it last tested?",
        ],
    },

    # ── 2. Australian Privacy Act / NDB ─────────────────────────────────────
    {
        "filename": "AU_Privacy_Act_Vendor_Assessment_2026.xlsx",
        "sheet": "Privacy Assessment",
        "customer": "Southern Cross Financial Group",
        "questions": [
            "Are you an APP entity bound by the Australian Privacy Act 1988? Confirm whether you are subject to the Australian Privacy Principles (APPs).",
            "Provide a link to your current Privacy Policy. Confirm it is publicly available and was reviewed within the last 12 months.",
            "Do you have a designated Privacy Officer? Provide their title and contact details.",
            "In which countries is personal information of Australian customers stored or processed? List all locations.",
            "Do you transfer personal information outside Australia? If yes, describe the safeguards in place under APP 8.",
            "Describe how you collect personal information and how you notify individuals at the point of collection (APP 5).",
            "Under what circumstances do you disclose personal information to third parties? Who are your key sub-processors?",
            "How do individuals request access to or correction of their personal information? What is your response timeframe?",
            "Do you have a documented Data Breach Response Plan aligned with the Notifiable Data Breaches (NDB) scheme?",
            "Walk us through your NDB incident response process — from detection to OAIC notification.",
            "What is the maximum timeframe between discovering a suspected eligible data breach and completing your assessment under the NDB scheme?",
            "Have you reported any eligible data breaches to the OAIC in the past three years? If yes, describe the nature of the breach.",
            "How long do you retain personal information? Describe your data retention schedule and secure destruction process.",
            "How do you handle personal information when the contract with Southern Cross Financial Group ends?",
            "What technical controls protect personal information stored in your systems (encryption, access control, logging)?",
            "Do you conduct Privacy Impact Assessments (PIAs) for new projects that involve personal information?",
            "How do you ensure your staff understand their obligations under the Australian Privacy Act? Describe your training program.",
            "Are you currently under investigation by the OAIC or subject to any privacy-related complaints or enforcement actions?",
        ],
    },

    # ── 3. APRA CPS 234 ──────────────────────────────────────────────────────
    {
        "filename": "APRA_CPS234_Technology_Supplier_2026.xlsx",
        "sheet": "CPS 234 Assessment",
        "customer": "Atlas Bank — Third Party Risk Management",
        "questions": [
            "Are you aware that Atlas Bank is an APRA-regulated entity subject to Prudential Standard CPS 234? Confirm you have read and understood your obligations as a material service provider.",
            "Describe your information security capability. How is it commensurate with the size, nature and extent of threats to the information assets you manage on behalf of Atlas Bank?",
            "Do you have a Board-approved Information Security Policy? Provide the policy name, version, and date of last Board approval.",
            "Who holds ultimate accountability for information security in your organisation? Provide their title.",
            "Describe the information security controls you have in place to protect Atlas Bank's data and systems, classified by control type (preventive, detective, corrective).",
            "Do you conduct annual testing of your information security controls? Describe the testing methodology and who performs it.",
            "Have you completed an independent assessment of your information security controls in the last 12 months, as required by CPS 234 paragraph 36? Provide the date and assessor.",
            "How do you notify Atlas Bank of material information security incidents? What is your notification timeframe and escalation process?",
            "Have you experienced any information security incidents in the past 12 months that impacted or could have impacted Atlas Bank? Provide details.",
            "How do you manage your own third-party (fourth-party) suppliers who may have access to Atlas Bank's information assets?",
            "Describe your vulnerability management program including scan frequency, severity classification, and remediation timeframes.",
            "Do you conduct penetration testing on systems that process Atlas Bank data? How frequently, and by whom?",
            "Describe your access control framework for Atlas Bank's data — who has access, how is it provisioned, reviewed, and revoked?",
            "How do you protect Atlas Bank's data in transit and at rest? Specify encryption standards and key management practices.",
            "Do you have a Business Continuity Plan and Disaster Recovery Plan for services provided to Atlas Bank? When were they last tested?",
            "What are your RTO and RPO commitments for services provided to Atlas Bank? Have these been validated through testing?",
        ],
    },

    # ── 4. ISO 27001 Vendor Security Assessment (AU) ─────────────────────────
    {
        "filename": "AU_ISO27001_Vendor_Security_Assessment_2026.xlsx",
        "sheet": "Vendor Security",
        "customer": "AusMed Health Systems Pty Ltd",
        "questions": [
            "Are you ISO 27001 certified? If yes, provide your certificate number, scope, issuing body, and expiry date.",
            "If not ISO 27001 certified, what equivalent security framework or standard do you align to? Provide evidence of compliance.",
            "Do you hold a current SOC 2 Type II report? Provide the audit period and a summary of any exceptions.",
            "Describe your Information Security Management System (ISMS). What is its scope and how is it governed?",
            "How do you manage information security risks? Describe your risk assessment process and frequency.",
            "Do you comply with the Australian Privacy Act 1988 and Australian Privacy Principles? Confirm and describe your compliance approach.",
            "Do you align with the ASD Essential Eight? If yes, provide your current maturity level across the eight controls.",
            "How is MFA enforced across your organisation — which systems, users and access types require it?",
            "Describe your patch management process. What are your SLAs for critical, high, and medium vulnerabilities?",
            "How do you manage and control privileged access to systems that will process AusMed data?",
            "How is AusMed's data encrypted at rest and in transit? Specify encryption algorithms and key management approach.",
            "In which Australian state(s) or territories is data physically stored? Do you use offshore data centres or cloud regions?",
            "Describe your security incident response process. What is your commitment for notifying AusMed of a security incident?",
            "Do you have a documented Business Continuity Plan? What are your RTO and RPO for services provided to AusMed?",
            "How do you manage employee background checks, security training, and offboarding access revocation?",
            "Describe your third-party supplier management process. How do you assess and monitor sub-processors?",
            "Do you conduct annual penetration testing on systems used to deliver services to AusMed? Provide the last test date.",
            "How do you handle and securely destroy AusMed data at contract end?",
            "Provide details of any security incidents, data breaches, or regulatory actions in the past two years.",
            "Are you willing to complete an onsite security audit or provide audit rights to AusMed upon request?",
        ],
    },

    # ── 5. Quick 5-minute check ──────────────────────────────────────────────
    {
        "filename": "Quick_Security_Check_5min.xlsx",
        "sheet": "Quick Check",
        "customer": "StartupMate Pty Ltd",
        "questions": [
            "Is MFA enforced on all employee accounts including email, cloud services, and remote access?",
            "Is customer data encrypted at rest and in transit using industry-standard algorithms?",
            "Do you comply with the Australian Privacy Act 1988 and do you have a public Privacy Policy?",
            "Have you completed a security audit or penetration test in the last 12 months?",
            "Do you have a documented process for notifying customers of a data breach under the Notifiable Data Breaches scheme?",
            "Are software dependencies and operating systems kept up to date with security patches within 30 days of release?",
        ],
    },
]


def make_xlsx(q: dict) -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = q["sheet"]

    # Header row
    header_fill = PatternFill(start_color="1e3a5f", end_color="1e3a5f", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)

    ws.append(["#", "Question", "Answer"])
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(vertical="center", wrap_text=True)

    ws.row_dimensions[1].height = 22

    # Question rows
    row_fill_alt = PatternFill(start_color="f0f4fa", end_color="f0f4fa", fill_type="solid")
    for i, question in enumerate(q["questions"], 1):
        ws.append([i, question, ""])
        row = ws[i + 1]
        if i % 2 == 0:
            for cell in row:
                cell.fill = row_fill_alt
        row[1].alignment = Alignment(wrap_text=True, vertical="top")
        row[2].alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[i + 1].height = 45

    ws.column_dimensions["A"].width = 5
    ws.column_dimensions["B"].width = 75
    ws.column_dimensions["C"].width = 55

    path = OUTPUT_DIR / q["filename"]
    wb.save(path)
    n = len(q["questions"])
    print(f"  ✓  {q['filename']}  ({n} question{'s' if n != 1 else ''})")


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    print(f"Generating {len(QUESTIONNAIRES)} AU-focused questionnaire files → {OUTPUT_DIR}/\n")
    for q in QUESTIONNAIRES:
        make_xlsx(q)
    print(f"\nDone. Upload via the Questionnaires page.")


if __name__ == "__main__":
    main()
