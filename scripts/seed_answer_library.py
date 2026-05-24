#!/usr/bin/env python
"""
Seed the answer library with common Australian GRC questionnaire Q&A pairs.

Covers:
  - ASD Essential Eight (most common in AU government / enterprise)
  - Australian Privacy Act 1988 / APPs + Notifiable Data Breaches scheme
  - APRA CPS 234 (financial services)
  - ISO 27001 common controls
  - General vendor security questionnaire staples

All answers are generic (customer_name=NULL) so they benefit every client.
Skips any question_text that already exists in the workspace's library.

Usage (from project root):
    python scripts/seed_answer_library.py [workspace_id]

    workspace_id defaults to 1 if not provided.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.db import SessionLocal
from app.models import ApprovedAnswer, Document, FileType, KnowledgeChunk, SourceType, Workspace
from app.services.answer_library import detect_category
from app.services.embeddings import get_embedding_provider


# ---------------------------------------------------------------------------
# Seed data — (question, answer, short_answer)
# short_answer: "Yes" | "No" | "Partial" | "N/A" | None
# ---------------------------------------------------------------------------

SEED_QA = [

    # ── ASD Essential Eight ─────────────────────────────────────────────────

    (
        "Do you implement the ASD Essential Eight mitigation strategies?",
        "Yes, we align our security controls with the Australian Signals Directorate (ASD) Essential Eight mitigation strategies. Our implementation is assessed against the ACSC Essential Eight Maturity Model annually, with findings tracked through our information security program and reported to senior management.",
        "Yes",
    ),
    (
        "Do you enforce multi-factor authentication (MFA)?",
        "Yes, multi-factor authentication is enforced for all remote access, all cloud services, email, and privileged accounts. MFA is implemented using an authenticator app and cannot be bypassed. This aligns with the ASD Essential Eight MFA control requirements.",
        "Yes",
    ),
    (
        "How do you manage and restrict administrative privileges?",
        "Administrative privileges are granted on a least-privilege, need-to-know basis. Privileged accounts are separate from standard user accounts and are not used for web browsing or email. Privileged access is reviewed quarterly, logged, and monitored. This aligns with the ASD Essential Eight control for restricting administrative privileges.",
        "Yes",
    ),
    (
        "Do you implement application control or application whitelisting?",
        "Yes, application control is implemented to prevent execution of unapproved or untrusted applications. Only approved, business-required applications are permitted to run on our systems. The approved application list is reviewed and maintained as part of our change management process, aligning with the ASD Essential Eight application control requirement.",
        "Yes",
    ),
    (
        "How do you manage patching for applications and operating systems?",
        "We follow ASD Essential Eight patching timelines: critical vulnerabilities in internet-facing systems are patched within 48 hours, and all other vulnerabilities are patched within 30 days of release. Patch compliance is monitored monthly. Unpatched systems are escalated for remediation with defined accountability.",
        "Yes",
    ),
    (
        "Do you restrict Microsoft Office macros?",
        "Yes, Microsoft Office macros are disabled by default for all users. Macros are only permitted where they are digitally signed by a trusted publisher and have been formally approved through our change management process. This aligns with the ASD Essential Eight macro restriction control.",
        "Yes",
    ),
    (
        "Do you apply user application hardening?",
        "Yes, we apply user application hardening to reduce attack surface. This includes disabling unnecessary browser plugins, preventing Java from running from the internet in web browsers, blocking access to malicious websites via DNS filtering and web proxy, and ensuring PDF readers and browsers are configured securely. Controls align with the ASD Essential Eight.",
        "Yes",
    ),
    (
        "Do you perform regular backups and test recoverability?",
        "Yes, daily backups are performed for all critical data and systems. Backups are encrypted, stored in a location separate from production systems, and tested quarterly to verify successful restoration. Recovery time and recovery point objectives are defined in our business continuity plan and validated through annual exercises.",
        "Yes",
    ),

    # ── Australian Privacy Act / APPs / NDB ─────────────────────────────────

    (
        "Do you comply with the Australian Privacy Act 1988?",
        "Yes, we are bound by and comply with the Australian Privacy Act 1988 and all 13 Australian Privacy Principles (APPs). Our Privacy Policy is publicly available and outlines how we collect, use, disclose, and protect personal information in accordance with APP requirements. Our Privacy Officer oversees ongoing compliance.",
        "Yes",
    ),
    (
        "Do you have a Privacy Policy?",
        "Yes, we maintain a current Privacy Policy that is publicly accessible on our website. It outlines how we collect, store, use, and disclose personal information in accordance with the Australian Privacy Act 1988 and the Australian Privacy Principles. The policy is reviewed annually and updated as required.",
        "Yes",
    ),
    (
        "Do you have a designated Privacy Officer?",
        "Yes, we have a designated Privacy Officer responsible for overseeing compliance with the Australian Privacy Act, handling privacy enquiries and complaints, and maintaining our privacy program. The Privacy Officer's contact details are available in our Privacy Policy.",
        "Yes",
    ),
    (
        "How do you handle data breaches under the Notifiable Data Breaches scheme?",
        "We maintain a Data Breach Response Plan aligned with the Notifiable Data Breaches (NDB) scheme under the Privacy Act 1988. In the event of a suspected eligible data breach, we conduct a prompt assessment — within 30 days — and notify the Office of the Australian Information Commissioner (OAIC) and affected individuals where required. Suspected breaches are escalated immediately to our Privacy Officer.",
        "Yes",
    ),
    (
        "Is data stored in Australia?",
        "Yes, data is stored in data centres located in Australia. We do not transfer or store personal information outside Australia without ensuring equivalent privacy protections are in place, consistent with APP 8 (cross-border disclosure of personal information) requirements.",
        "Yes",
    ),
    (
        "Do you transfer personal data overseas?",
        "We do not routinely transfer personal information overseas. Where overseas transfers are necessary, we take reasonable steps to ensure the overseas recipient handles the information in accordance with the Australian Privacy Principles, consistent with our obligations under APP 8.",
        "No",
    ),
    (
        "What is your data retention policy?",
        "Personal information is retained only for as long as it is required for the purpose for which it was collected, or as required by applicable law. Our data retention schedule defines specific retention periods by data category. At the end of the retention period, data is securely destroyed or de-identified in accordance with our data destruction procedures.",
        "Yes",
    ),
    (
        "How do you handle individuals' requests to access or correct their personal information?",
        "We have a documented process for handling access and correction requests in accordance with APP 12 and APP 13. Individuals can submit requests to our Privacy Officer. We respond within 30 days, and where we are unable to provide access or make a correction, we provide reasons in writing as required by the Privacy Act.",
        "Yes",
    ),

    # ── APRA CPS 234 ────────────────────────────────────────────────────────

    (
        "Do you comply with APRA Prudential Standard CPS 234?",
        "Yes, we maintain an information security capability aligned with APRA Prudential Standard CPS 234 (Information Security). Our security controls are commensurate with the size and extent of threats to our information assets. We conduct annual independent assessments of our security controls and notify APRA of material information security incidents within the required timeframes.",
        "Yes",
    ),
    (
        "Do you have an information security policy framework aligned with APRA requirements?",
        "Yes, our information security policy framework is designed to meet APRA's prudential requirements including CPS 234. The framework is approved by the Board, reviewed annually, and covers all aspects of information security including asset management, access control, incident management, and third-party risk management.",
        "Yes",
    ),
    (
        "How do you notify regulators of material security incidents?",
        "We maintain a regulatory notification matrix defining our obligations to notify APRA, the OAIC, and other regulators in the event of a material security incident or eligible data breach. Notification procedures are documented in our Incident Response Plan, with defined escalation paths and timeframes. Material incidents are notified to APRA within 72 hours as required under CPS 234.",
        "Yes",
    ),
    (
        "Do you conduct independent security assessments?",
        "Yes, we engage independent third-party security specialists to conduct assessments of our information security controls at least annually. Assessment findings are reported to senior management and the Board, and remediation plans are tracked to completion. This satisfies the APRA CPS 234 requirement for independent assessments.",
        "Yes",
    ),

    # ── ISO 27001 ────────────────────────────────────────────────────────────

    (
        "Are you ISO 27001 certified?",
        "Yes, we maintain ISO 27001 certification for our information security management system. Our certification is issued by an accredited certification body and is subject to annual surveillance audits and triennial recertification audits. A copy of our current certificate is available on request.",
        "Yes",
    ),
    (
        "Do you have a formal Information Security Management System (ISMS)?",
        "Yes, we operate a formal Information Security Management System (ISMS) aligned with ISO/IEC 27001. The ISMS covers all core business operations, defines our security policies, risk management approach, and controls, and is subject to regular internal audits and annual external certification audits.",
        "Yes",
    ),
    (
        "How do you manage information security risks?",
        "We maintain a formal risk register and conduct information security risk assessments at least annually and following significant changes to our environment. Risks are evaluated using a likelihood and impact matrix. Treatment plans are assigned, tracked, and reviewed by senior management quarterly. Our approach aligns with ISO 27001 and ISO 31000.",
        "Yes",
    ),
    (
        "How do you handle security incidents?",
        "We maintain a documented Incident Response Plan that defines roles, escalation procedures, containment steps, and communication protocols for security incidents. All incidents are logged, classified by severity, investigated, and resolved within defined timeframes. Post-incident reviews are conducted for significant incidents to drive continual improvement.",
        "Yes",
    ),
    (
        "Do you conduct penetration testing?",
        "Yes, we engage independent third-party security specialists to conduct penetration testing at least annually, and additionally following significant changes to our infrastructure or applications. Findings are risk-rated, tracked in our vulnerability management system, and remediated within timeframes defined by severity.",
        "Yes",
    ),
    (
        "How do you manage third-party and vendor security risk?",
        "We conduct security assessments of all third-party vendors prior to engagement, with enhanced due diligence for vendors handling sensitive data or providing critical services. Assessments include review of security certifications, questionnaires, and contractual security requirements. High-risk vendors are subject to annual reassessment. Our vendor management process aligns with ISO 27001 Annex A controls.",
        "Yes",
    ),
    (
        "Do you have a business continuity plan and disaster recovery plan?",
        "Yes, we maintain a Business Continuity Plan (BCP) and Disaster Recovery Plan (DRP) that are reviewed and tested at least annually. The plans define recovery time objectives (RTOs) and recovery point objectives (RPOs) for critical systems. Plans are validated through tabletop exercises and technical failover tests, with findings used to drive continuous improvement.",
        "Yes",
    ),
    (
        "How do you manage access control to systems and data?",
        "Access to systems and data is granted on a least-privilege, need-to-know basis following a formal request and approval process. Access rights are reviewed quarterly and revoked promptly upon role changes or termination. We enforce strong authentication and multi-factor authentication for remote and privileged access. Access controls align with ISO 27001 Annex A.9.",
        "Yes",
    ),
    (
        "How do you handle employee information security training and awareness?",
        "All employees receive mandatory information security awareness training upon joining and at least annually thereafter. Training covers phishing awareness, data handling, password hygiene, acceptable use, and incident reporting procedures. Completion is tracked, and we conduct simulated phishing exercises to measure and continuously improve security awareness.",
        "Yes",
    ),
    (
        "Do you have a vulnerability management program?",
        "Yes, we operate a formal vulnerability management program. Systems are scanned for vulnerabilities at least monthly using automated tools. Identified vulnerabilities are risk-rated and remediated within defined timeframes: critical within 48 hours, high within 30 days, and medium within 90 days. Remediation progress is tracked and reported to management.",
        "Yes",
    ),
    (
        "How do you protect data in transit and at rest?",
        "Data in transit is encrypted using TLS 1.2 or higher for all communications. Data at rest is encrypted using AES-256. Encryption keys are managed securely, stored separately from the encrypted data, and rotated on a defined schedule. Our encryption standards are reviewed annually to ensure they remain current.",
        "Yes",
    ),
    (
        "Do you have a formal change management process?",
        "Yes, all changes to production systems and infrastructure follow a formal change management process. Changes are categorised by risk level, reviewed and approved by appropriate stakeholders, tested in non-production environments prior to deployment, and documented with rollback procedures. Emergency changes follow an expedited approval process with mandatory post-implementation review.",
        "Yes",
    ),
    (
        "Do you have a formal information security policy?",
        "Yes, we maintain a comprehensive Information Security Policy approved by senior management and reviewed at least annually. The policy sets out our security objectives, roles and responsibilities, and minimum security requirements. It is communicated to all employees upon joining and following material updates. Supporting policies address specific domains including access control, data classification, incident management, and acceptable use.",
        "Yes",
    ),

    # ── General vendor security staples ─────────────────────────────────────

    (
        "Do you conduct background checks on employees?",
        "Yes, pre-employment background checks are conducted for all new employees. Checks include identity verification, right-to-work verification, and criminal history checks where permitted by law and relevant to the role. Contractors and third parties with access to sensitive systems are subject to equivalent screening requirements.",
        "Yes",
    ),
    (
        "How do you classify and handle sensitive data?",
        "We maintain a data classification policy with defined tiers (e.g. Public, Internal, Confidential, Restricted). Each classification tier has associated handling requirements covering storage, transmission, access, and disposal. Employees are trained on data classification requirements, and technical controls enforce protections for higher classification tiers.",
        "Yes",
    ),
    (
        "How do you secure remote access to your systems?",
        "Remote access is provided exclusively through encrypted VPN or equivalent secure access solutions. Multi-factor authentication is required for all remote access sessions. Remote sessions are logged and monitored. Devices used for remote access must meet minimum security standards defined in our endpoint security policy.",
        "Yes",
    ),
    (
        "Do your vendor contracts include information security requirements?",
        "Yes, all vendors with access to our systems or data are required to sign agreements that include specific information security requirements. These include data handling obligations, breach notification timelines (within 72 hours), right-to-audit clauses, and requirements to comply with applicable laws including the Australian Privacy Act.",
        "Yes",
    ),
    (
        "Do you have cyber liability insurance?",
        "Yes, we maintain cyber liability insurance coverage appropriate to the nature and scale of our operations. Coverage includes first-party and third-party cyber incidents including data breaches, ransomware events, and business interruption. Further details are available on request under a non-disclosure agreement.",
        "Yes",
    ),
    (
        "Have you experienced a data breach in the last 3 years?",
        "We have not experienced an eligible data breach requiring notification to the Office of the Australian Information Commissioner (OAIC) under the Notifiable Data Breaches scheme. We conduct regular security assessments and maintain active security monitoring to detect and respond to potential incidents promptly.",
        "No",
    ),
    (
        "Do you have a formal asset management process?",
        "Yes, we maintain an asset register covering all hardware, software, and information assets. Assets are assigned to owners responsible for their security, maintenance, and disposal. The register is reviewed at least annually and updated as assets are added, changed, or decommissioned.",
        "Yes",
    ),
    (
        "How do you manage passwords and credential security?",
        "We enforce a password policy requiring minimum length, complexity, and regular rotation for privileged accounts. Password managers are used to generate and store strong, unique credentials. Default passwords are changed before deployment. Multi-factor authentication supplements password controls for all remote and privileged access.",
        "Yes",
    ),
    (
        "Do you have a SOC 2 report?",
        "We do not currently hold a SOC 2 Type II report. We are ISO 27001 certified, which provides comparable independent assurance of our information security controls through annual surveillance audits by an accredited certification body. Our ISO 27001 certificate and audit summary are available on request under NDA.",
        "No",
    ),
    (
        "How do you manage security for software development?",
        "Our software development lifecycle (SDLC) incorporates security at every stage. This includes threat modelling during design, static and dynamic application security testing (SAST/DAST) during development, peer code reviews, dependency vulnerability scanning, and penetration testing prior to major releases. Developers receive annual secure coding training.",
        "Yes",
    ),
    (
        "Do you have network segmentation and firewall controls?",
        "Yes, our network is segmented to limit lateral movement in the event of a compromise. Firewalls and network access control lists enforce traffic restrictions between segments. Internet-facing systems are isolated in a DMZ. Network traffic is monitored for anomalous behaviour using intrusion detection systems.",
        "Yes",
    ),
    (
        "How do you manage security logging and monitoring?",
        "We maintain centralised security logging across all critical systems and network infrastructure. Logs are retained for a minimum of 12 months. Automated alerting is configured for high-priority security events. Logs are reviewed regularly, and our monitoring capability includes detection of anomalous authentication, access, and network activity.",
        "Yes",
    ),
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main(workspace_id: int) -> None:
    db = SessionLocal()
    try:
        ws = db.get(Workspace, workspace_id)
        if not ws:
            print(f"Workspace {workspace_id} not found.")
            return

        print(f"Seeding answer library for workspace: {ws.name} (id={workspace_id})")

        provider = get_embedding_provider()

        # Get or create the "Approved Answers" document that chunks are attached to
        doc = db.query(Document).filter(
            Document.filename == "Approved Answers",
            Document.workspace_id == workspace_id,
        ).first()
        if not doc:
            doc = Document(
                filename="Approved Answers",
                file_type=FileType.xlsx,
                chunk_count=0,
                workspace_id=workspace_id,
            )
            db.add(doc)
            db.flush()

        # Batch embed all question texts (for ApprovedAnswer similarity search)
        questions = [q for q, _, _ in SEED_QA]
        print(f"Embedding {len(questions)} questions…")
        q_embeddings = await provider.embed(questions, input_type="query")

        # Batch embed all chunk texts (Q+A format, for retrieval)
        chunk_texts = [f"Q: {q}\nA: {a}" for q, a, _ in SEED_QA]
        chunk_ctx = [f"Document: Approved Answers\n{t}" for t in chunk_texts]
        print(f"Embedding {len(chunk_ctx)} chunks…")
        chunk_embeddings = await provider.embed(chunk_ctx)

        inserted = 0
        skipped = 0

        for (question_text, answer_text, short_answer), q_emb, chunk_text, chunk_emb in zip(
            SEED_QA, q_embeddings, chunk_texts, chunk_embeddings
        ):
            # Skip if already exists in this workspace
            exists = db.execute(
                select(ApprovedAnswer.id).where(
                    ApprovedAnswer.workspace_id == workspace_id,
                    ApprovedAnswer.question_text == question_text,
                ).limit(1)
            ).scalar_one_or_none()

            if exists:
                skipped += 1
                continue

            # Create the KnowledgeChunk so the retriever can find it
            chunk = KnowledgeChunk(
                document_id=doc.id,
                source_document="Approved Answers",
                source_section="Seeded",
                source_type=SourceType.approved_answer,
                text=chunk_text,
                embedding=chunk_emb,
                customer_name=None,  # generic
            )
            db.add(chunk)
            db.flush()

            db.add(ApprovedAnswer(
                question_text=question_text,
                answer_text=answer_text,
                short_answer=short_answer,
                answer_category=detect_category(question_text),
                cited_chunk_ids=None,
                confidence_score=0.85,
                embedding=q_emb,
                source_question_id=None,
                workspace_id=workspace_id,
                customer_name=None,
                status="active",
                times_reused=0,
                is_stale=False,
            ))
            doc.chunk_count = (doc.chunk_count or 0) + 1
            inserted += 1

        db.commit()
        print(f"Done — {inserted} answers inserted, {skipped} already existed.")

    finally:
        db.close()


if __name__ == "__main__":
    wid = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    asyncio.run(main(wid))
