#!/usr/bin/env python
"""
Generate sample questionnaire Excel files for import testing.

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
    {
        "filename": "TechCorp_Security_Assessment_2026.xlsx",
        "sheet": "Security Assessment",
        "questions": [
            "Do you maintain an up-to-date information security policy reviewed by executive leadership?",
            "Is multi-factor authentication (MFA) required for all user accounts with access to production systems?",
            "How is customer data encrypted at rest and in transit? Please specify algorithms and key lengths.",
            "What is your process and timeline for notifying customers in the event of a data breach?",
            "Do you conduct annual penetration testing? Who performs it and what scope does it cover?",
            "What is your vulnerability remediation SLA for critical (CVSS 9.0+) findings?",
            "Describe your data retention and secure deletion practices for customer data after contract termination.",
            "Do you hold a current SOC 2 Type II or ISO 27001 certification?",
            "How do you manage and audit privileged access to production databases and infrastructure?",
            "What is your Recovery Time Objective (RTO) and Recovery Point Objective (RPO)?",
            "Do you perform background checks on employees with access to customer data?",
            "How do you handle security vulnerabilities in third-party software dependencies?",
            "Describe your security incident response process including escalation and SLAs.",
            "Do you carry cyber liability insurance? What is the coverage limit?",
            "How do you enforce least-privilege access control across your organization?",
        ],
    },
    {
        "filename": "GlobalBank_Vendor_Due_Diligence_2026.xlsx",
        "sheet": "Vendor Due Diligence",
        "questions": [
            "Provide your most recent SOC 2 Type II report date and audit period.",
            "Are all production system logins protected by phishing-resistant MFA (FIDO2 or equivalent)?",
            "Where is customer data physically stored? List all geographic regions and cloud providers.",
            "What sub-processors or fourth parties have access to customer data? Provide a current list.",
            "Describe your encryption key management practices including rotation frequency and HSM usage.",
            "What is your process for revoking employee access upon termination?",
            "How frequently do you test your disaster recovery plan and what were the results of the last test?",
            "Do you have a formal vendor risk management program for your own third-party suppliers?",
            "How do you protect against insider threats?",
            "Describe your network segmentation architecture between production and non-production environments.",
            "What security training is mandatory for all employees? How often is it completed?",
            "How do you detect and respond to DDoS attacks?",
            "What change management controls are in place before changes reach production?",
            "Describe your approach to data minimization and privacy by design.",
            "Do you have a formal bug bounty or responsible disclosure program?",
            "What GDPR and CCPA compliance mechanisms do you have in place?",
            "How do you manage secrets, API keys, and credentials across your infrastructure?",
            "Describe your container and cloud workload security controls.",
        ],
    },
    {
        "filename": "HealthPlus_HIPAA_Security_Review_2026.xlsx",
        "sheet": "HIPAA Security Review",
        "questions": [
            "Do you have a signed Business Associate Agreement (BAA) process? Describe how you handle BAAs.",
            "How is Protected Health Information (PHI) encrypted at rest and in transit?",
            "Describe your access control policies for staff who may access PHI.",
            "What audit logging do you maintain for access to systems containing PHI?",
            "How do you handle and report breaches involving PHI under HIPAA Breach Notification Rule?",
            "Do you perform a HIPAA Security Risk Assessment? How frequently?",
            "How do you ensure PHI is not retained beyond its required retention period?",
            "Describe your workforce training program specific to HIPAA requirements.",
            "What physical security controls protect systems that store or process PHI?",
            "How do you manage access for business associates and subcontractors who access PHI?",
            "Do you have documented policies for workstation use and device security for PHI access?",
            "How do you handle portable media and mobile devices that may contain PHI?",
            "What is your incident response procedure specific to PHI breaches?",
            "Describe your data backup and disaster recovery procedures for PHI systems.",
        ],
    },
    {
        "filename": "StartupCo_Quick_Security_Check_2026.xlsx",
        "sheet": "Security Check",
        "questions": [
            "Do you have MFA enabled for all employee accounts?",
            "Is customer data encrypted at rest?",
            "Do you have a privacy policy and terms of service?",
            "Have you had a security audit or penetration test in the last 12 months?",
            "Do you have a process for responding to security incidents?",
            "Are employee passwords stored using a secure hashing algorithm?",
            "Do you use a reputable cloud provider (AWS, GCP, Azure)?",
            "Do you have a data breach notification process?",
            "Are software dependencies regularly updated for security patches?",
            "Do you have offboarding procedures that revoke access when employees leave?",
        ],
    },
    {
        "filename": "EuroRetail_GDPR_Compliance_Questionnaire_2026.xlsx",
        "sheet": "GDPR Compliance",
        "questions": [
            "Are you able to act as a Data Processor under GDPR? Do you sign Data Processing Agreements?",
            "In which EU/EEA member states or third countries is personal data stored or processed?",
            "What legal basis do you rely on for processing personal data on behalf of customers?",
            "How do you fulfill data subject access requests (DSAR) and within what timeframe?",
            "Describe your process for handling requests for erasure ('right to be forgotten').",
            "How do you handle data portability requests?",
            "Do you maintain a Record of Processing Activities (RoPA) as required by GDPR Article 30?",
            "How do you ensure cross-border data transfers comply with GDPR (SCCs, adequacy decision, etc.)?",
            "What is your data breach notification procedure under GDPR Article 33/34?",
            "Do you conduct Data Protection Impact Assessments (DPIAs) for high-risk processing?",
            "Who is your Data Protection Officer (DPO) and how can they be contacted?",
            "How do you ensure your sub-processors comply with GDPR requirements?",
            "What technical and organizational measures (TOMs) do you have in place to protect personal data?",
            "How do you handle consent management and withdrawal of consent?",
            "What is your data minimization and purpose limitation policy?",
            "How do you handle personal data of minors?",
        ],
    },
]


def make_xlsx(q: dict) -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = q["sheet"]

    # Header row
    header_fill = PatternFill(start_color="3F51B5", end_color="3F51B5", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)

    ws.append(["#", "Question", "Answer"])
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(vertical="center", wrap_text=True)

    ws.row_dimensions[1].height = 22

    # Question rows
    row_fill_alt = PatternFill(start_color="F5F5FF", end_color="F5F5FF", fill_type="solid")
    for i, question in enumerate(q["questions"], 1):
        ws.append([i, question, ""])
        row = ws[i + 1]
        if i % 2 == 0:
            for cell in row:
                cell.fill = row_fill_alt
        row[1].alignment = Alignment(wrap_text=True, vertical="top")
        row[2].alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[i + 1].height = 40

    # Column widths
    ws.column_dimensions["A"].width = 5
    ws.column_dimensions["B"].width = 72
    ws.column_dimensions["C"].width = 55

    path = OUTPUT_DIR / q["filename"]
    wb.save(path)
    print(f"   ✓ {q['filename']}  ({len(q['questions'])} questions)")


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    print(f"📊  Generating {len(QUESTIONNAIRES)} questionnaire files → {OUTPUT_DIR}/\n")
    for q in QUESTIONNAIRES:
        make_xlsx(q)
    print(f"\n✅  Done. Upload them at /knowledge or the questionnaire import page.")


if __name__ == "__main__":
    main()
