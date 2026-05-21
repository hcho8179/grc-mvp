#!/usr/bin/env python
"""
Seed the database with Acme Corp demo data.

Usage (from project root):
    python scripts/seed_demo.py

Drops ALL existing data, then creates:
  - 3 policy documents (Information Security, Data Protection, Incident Response)
  - 30 past Q&A pairs as knowledge chunks
  - 1 sample questionnaire (MegaBank Vendor Assessment, 20 questions)
"""

import asyncio
import io
import sys
from pathlib import Path

# Allow running from the project root
sys.path.insert(0, str(Path(__file__).parent.parent))

import openpyxl
from docx import Document as DocxDocument
from sqlalchemy import text

from app.db import SessionLocal
from app.models import (
    Document, FileType, KnowledgeChunk, LLMCall, Organization, Questionnaire, Question,
    QuestionStatus, SourceType,
)
from app.services.chunking import chunk_text
from app.services.embeddings import get_embedding_provider
from app.services.parsing import parse_docx, parse_xlsx_qa


# ---------------------------------------------------------------------------
# Policy document content
# ---------------------------------------------------------------------------

INFO_SEC_POLICY = """INFORMATION SECURITY POLICY
Version 3.2 | Effective: January 1, 2026 | Owner: CISO

1. PURPOSE AND SCOPE
This Information Security Policy establishes the framework for protecting Acme Corp's information assets, customer data, and IT infrastructure. It applies to all employees, contractors, vendors, and third parties who access Acme Corp systems.

2. ACCESS CONTROL
All access to systems and data is granted on a least-privilege basis following role-based access control (RBAC). Access rights are reviewed quarterly. Privileged access requires additional approval from the Security team.

Multi-factor authentication (MFA) is mandatory for all user accounts accessing production systems, administrative interfaces, and remote connections. Acceptable MFA methods include TOTP authenticator apps and FIDO2 hardware security keys. SMS-based MFA is not permitted due to SIM-swapping vulnerabilities.

Passwords must be at least 14 characters and contain uppercase letters, lowercase letters, numbers, and special characters. Passwords are rotated every 90 days. The last 12 passwords may not be reused. All passwords are stored using bcrypt hashing with a minimum cost factor of 12.

3. DATA CLASSIFICATION
Data is classified into four tiers: Public, Internal, Confidential, and Restricted. Customer personal data and financial records are classified as Restricted and require encryption at rest and in transit. Data owners are responsible for classifying data in their domain.

4. ENCRYPTION
All data at rest is encrypted using AES-256. Database encryption keys are managed through AWS KMS with automatic rotation every 12 months. All data in transit is encrypted using TLS 1.2 or higher. TLS 1.0 and 1.1 are disabled on all endpoints.

Customer data stored in our cloud infrastructure uses envelope encryption: each customer's data is encrypted with a unique data encryption key (DEK), which is itself encrypted by a key encryption key (KEK) stored in AWS KMS.

5. VULNERABILITY MANAGEMENT
Acme Corp conducts automated vulnerability scanning of all internet-facing systems weekly using industry-standard tools. Critical vulnerabilities (CVSS 9.0+) must be remediated within 72 hours. High vulnerabilities (CVSS 7.0-8.9) within 7 days. Medium vulnerabilities within 30 days.

Annual penetration testing is conducted by an accredited third-party firm. Findings are tracked to remediation in our security issue tracker. The most recent penetration test was completed in October 2025 with no critical findings.

6. SECURITY MONITORING
Security events are logged to a centralized SIEM. Alerts are monitored 24/7 by our Security Operations team. Log retention is 12 months online and 7 years in cold storage to meet regulatory requirements.

7. SECURITY TRAINING
All employees complete mandatory security awareness training upon hire and annually thereafter. Phishing simulation exercises are conducted quarterly. Role-specific training (e.g., secure development) is provided to engineering staff.

8. COMPLIANCE
Acme Corp maintains SOC 2 Type II certification, audited annually by an independent third-party auditor. The most recent audit covered the period October 2024 through September 2025 with no exceptions noted.
"""

DATA_PROTECTION_POLICY = """DATA PROTECTION POLICY
Version 2.1 | Effective: January 1, 2026 | Owner: DPO

1. PURPOSE
This policy defines how Acme Corp collects, processes, stores, and deletes personal data in compliance with GDPR, CCPA, and applicable data protection laws.

2. DATA RETENTION
Customer personal data is retained for the duration of the contract plus 3 years, unless a shorter retention period is required by law or requested by the customer. After the retention period, data is securely deleted using NIST 800-88 compliant methods. Backup data is purged on the same schedule as live data.

Transactional logs containing personal data are retained for 12 months. Security audit logs are retained for 7 years. Financial records are retained for 7 years as required by tax regulations.

3. DATA SUBJECT RIGHTS
Acme Corp supports all GDPR data subject rights including: right of access, right to rectification, right to erasure (right to be forgotten), right to restriction of processing, right to data portability, and right to object. Requests are fulfilled within 30 days. A dedicated privacy portal is available at privacy.acme.com.

4. DATA TRANSFERS
Customer data is stored in the European Union (AWS eu-west-1) and the United States (AWS us-east-1). Cross-border transfers rely on Standard Contractual Clauses (SCCs) approved by the European Commission. Acme Corp participates in the EU-US Data Privacy Framework.

5. THIRD-PARTY DATA PROCESSORS
All vendors with access to personal data sign a Data Processing Agreement (DPA). Vendors are assessed annually for security posture. A list of sub-processors is maintained at acme.com/sub-processors and is updated within 30 days of any change.

6. DATA BREACH NOTIFICATION
In the event of a data breach affecting personal data, Acme Corp will notify affected supervisory authorities within 72 hours of becoming aware of the breach, as required by GDPR Article 33. Affected data subjects will be notified without undue delay if the breach poses a high risk to their rights and freedoms.

7. BACKUP AND RECOVERY
Customer data is backed up daily to geographically separate AWS regions. Backups are encrypted using AES-256. Recovery Time Objective (RTO) is 4 hours. Recovery Point Objective (RPO) is 1 hour. Backup restoration is tested quarterly.

8. PRIVACY BY DESIGN
New products and features undergo a Privacy Impact Assessment (PIA) before launch. Data minimization principles are applied throughout — Acme Corp collects only data necessary for the stated purpose.
"""

INCIDENT_RESPONSE_PLAN = """INCIDENT RESPONSE PLAN
Version 1.8 | Effective: January 1, 2026 | Owner: Security Engineering

1. PURPOSE
This plan defines the process for identifying, containing, eradicating, and recovering from security incidents affecting Acme Corp systems and customer data.

2. INCIDENT CLASSIFICATION
Severity 1 (Critical): Active data breach, ransomware, production system compromise. Response time: 15 minutes. Incidents affecting 10,000+ customers or involving regulated data.
Severity 2 (High): Confirmed intrusion without confirmed data loss, critical vulnerability exploitation. Response time: 1 hour.
Severity 3 (Medium): Unsuccessful attack, policy violation, single account compromise. Response time: 4 hours.
Severity 4 (Low): Security alert requiring investigation, no confirmed impact. Response time: next business day.

3. RESPONSE TEAM
Incident Commander: CISO or designated deputy
Security Lead: On-call Security Engineer
Technical Lead: On-call Platform Engineer
Communications: VP of Engineering (internal), Legal (customer/regulatory)
All team members are available 24/7 via PagerDuty rotation.

4. DETECTION AND REPORTING
Incidents may be detected via: SIEM alerts, customer reports, employee reports, third-party disclosure, or bug bounty program. All suspected incidents must be reported immediately via the #security-incidents Slack channel or security@acme.com.

5. CONTAINMENT
Immediate containment actions are taken within the first hour: isolate affected systems, revoke compromised credentials, block malicious IP addresses, and preserve forensic evidence. No affected systems are shut down without Incident Commander approval to preserve evidence.

6. ERADICATION AND RECOVERY
After containment, root cause analysis is performed. Affected systems are rebuilt from known-good images. Compromised credentials are reset. System is returned to production only after validation by Security Engineering.

7. POST-INCIDENT REVIEW
A post-incident review is conducted within 5 business days of resolution. Findings, timeline, and remediation actions are documented in our incident tracker. Lessons learned are incorporated into security controls within 30 days.

8. SERVICE LEVEL AGREEMENTS
Severity 1: Customer notification within 1 hour of confirmation, regulatory notification within 72 hours.
Severity 2: Customer notification within 4 hours if customer data affected.
Severity 3-4: Reported in monthly security summary to customers.
"""

# ---------------------------------------------------------------------------
# 30 Q&A pairs (Acme Corp voice)
# ---------------------------------------------------------------------------

QA_PAIRS = [
    ("Do you perform background checks on employees?", "Yes, all employees and contractors undergo background checks prior to starting, including criminal history, employment verification, and reference checks. Checks comply with local laws in all jurisdictions."),
    ("Do you have a formal information security policy?", "Yes, Acme Corp maintains a comprehensive Information Security Policy reviewed and approved by executive leadership annually. The policy covers access control, encryption, vulnerability management, and incident response."),
    ("Is MFA required for remote access?", "Yes, multi-factor authentication is mandatory for all remote access to production systems and corporate networks. We support TOTP authenticator apps and FIDO2 hardware keys. SMS MFA is not permitted."),
    ("How do you handle privileged access management?", "Privileged access is granted on a least-privilege, need-to-know basis with additional approval required. All privileged sessions are logged and audited. Privileged accounts are reviewed quarterly and de-provisioned immediately upon role change or termination."),
    ("Do you encrypt data at rest?", "Yes, all customer data is encrypted at rest using AES-256. Encryption keys are managed through AWS KMS with automatic rotation every 12 months. We use envelope encryption with per-customer data encryption keys."),
    ("Do you encrypt data in transit?", "All data in transit is encrypted using TLS 1.2 or higher. TLS 1.0 and 1.1 are disabled. Internal service-to-service communication uses mutual TLS (mTLS). We achieve an A+ rating on SSL Labs."),
    ("What is your password policy?", "Passwords must be at least 14 characters and include uppercase, lowercase, numbers, and special characters. Passwords rotate every 90 days, with the last 12 passwords prohibited. All passwords are hashed using bcrypt with a minimum cost factor of 12."),
    ("Do you have a SOC 2 report?", "Yes, Acme Corp holds a current SOC 2 Type II certification. Our audit period covers October 2024 through September 2025. The report is available under NDA to enterprise customers upon request."),
    ("How often do you perform penetration testing?", "We engage an accredited third-party firm for annual penetration testing of our full production environment. The most recent test was completed October 2025 with no critical findings. Application-layer penetration testing is also conducted after major releases."),
    ("Do you have a vulnerability management program?", "Yes. We perform automated vulnerability scanning weekly on all internet-facing systems. Critical vulnerabilities (CVSS 9.0+) must be remediated within 72 hours; high within 7 days; medium within 30 days. Results are tracked in our security issue tracker."),
    ("What is your data retention policy?", "Customer personal data is retained for the contract duration plus 3 years. After the retention period, data is securely deleted using NIST 800-88 compliant methods. Financial records are retained for 7 years per tax regulations."),
    ("How do you handle data subject requests (GDPR/CCPA)?", "We support all GDPR and CCPA data subject rights. Requests are fulfilled within 30 days. A self-service privacy portal is available at privacy.acme.com. Requests for data deletion are processed within 7 days and include all backup copies on their normal purge schedule."),
    ("Where is customer data stored?", "Customer data is stored in the European Union (AWS eu-west-1) and the United States (AWS us-east-1). Cross-border transfers use Standard Contractual Clauses approved by the European Commission."),
    ("Do you have a business continuity plan?", "Yes, Acme Corp maintains a Business Continuity Plan (BCP) and Disaster Recovery Plan (DRP) tested annually. Our RTO is 4 hours and RPO is 1 hour. Data is backed up daily to geographically separate AWS regions."),
    ("What is your incident response process?", "We follow a documented Incident Response Plan with severity classification, a 24/7 on-call Security Engineering team, and defined SLAs. Severity 1 incidents require customer notification within 1 hour and regulatory notification within 72 hours."),
    ("Do you have cyber liability insurance?", "Yes, Acme Corp maintains cyber liability insurance with $10M per occurrence coverage, including first-party and third-party coverage for data breaches, business interruption, and regulatory defense costs."),
    ("How do you manage third-party vendor risk?", "All vendors with access to customer data sign a Data Processing Agreement and undergo annual security assessments. We maintain a register of sub-processors updated within 30 days of any change. Critical vendors are assessed for SOC 2 or equivalent certifications."),
    ("Do you have a formal SDLC security process?", "Yes, security is integrated throughout our SDLC. Developers complete secure coding training. Code reviews are mandatory for all changes. SAST tools scan every pull request. DAST scanning is performed on staging before production deploys."),
    ("How do you handle security logging and monitoring?", "All security-relevant events are logged to a centralized SIEM. Logs are retained for 12 months online and 7 years in cold storage. Alerts are monitored 24/7 by our Security Operations team with PagerDuty escalation."),
    ("Do you perform security awareness training?", "All employees complete mandatory security awareness training on hire and annually. Phishing simulations run quarterly. Role-specific secure development training is provided to engineering teams. Training completion is tracked and enforced."),
    ("What cloud providers do you use?", "We use Amazon Web Services (AWS) as our primary cloud provider. We are an AWS Advanced Technology Partner. Infrastructure is deployed using Terraform with change management controls. We do not use multi-cloud for primary systems."),
    ("How do you handle software dependencies and open-source security?", "We maintain a Software Bill of Materials (SBOM) for all services. Dependency scanning runs automatically in CI/CD. Dependabot monitors for known CVEs daily. We have a policy to address known critical dependency vulnerabilities within 72 hours."),
    ("Do you have a bug bounty program?", "Yes, Acme Corp operates a private bug bounty program through HackerOne. The program covers our production web application, API endpoints, and mobile applications. Critical findings are rewarded up to $10,000 and remediated within 72 hours."),
    ("How do you manage encryption keys?", "Encryption keys are managed through AWS Key Management Service (KMS). Keys are automatically rotated every 12 months. Access to KMS operations is logged and monitored. Cryptographic operations are performed in FIPS 140-2 validated hardware security modules."),
    ("Do you perform disaster recovery testing?", "Disaster recovery tests are conducted annually, including a full failover to our secondary AWS region. The last DR test was completed in July 2025 with an RTO of 3.2 hours, within our 4-hour target. Test results are documented and reviewed by leadership."),
    ("What are your data center physical security controls?", "Acme Corp uses AWS data centers which maintain SOC 2, ISO 27001, and FedRAMP certifications. Physical access controls include biometric authentication, 24/7 security guards, CCTV monitoring, and man-trap entry systems. Acme Corp staff do not have physical data center access."),
    ("Do you have a change management process?", "All production changes require a written change request, peer review, and approval from a senior engineer. Emergency changes require post-facto review within 24 hours. We maintain a change log accessible to the Security team for audit purposes."),
    ("How do you protect against DDoS attacks?", "We use AWS Shield Advanced for DDoS protection, providing automatic mitigation for network and application layer attacks. AWS CloudFront serves as our CDN with built-in DDoS mitigation. We conduct annual DDoS simulation exercises to validate our defenses."),
    ("Do you have a formal risk management program?", "Yes, Acme Corp maintains a risk register updated quarterly. Risks are assessed using a qualitative likelihood-impact matrix. The CISO presents a risk summary to the Board of Directors quarterly. We follow the NIST Cybersecurity Framework as our risk management foundation."),
    ("What is your process for offboarding employees?", "Upon termination, all system access is revoked within 1 hour for voluntary departures and immediately for involuntary terminations. Company devices are recovered and wiped. Service account credentials associated with the employee are rotated. Offboarding is tracked through our HR and IT systems."),
]

# ---------------------------------------------------------------------------
# 20-question MegaBank questionnaire
# ---------------------------------------------------------------------------

MEGABANK_QUESTIONS = [
    "Do you maintain a current SOC 2 Type II or equivalent third-party audit report?",
    "Is multi-factor authentication enforced for all administrative and privileged access?",
    "Describe your encryption standards for data at rest and in transit.",
    "How frequently do you conduct external penetration testing, and who performs it?",
    "What is your process and SLA for notifying customers of a data breach?",
    "Where is customer data physically stored, and do you use any sub-processors?",
    "What is your vulnerability remediation SLA for critical security findings?",
    "Do you have a formal business continuity and disaster recovery plan? What is your RTO/RPO?",
    "How do you manage and review privileged access to production systems?",
    "Do you perform background checks on employees with access to customer data?",
    "How do you handle software dependency vulnerabilities and supply chain risks?",
    "Describe your security incident response process and escalation procedures.",
    "Do you carry cyber liability insurance? What is the coverage amount?",
    "How do you ensure secure coding practices in your software development lifecycle?",
    "What logging and monitoring controls do you have in place for security events?",
    "How do you manage encryption key lifecycle, including rotation and revocation?",
    "Describe your third-party vendor security assessment process.",
    "Do you have a formal data retention and secure deletion policy?",
    "How do you protect your infrastructure against DDoS and other availability attacks?",
    "What security awareness training do you provide to employees, and how often?",
]


# ---------------------------------------------------------------------------
# Seed logic
# ---------------------------------------------------------------------------

async def seed() -> None:
    db = SessionLocal()

    # Show existing orgs
    orgs = db.query(Organization).order_by(Organization.id).all()
    if not orgs:
        print("No organizations found. Register an account at http://localhost:5173/register first.")
        db.close()
        return

    print("Existing organizations:")
    for org in orgs:
        print(f"  [{org.id}] {org.name}  (slug: {org.slug})")
    org_id_str = input("\nEnter org ID to seed demo data into: ").strip()
    try:
        org_id = int(org_id_str)
        org = next(o for o in orgs if o.id == org_id)
    except (ValueError, StopIteration):
        print("Invalid org ID. Aborted.")
        db.close()
        return

    print(f"\nSeeding into: {org.name} (id={org.id})")
    print("This will DELETE existing knowledge + questionnaires for this org (users are kept).")
    confirm = input("Type 'yes' to continue: ").strip().lower()
    if confirm != "yes":
        print("Aborted.")
        db.close()
        return

    provider = get_embedding_provider()

    # Clear only this org's data
    print("\nClearing existing data for this org…")
    existing_qs = db.query(Questionnaire).filter(Questionnaire.org_id == org_id).all()
    for qs in existing_qs:
        db.delete(qs)
    existing_docs = db.query(Document).filter(Document.org_id == org_id).all()
    for d in existing_docs:
        db.delete(d)
    db.execute(text(f"DELETE FROM llm_calls WHERE org_id = {org_id}"))
    db.commit()

    # -----------------------------------------------------------------------
    # Policy documents
    # -----------------------------------------------------------------------
    print("Creating policy documents…")

    policies = [
        ("Acme Corp — Information Security Policy.docx", INFO_SEC_POLICY),
        ("Acme Corp — Data Protection Policy.docx", DATA_PROTECTION_POLICY),
        ("Acme Corp — Incident Response Plan.docx", INCIDENT_RESPONSE_PLAN),
    ]

    for filename, content in policies:
        doc_obj = DocxDocument()
        for para in content.strip().split("\n\n"):
            doc_obj.add_paragraph(para.strip())
        buf = io.BytesIO()
        doc_obj.save(buf)
        docx_bytes = buf.getvalue()

        text_content = parse_docx(docx_bytes)
        chunks = chunk_text(text_content)

        print(f"   {filename}: {len(chunks)} chunks")

        document = Document(
            filename=filename,
            file_type=FileType.docx,
            chunk_count=len(chunks),
            org_id=org_id,
        )
        db.add(document)
        db.flush()

        embeddings = await provider.embed(chunks)
        for chunk_text_val, emb in zip(chunks, embeddings):
            db.add(KnowledgeChunk(
                document_id=document.id,
                source_document=filename,
                source_type=SourceType.policy,
                text=chunk_text_val,
                embedding=emb,
            ))
        db.commit()

    # -----------------------------------------------------------------------
    # Past Q&A pairs
    # -----------------------------------------------------------------------
    print("Creating past Q&A knowledge base…")

    qa_doc = Document(
        filename="Acme Corp — Past Questionnaire Answers.xlsx",
        file_type=FileType.xlsx,
        chunk_count=len(QA_PAIRS),
        org_id=org_id,
    )
    db.add(qa_doc)
    db.flush()

    qa_texts = [f"Q: {q}\nA: {a}" for q, a in QA_PAIRS]
    print(f"   Embedding {len(qa_texts)} Q&A pairs in batches…")
    embeddings = await provider.embed(qa_texts)

    for (question, answer), emb in zip(QA_PAIRS, embeddings):
        db.add(KnowledgeChunk(
            document_id=qa_doc.id,
            source_document=qa_doc.filename,
            source_type=SourceType.past_answer,
            text=f"Q: {question}\nA: {answer}",
            embedding=emb,
        ))
    db.commit()
    print(f"   {len(QA_PAIRS)} Q&A chunks stored")

    # -----------------------------------------------------------------------
    # Sample questionnaire (MegaBank)
    # -----------------------------------------------------------------------
    print("Creating MegaBank Vendor Assessment questionnaire…")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Vendor Assessment"
    ws.append(["#", "Question", "Answer"])
    for i, q_text in enumerate(MEGABANK_QUESTIONS, 1):
        ws.append([i, q_text, ""])

    # Style header row
    from openpyxl.styles import Font, PatternFill
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="E8EAF6", end_color="E8EAF6", fill_type="solid")

    # Set column widths
    ws.column_dimensions["A"].width = 5
    ws.column_dimensions["B"].width = 70
    ws.column_dimensions["C"].width = 50

    xlsx_buf = io.BytesIO()
    wb.save(xlsx_buf)
    xlsx_bytes = xlsx_buf.getvalue()

    questionnaire = Questionnaire(
        name="MegaBank Vendor Security Assessment",
        customer_name="MegaBank Financial Group",
        source_filename="MegaBank_Vendor_Assessment_2026.xlsx",
        question_count=len(MEGABANK_QUESTIONS),
        raw_xlsx_blob=xlsx_bytes,
        answer_col_index=2,  # column C (0-based)
        org_id=org_id,
    )
    db.add(questionnaire)
    db.flush()

    for idx, q_text in enumerate(MEGABANK_QUESTIONS):
        db.add(Question(
            questionnaire_id=questionnaire.id,
            row_index=idx,
            question_text=q_text,
            status=QuestionStatus.pending,
        ))
    db.commit()

    print(f"   {len(MEGABANK_QUESTIONS)}-question questionnaire created (id={questionnaire.id})")

    from app.models import KnowledgeChunk as KC
    total_chunks = db.query(KC).filter(KC.document_id.in_(
        db.query(Document.id).filter(Document.org_id == org_id)
    )).count()
    print(f"\nSeed complete!")
    print(f"   Org:            {org.name} (id={org.id})")
    print(f"   Knowledge base: {total_chunks} chunks (3 policies + 30 Q&A pairs)")
    print(f"   Questionnaire:  '{questionnaire.name}' ({len(MEGABANK_QUESTIONS)} questions)")
    print(f"\nOpen http://localhost:5173 -> log in -> open the questionnaire -> click Generate Answers")

    db.close()


if __name__ == "__main__":
    asyncio.run(seed())
