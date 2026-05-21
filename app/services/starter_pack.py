"""Starter pack: seeds 20 SOC 2 / ISO 27001 policy documents for new orgs.

Called as a FastAPI background task immediately after a new Organization is created.
Each policy is embedded and stored as KnowledgeChunks so the AI can answer
questionnaire questions from day one, before the customer uploads anything.
"""

from __future__ import annotations

STARTER_POLICIES: list[dict] = [
    {
        "filename": "[Starter] Access Control Policy.txt",
        "section": "Access Control",
        "content": """POL-001 Access Control Policy
Version: 1.0 | Owner: CISO | Classification: Internal

PURPOSE
This policy establishes requirements for controlling access to information systems, applications, and data to ensure that only authorized individuals can access resources appropriate to their role.

SCOPE
Applies to all employees, contractors, consultants, and third-party users who access company systems or data.

POLICY STATEMENTS
Access Provisioning: All access requests must be submitted through the formal access request process and approved by the resource owner and HR before credentials are issued. Access is granted on the principle of least privilege — users receive only the minimum permissions required to perform their job function.

Role-Based Access Control (RBAC): Access rights are assigned based on job roles. Role definitions are maintained in the identity management system and reviewed annually. Privileged roles (administrator, root, super-user) require additional justification and senior management approval.

Multi-Factor Authentication (MFA): MFA is mandatory for all remote access, all cloud-based services, all administrative accounts, and any system storing sensitive or regulated data. Acceptable MFA methods include hardware tokens, authenticator apps (TOTP), and biometrics. SMS-based MFA is permitted only as a fallback where stronger methods are unavailable.

Single Sign-On (SSO): The organization uses a centralized Identity Provider (IdP) for SSO. Direct credential-based logins to individual applications are prohibited unless the application does not support SSO integration.

Privileged Access Management: Privileged accounts must not be used for day-to-day activities. Privileged sessions are recorded and retained for 90 days. Just-in-time (JIT) access is used where possible. Shared administrative accounts are prohibited.

Access Reviews: Quarterly access reviews are conducted for all privileged accounts. Annual reviews are conducted for all standard accounts. Access for terminated employees is revoked within 24 hours of termination. Access for employees who change roles is updated within 5 business days.

Password Requirements: Minimum length of 12 characters. Must include uppercase, lowercase, numbers, and special characters. Passwords must not be reused within the last 12 cycles. Passwords must not be shared. Accounts are locked after 5 consecutive failed login attempts.

Remote Access: Remote access to internal systems requires VPN with MFA. Personal devices used for remote work must have endpoint protection software installed. Split tunneling is disabled for VPN connections.

ROLES AND RESPONSIBILITIES
IT Security: Maintains identity management systems, conducts access reviews, monitors for unauthorized access attempts.
Managers: Approve access requests for their team members, notify IT immediately when staff leave or change roles.
All Users: Responsible for keeping credentials secure, not sharing access, and reporting suspected unauthorized access.

COMPLIANCE
Violations of this policy may result in disciplinary action up to and including termination. Access may be revoked immediately upon suspected violation pending investigation.

RELATED STANDARDS
SOC 2 CC6.1, CC6.2, CC6.3 | ISO 27001 A.9 | NIST SP 800-53 AC family
""",
    },
    {
        "filename": "[Starter] Data Encryption Policy.txt",
        "section": "Data Encryption",
        "content": """POL-002 Data Encryption Policy
Version: 1.0 | Owner: CISO | Classification: Internal

PURPOSE
This policy defines requirements for encrypting data at rest and in transit to protect confidentiality and integrity of sensitive information.

SCOPE
Applies to all company data, systems, applications, and communication channels, including cloud-hosted infrastructure and employee endpoints.

POLICY STATEMENTS
Encryption at Rest: All databases storing sensitive, confidential, or regulated data must use AES-256 encryption. Full-disk encryption (FDE) is mandatory on all laptops, workstations, and mobile devices using BitLocker, FileVault, or equivalent. Cloud storage buckets and object stores containing customer or company data must have server-side encryption enabled. Database backups must be encrypted using the same standard as the primary database.

Encryption in Transit: TLS 1.2 or higher is required for all data transmitted over public networks. TLS 1.3 is preferred. TLS 1.0 and 1.1 are prohibited. HTTPS is mandatory for all web-facing applications. Unencrypted protocols (HTTP, FTP, Telnet, plain SMTP) are prohibited for transmitting sensitive data. Internal service-to-service communication within the production environment must use mutual TLS (mTLS) or equivalent.

Key Management: Encryption keys must be stored separately from the data they protect. Keys must be rotated at least annually and upon any suspicion of compromise. Access to encryption keys is restricted to authorized personnel and services only. Hardware Security Modules (HSMs) or cloud KMS services (AWS KMS, Azure Key Vault, GCP KMS) must be used for production key management. Key rotation logs must be maintained and reviewed quarterly.

Certificate Management: TLS certificates must be issued by a trusted Certificate Authority. Self-signed certificates are prohibited in production environments. Certificate expiry must be monitored with automated renewal where possible. Wildcard certificates require CISO approval.

Prohibited Practices: MD5 and SHA-1 must not be used for cryptographic purposes. DES, 3DES, RC4, and export-grade ciphers are prohibited. Custom or proprietary cryptographic algorithms must not be used.

End-to-End Encryption: Customer-facing features that transmit personal data must implement end-to-end encryption where technically feasible. Encryption implementation must be reviewed by the security team before production deployment.

ROLES AND RESPONSIBILITIES
Engineering: Implements encryption controls in all systems and applications. Responsible for key rotation schedules.
IT Operations: Manages FDE on endpoints, certificate lifecycle management.
CISO: Approves exceptions, oversees cryptographic standard updates.

COMPLIANCE
Non-compliant systems must be remediated within 30 days of discovery. Critical findings require immediate escalation to the CISO.

RELATED STANDARDS
SOC 2 CC9.9 | ISO 27001 A.10 | NIST SP 800-111 | PCI DSS Req 3–4
""",
    },
    {
        "filename": "[Starter] Incident Response Policy.txt",
        "section": "Incident Response",
        "content": """POL-003 Incident Response Policy
Version: 1.0 | Owner: CISO | Classification: Internal

PURPOSE
This policy defines the process for detecting, reporting, triaging, containing, eradicating, and recovering from security incidents to minimize business impact and fulfill legal notification obligations.

SCOPE
Applies to all security events affecting company systems, data, infrastructure, or personnel, including cloud environments and third-party hosted services.

POLICY STATEMENTS
Incident Classification:
- P1 (Critical): Active breach, ransomware, unauthorized data exfiltration, system compromise affecting production. Response within 1 hour.
- P2 (High): Suspected breach, significant malware infection, unauthorized privileged access. Response within 4 hours.
- P3 (Medium): Policy violation, phishing attempt, suspicious activity. Response within 24 hours.
- P4 (Low): Minor policy violation, failed attack attempt, false positive. Response within 5 business days.

Detection and Reporting: All employees must report suspected security incidents immediately to security@company.com or the security hotline. Automated detection via SIEM, EDR, and IDS/IPS tools is monitored 24/7. Employees must not attempt to investigate or remediate incidents themselves.

Incident Response Team: The Incident Response Team (IRT) consists of the CISO (Incident Commander), Security Engineer (Lead Analyst), Legal Counsel, and Communications Lead. Additional members are added based on incident type.

Response Phases:
1. Identification: Confirm the incident, determine scope, assign severity.
2. Containment: Isolate affected systems, revoke compromised credentials, block malicious IPs.
3. Eradication: Remove malware, patch vulnerabilities, eliminate root cause.
4. Recovery: Restore systems from clean backups, validate integrity, return to normal operations.
5. Post-Incident Review: Conduct within 5 business days. Document timeline, root cause, lessons learned, remediation actions.

Breach Notification: For incidents involving personal data, the legal team must be notified within 1 hour. GDPR notification to supervisory authority within 72 hours if required. US state law notifications (CCPA, NY SHIELD, etc.) within required timeframes. Customers affected by a breach will be notified within the timeframe required by applicable law, contract, or as soon as reasonably practicable.

Evidence Preservation: Logs and forensic evidence must be preserved for at least 12 months. Chain of custody must be documented. No affected systems may be wiped or rebuilt until evidence is collected and approved by CISO.

Communication: External communication about security incidents must be approved by Legal and Communications. Employees must not discuss active incidents on social media or with the press.

ROLES AND RESPONSIBILITIES
All Employees: Report incidents immediately, cooperate with IRT investigations.
Security Team: Leads detection, containment, eradication, and recovery activities.
Legal: Advises on notification obligations, manages regulatory communications.
CISO: Final decision authority on incident classification and public disclosure.

RELATED STANDARDS
SOC 2 CC7.3, CC7.4, CC7.5 | ISO 27001 A.16 | NIST SP 800-61
""",
    },
    {
        "filename": "[Starter] Business Continuity Policy.txt",
        "section": "Business Continuity",
        "content": """POL-004 Business Continuity Policy
Version: 1.0 | Owner: COO | Classification: Internal

PURPOSE
This policy ensures the organization can continue critical business operations and recover from disruptive events in a timely, controlled manner.

SCOPE
Applies to all critical business functions, systems, and processes including IT infrastructure, customer-facing services, and internal operations.

POLICY STATEMENTS
Business Impact Analysis (BIA): A BIA must be conducted annually to identify critical business functions, dependencies, and recovery priorities. The BIA output defines Recovery Time Objectives (RTO) and Recovery Point Objectives (RPO) for each critical system.

Recovery Objectives:
- Tier 1 (Customer-facing production systems): RTO 4 hours, RPO 1 hour.
- Tier 2 (Internal business systems): RTO 24 hours, RPO 4 hours.
- Tier 3 (Non-critical systems): RTO 72 hours, RPO 24 hours.

Business Continuity Plan (BCP): A documented BCP must exist for each critical business function. BCPs must include activation criteria, escalation contacts, step-by-step recovery procedures, alternative work arrangements, and communication templates. BCPs must be reviewed and updated annually and after any major organizational or infrastructure change.

Disaster Recovery (DR): A Disaster Recovery Plan (DRP) documents technical recovery procedures for all Tier 1 and Tier 2 systems. DR infrastructure must be maintained in a geographically separate region. Automated failover must be configured for Tier 1 systems where technically feasible.

Testing: BCP and DRP must be tested at least annually. Tests may include tabletop exercises, partial failover tests, or full DR exercises. Test results, gaps identified, and remediation actions must be documented. Critical gaps must be remediated within 90 days.

Third-Party Dependencies: Key third-party service providers must provide evidence of their own BCP/DR capabilities annually. Single points of failure from third-party dependencies must be identified and mitigated.

Crisis Communication: An emergency contact list must be maintained and tested quarterly. Communication procedures for employees, customers, and regulators must be included in the BCP. A designated spokesperson must be assigned for external communications.

ROLES AND RESPONSIBILITIES
COO: Overall ownership of BCP, approves activation of DR procedures.
IT Operations: Maintains DR infrastructure, executes technical recovery procedures.
Business Unit Leads: Maintain departmental BCPs, conduct staff training.
All Employees: Familiar with evacuation procedures and reporting escalation paths.

RELATED STANDARDS
SOC 2 A1.2, A1.3 | ISO 27001 A.17 | ISO 22301
""",
    },
    {
        "filename": "[Starter] Vendor Risk Management Policy.txt",
        "section": "Vendor Risk",
        "content": """POL-005 Vendor Risk Management Policy
Version: 1.0 | Owner: CISO | Classification: Internal

PURPOSE
This policy establishes requirements for assessing and managing security risks introduced by third-party vendors, subprocessors, and service providers who access, process, or store company or customer data.

SCOPE
Applies to all third-party vendors, cloud service providers, subprocessors, contractors, and consultants who are given access to company systems or data, or who process personal data on the company's behalf.

POLICY STATEMENTS
Vendor Classification: Vendors are classified by risk tier based on data access and criticality.
- Tier 1 (Critical): Access to personal data, production systems, or financial data. Highest scrutiny.
- Tier 2 (High): Access to internal systems or non-public business data.
- Tier 3 (Standard): No data access; provides standard commercial services.

Pre-Engagement Due Diligence: Before engaging a Tier 1 or Tier 2 vendor, the security team must conduct a security assessment including review of SOC 2 Type II report or ISO 27001 certificate, completion of vendor security questionnaire, review of data processing agreement (DPA) and privacy policy, and assessment of subprocessor chain.

Contractual Requirements: All vendors with data access must sign a Data Processing Agreement (DPA) before processing begins. Contracts must include security obligations, breach notification timelines (maximum 72 hours), right to audit, and data return/deletion requirements upon contract termination.

Ongoing Monitoring: Tier 1 vendors must provide updated SOC 2 Type II reports annually. Significant security incidents at vendors must be reported to the company within 24 hours. Vendor risk assessments must be refreshed annually or upon material change to the vendor's service.

Subprocessors: The company maintains a public register of subprocessors. Customers will be notified of new subprocessors with a minimum of 30 days' notice (where contractually required). Subprocessors must meet the same data protection standards as the company.

Access Termination: Vendor access must be revoked within 24 hours of contract termination. Vendors must certify destruction or return of all company data within 30 days of termination.

Fourth-Party Risk: Tier 1 vendors must disclose their own critical subprocessors. Known fourth-party concentrations (multiple Tier 1 vendors relying on the same provider) must be assessed for systemic risk.

ROLES AND RESPONSIBILITIES
Procurement: Initiates vendor onboarding, ensures DPAs are signed before work begins.
Security: Conducts risk assessments, maintains vendor risk register.
Legal: Reviews and approves vendor contracts and DPAs.
Business Owners: Responsible for ongoing vendor relationship and monitoring SLAs.

RELATED STANDARDS
SOC 2 CC9.2 | ISO 27001 A.15 | GDPR Art. 28
""",
    },
    {
        "filename": "[Starter] Audit Logging Policy.txt",
        "section": "Audit & Logging",
        "content": """POL-006 Audit Logging and Monitoring Policy
Version: 1.0 | Owner: CISO | Classification: Internal

PURPOSE
This policy defines requirements for capturing, retaining, and monitoring security-relevant logs to support incident detection, forensic investigation, and compliance.

SCOPE
Applies to all production systems, cloud infrastructure, network devices, applications, and identity management systems.

POLICY STATEMENTS
Log Collection Requirements: All systems must generate audit logs capturing at minimum: user authentication (success and failure), privileged access activity, data access and modification events, system configuration changes, network connections (inbound and outbound to sensitive systems), and security tool alerts. Logs must include a timestamp (UTC), source IP, user identity, action taken, and outcome.

Log Integrity: Logs must be forwarded to a centralized SIEM system within 5 minutes of generation. Local log modification must be prevented through write-once log storage or forwarding to an immutable log sink. Log tampering or deletion must trigger an immediate alert.

Retention: Security logs must be retained for a minimum of 12 months, with 3 months in hot storage (searchable). Logs related to security incidents must be retained for the duration of any investigation plus 3 years. Cloud trail logs (AWS CloudTrail, Azure Activity Log, GCP Audit Log) must be enabled for all environments.

SIEM and Alerting: The organization operates a SIEM platform that correlates log events and generates security alerts. Alert rules must cover: multiple failed login attempts (brute force), after-hours privileged access, access from unusual geographies, large data exports, configuration changes to security controls, and new administrative account creation. Alerts must be triaged within the SLA defined by severity: Critical within 30 minutes, High within 2 hours, Medium within 8 hours.

Monitoring Coverage: 100% of internet-facing systems must have logging enabled. All IAM events in cloud environments must be logged. Database query logs must be enabled for databases storing personal or sensitive data. API gateway access logs must be retained.

Log Review: Security engineers must review SIEM dashboards daily. Automated anomaly detection must supplement manual review. Quarterly log review audits must verify logging completeness and alert effectiveness.

Access to Logs: Log access is restricted to security personnel and auditors. Logs must not be accessible to the systems or users they are auditing. Audit log access itself must be logged.

ROLES AND RESPONSIBILITIES
Security Operations: Manages SIEM, tunes alert rules, responds to alerts, conducts log reviews.
IT Operations: Ensures all systems are configured to forward logs to SIEM.
Compliance: Verifies retention and access controls meet regulatory requirements.

RELATED STANDARDS
SOC 2 CC7.2 | ISO 27001 A.12.4 | NIST SP 800-92 | PCI DSS Req 10
""",
    },
    {
        "filename": "[Starter] Vulnerability Management Policy.txt",
        "section": "Vulnerability Mgmt",
        "content": """POL-007 Vulnerability Management Policy
Version: 1.0 | Owner: CISO | Classification: Internal

PURPOSE
This policy establishes a systematic approach to identifying, assessing, and remediating security vulnerabilities in company systems and software.

SCOPE
Applies to all production systems, cloud infrastructure, applications, network devices, endpoints, and open-source software dependencies.

POLICY STATEMENTS
Vulnerability Scanning: Authenticated vulnerability scans must run against all production infrastructure at minimum weekly. Container images must be scanned at build time and before deployment. Web application scans must run monthly and before major releases. Network perimeter scans must run from an external vantage point quarterly.

Penetration Testing: External penetration tests must be conducted at least annually by a qualified third-party vendor. Internal network penetration tests must be conducted annually. Web application penetration tests must be conducted annually and after significant feature releases. Penetration test scope, findings, and remediation status must be documented and retained for 3 years.

Severity and Remediation SLAs: Based on CVSS score and exploitability:
- Critical (CVSS 9.0–10.0): Remediate within 24 hours if exploitable, 7 days otherwise.
- High (CVSS 7.0–8.9): Remediate within 14 days.
- Medium (CVSS 4.0–6.9): Remediate within 30 days.
- Low (CVSS 0.1–3.9): Remediate within 90 days.

Patch Management: Security patches for critical and high vulnerabilities must be applied within the SLAs above. Monthly patch cycles address medium and low findings. Patch exceptions require CISO approval and a compensating control. All exceptions must be documented with a target remediation date.

Dependency Management: Software dependency inventories (SBOMs) must be maintained for all production applications. Automated dependency scanning (e.g., Dependabot, Snyk) must be enabled in all repositories. Known exploited vulnerabilities in dependencies must be addressed as Critical regardless of CVSS score.

Zero-Day and Threat Intelligence: The security team subscribes to relevant threat intelligence feeds. Critical zero-day vulnerabilities in technology the company uses trigger an emergency response following the incident response process.

Vulnerability Disclosure: The company maintains a responsible disclosure program. External researchers who report vulnerabilities in good faith will not face legal action. A CVD policy and contact email (security@company.com) must be published.

ROLES AND RESPONSIBILITIES
Security: Operates scanning tools, triages findings, tracks remediation progress.
Engineering: Remediates vulnerabilities in code and dependencies within SLAs.
IT Operations: Applies OS and infrastructure patches within SLAs.
CISO: Approves exceptions, oversees metrics and program health.

RELATED STANDARDS
SOC 2 CC7.1 | ISO 27001 A.12.6 | NIST SP 800-40 | PCI DSS Req 6
""",
    },
    {
        "filename": "[Starter] Data Privacy Policy.txt",
        "section": "Data Privacy",
        "content": """POL-008 Data Privacy Policy
Version: 1.0 | Owner: DPO | Classification: Internal

PURPOSE
This policy defines how the organization collects, uses, retains, and protects personal data to comply with applicable data protection laws including GDPR, CCPA, and other regional privacy regulations.

SCOPE
Applies to all personal data processed by the company, including employee data, customer data, and any other data relating to identifiable individuals.

DEFINITIONS
Personal Data (PII): Any information relating to an identified or identifiable natural person. Includes names, email addresses, IP addresses, location data, device identifiers, and any data that can be combined to identify an individual.
Sensitive Personal Data: Special categories under GDPR including health data, biometric data, racial/ethnic origin, religious beliefs, and financial data. Requires additional protections.

POLICY STATEMENTS
Lawful Basis for Processing: All processing of personal data must have a documented lawful basis. Permissible bases include: consent (freely given, specific, informed), contract performance, legal obligation, vital interests, legitimate interests (with documented balancing test). Consent must be recorded and must be withdrawable at any time.

Data Minimization: Only personal data strictly necessary for the stated purpose may be collected. Collecting data "just in case" it may be useful is prohibited. Data collection practices must be reviewed annually.

Purpose Limitation: Personal data collected for one purpose must not be used for incompatible purposes without new consent or legal basis.

Data Subject Rights: Individuals have the right to access their personal data (within 30 days), correction of inaccurate data, erasure ("right to be forgotten") where no legal basis for retention exists, data portability in a machine-readable format, objection to processing, and restriction of processing. A process for handling data subject requests within legally required timeframes must be maintained.

Data Retention: Personal data must not be retained longer than necessary for the original purpose. A data retention schedule must document retention periods for each data category. Data past its retention period must be securely deleted.

International Data Transfers: Personal data must not be transferred to countries outside the EEA without appropriate safeguards (Standard Contractual Clauses, Adequacy Decision, or Binding Corporate Rules). A record of international transfers must be maintained.

Privacy by Design: Privacy impact assessments (PIAs/DPIAs) must be conducted for new products, features, and processes that involve significant personal data processing. Privacy controls must be built into systems from the design stage.

ROLES AND RESPONSIBILITIES
DPO: Oversees privacy compliance, handles regulatory inquiries, reviews DPIAs.
Engineering: Implements privacy by design, data deletion mechanisms, and consent management.
All Employees: Must complete annual privacy training, report potential breaches immediately.

RELATED STANDARDS
GDPR | CCPA | ISO 27701 | SOC 2 P criteria
""",
    },
    {
        "filename": "[Starter] Network Security Policy.txt",
        "section": "Network Security",
        "content": """POL-009 Network Security Policy
Version: 1.0 | Owner: CISO | Classification: Internal

PURPOSE
This policy establishes controls for protecting the organization's network infrastructure from unauthorized access, misuse, and attack.

SCOPE
Applies to all network infrastructure including on-premises, cloud, hybrid, and remote access environments.

POLICY STATEMENTS
Network Segmentation: The network must be segmented into security zones: Internet DMZ, production, staging/test, corporate, and management networks. Inter-zone traffic must traverse firewalls with explicit allow-list rules. Direct traffic between production and corporate networks is prohibited. Micro-segmentation must be applied within cloud production environments.

Firewall Management: Perimeter firewalls must operate on a default-deny policy. All firewall rule changes require change management approval. Firewall rules must be reviewed and cleaned up quarterly. Unused rules must be removed. Internet-facing ports are restricted to 80/443 and required service-specific ports.

Intrusion Detection and Prevention: IDS/IPS must be deployed on all internet-facing network segments. Alerts must be integrated into the SIEM. IDS signatures must be updated weekly. Network traffic anomaly detection must operate in all production environments.

VPN and Remote Access: All remote access to internal systems must use an approved VPN solution with MFA. Split tunneling is disabled. VPN clients must enforce endpoint compliance checks (OS patch level, AV status) before granting access. Personal VPN usage on company devices is prohibited.

DNS Security: DNSSEC must be enabled for the company's external DNS zones. DNS-over-HTTPS (DoH) must be enforced on managed endpoints. DNS query logs must be captured and monitored for data exfiltration and C2 activity.

DDoS Protection: Internet-facing services must be fronted by a DDoS mitigation provider. Rate limiting must be configured at the API gateway and load balancer layers.

Wireless Security: Corporate Wi-Fi must use WPA3 or WPA2-Enterprise with 802.1X authentication. Guest Wi-Fi must be isolated from corporate networks. Rogue access point detection must be active in office locations. Personal hotspot usage for company work requires VPN.

Network Monitoring: Full packet capture or flow logging (NetFlow/IPFIX) must be enabled at network choke points. Lateral movement patterns, unusual data transfers, and port scanning must trigger SIEM alerts.

ROLES AND RESPONSIBILITIES
IT Operations: Manages network devices, firewall rules, VPN infrastructure.
Security: Monitors IDS/IPS, reviews firewall rules, responds to network alerts.
Engineering: Implements network security controls in cloud environments.

RELATED STANDARDS
SOC 2 CC6.6, CC6.7 | ISO 27001 A.13 | NIST SP 800-41 | CIS Controls 12–13
""",
    },
    {
        "filename": "[Starter] Physical Security Policy.txt",
        "section": "Physical Security",
        "content": """POL-010 Physical Security Policy
Version: 1.0 | Owner: COO | Classification: Internal

PURPOSE
This policy establishes controls to protect company facilities, equipment, and personnel from physical security threats.

SCOPE
Applies to all company offices, data centers, co-location facilities, and employee home offices when used for remote work.

POLICY STATEMENTS
Facility Access Control: Access to company offices requires key card or biometric authentication. Visitor access requires prior authorization, visitor badges, and escorted entry. Visitor logs must be maintained for 12 months. Tailgating through secured doors is prohibited. Access rights must be revoked within 24 hours of employee departure.

Secure Areas: Data center areas, server rooms, and network equipment rooms are designated secure areas requiring additional authorization. Two-person integrity rules apply in the most sensitive secure areas. CCTV must cover all entry/exit points to secure areas. Motion-triggered recording must be retained for 90 days.

Clear Desk and Screen Policy: Employees must not leave sensitive documents unattended at workstations. Computer screens must be locked when unattended (automatic lock after 5 minutes of inactivity is required). Passwords, keys, and access cards must be secured when not in use.

Equipment Security: All company-issued laptops and mobile devices must be tracked in the asset inventory. Equipment must not be left unattended in public places. Company equipment taken off-premises must have full-disk encryption enabled. Lost or stolen equipment must be reported within 1 hour so remote wipe can be initiated.

Hardware Disposal: Storage media (hard drives, SSDs, USB drives) must be securely wiped or physically destroyed before disposal. A certificate of destruction must be obtained from the disposal vendor. Disposal records must be retained for 5 years.

Data Center Controls: Production servers must be hosted in data centers with ISO 27001, SOC 2, or equivalent certification. Data center providers must control physical access with biometric or card authentication, maintain visitor logs, provide 24/7 security, and operate CCTV coverage. Physical access lists for co-location cages must be reviewed quarterly.

Environmental Controls: Server rooms and data centers must have temperature monitoring, humidity control, fire suppression, and UPS/generator backup. Environmental alerts must be monitored 24/7.

ROLES AND RESPONSIBILITIES
Facilities: Manages access control systems, CCTV, visitor management.
IT Operations: Manages equipment inventory, disposal procedures, remote wipe capability.
All Employees: Responsible for clear desk compliance, securing personal credentials, reporting lost equipment.

RELATED STANDARDS
SOC 2 CC6.4 | ISO 27001 A.11 | SOC 2 A1.1
""",
    },
    {
        "filename": "[Starter] Password and Authentication Policy.txt",
        "section": "Access Control",
        "content": """POL-011 Password and Authentication Policy
Version: 1.0 | Owner: CISO | Classification: Internal

PURPOSE
This policy defines minimum requirements for passwords and authentication mechanisms to protect user accounts from unauthorized access.

SCOPE
Applies to all accounts on company systems, including employee accounts, service accounts, and administrative accounts.

POLICY STATEMENTS
Password Requirements: Minimum password length is 12 characters for standard accounts and 16 characters for privileged accounts. Passwords must contain at least one uppercase letter, one lowercase letter, one number, and one special character. Passwords must not contain the user's name, email, or username. Passwords must not be dictionary words or common patterns.

Password Reuse and Rotation: Passwords must not be reused within the last 12 password changes. Routine forced periodic rotation (e.g., every 90 days) is not required unless there is evidence of compromise (following NIST SP 800-63B guidance). Passwords must be changed immediately upon known or suspected compromise. Service account passwords must be rotated annually and upon any personnel change affecting that account.

Multi-Factor Authentication: MFA is mandatory for all user accounts. Acceptable second factors include TOTP authenticator apps (Google Authenticator, Authy, Microsoft Authenticator), hardware security keys (FIDO2/WebAuthn), and push notifications from a registered device. SMS OTP is allowed only as a fallback and is discouraged. MFA must not be bypassed for any reason other than a documented emergency break-glass procedure.

Account Lockout: Standard accounts lock after 10 consecutive failed login attempts. Privileged accounts lock after 5 consecutive failed login attempts. Locked accounts require administrator unlock or a timed unlock after 30 minutes. All lockout events must be logged and monitored for brute-force patterns.

Service and System Accounts: Service accounts must use long (24+ character) randomly generated passwords or certificate-based authentication. Human-interactive login to service accounts is prohibited. Service account credentials must be stored in an approved secrets manager (HashiCorp Vault, AWS Secrets Manager, or equivalent). Hardcoded credentials in source code are prohibited.

Password Storage: User passwords must be stored using an approved one-way hashing algorithm (Argon2id preferred, bcrypt acceptable). MD5 and SHA-1 must not be used for password storage. Plaintext passwords must never be logged or transmitted.

ROLES AND RESPONSIBILITIES
IT Security: Enforces password policy through identity management systems, monitors lockout events.
All Users: Responsible for selecting strong unique passwords, not sharing credentials, using a password manager.
Engineering: Implements secure password storage in all applications.

RELATED STANDARDS
SOC 2 CC6.1 | ISO 27001 A.9.4 | NIST SP 800-63B
""",
    },
    {
        "filename": "[Starter] Change Management Policy.txt",
        "section": "General",
        "content": """POL-012 Change Management Policy
Version: 1.0 | Owner: CTO | Classification: Internal

PURPOSE
This policy ensures that changes to production systems, infrastructure, and applications are planned, tested, approved, and implemented in a controlled manner to minimize risk of service disruption or security degradation.

SCOPE
Applies to all changes to production environments including application deployments, infrastructure changes, configuration changes, firewall rule changes, and third-party integrations.

POLICY STATEMENTS
Change Categories:
- Standard Changes: Pre-approved, low-risk, routine changes with established procedures (e.g., scheduled patch deployment). No individual approval needed.
- Normal Changes: Require planning, testing, and approval before implementation. Most production deployments fall here.
- Emergency Changes: Required to resolve a critical incident. Expedited approval process. Must be documented retrospectively within 24 hours.

Change Request Process: All Normal changes must be submitted in the change management system with a description of the change, business justification, risk assessment, rollback plan, testing evidence, and scheduled maintenance window. Changes must be reviewed and approved by at least one peer (code review) and a technical lead before deployment.

Testing Requirements: All code changes must pass automated unit tests, integration tests, and security scans before deployment. Infrastructure changes must be tested in a staging environment that mirrors production. Load tests are required for changes expected to materially affect system performance.

Approval Authority: Standard changes: No approval required. Normal changes: Engineering lead or designated change approver. High-risk changes (database migrations, security controls, authentication changes): CISO sign-off required. Emergency changes: On-call incident commander with retrospective approval from engineering lead within 24 hours.

Deployment and Rollback: Deployments must use blue/green, canary, or equivalent deployment strategies for Tier 1 systems. Rollback procedures must be documented and tested before deployment. Deployments must be monitored for 30 minutes after completion. Automated rollback triggers must be configured where possible.

Security Review: Changes to authentication, authorization, cryptography, network firewall rules, and data handling code require security team review before deployment. Automated SAST and dependency scanning must be integrated into the CI/CD pipeline.

Change Freeze: Change freezes may be declared before major product launches, holidays, or at the discretion of the CTO. Only emergency changes are permitted during a freeze.

ROLES AND RESPONSIBILITIES
Engineering: Submits change requests, develops and tests changes, performs deployments.
Technical Lead: Reviews and approves Normal changes.
CISO: Approves high-risk changes with security implications.
IT Operations: Executes infrastructure and network changes.

RELATED STANDARDS
SOC 2 CC8.1 | ISO 27001 A.12.1 | ITIL Change Management
""",
    },
    {
        "filename": "[Starter] Data Retention and Disposal Policy.txt",
        "section": "Data Privacy",
        "content": """POL-013 Data Retention and Disposal Policy
Version: 1.0 | Owner: DPO | Classification: Internal

PURPOSE
This policy defines retention periods for different categories of company data and establishes requirements for the secure disposal of data and media at end of life.

SCOPE
Applies to all data created, received, or processed by the company regardless of format (digital or physical) or storage location (on-premises, cloud, employee devices).

DATA RETENTION SCHEDULE
Customer Personal Data: Retained for the duration of the customer relationship plus 3 years (or as specified in the customer contract), unless a shorter period is required by law.
Employee Personal Data: Retained for the duration of employment plus 7 years for financial records, 5 years for HR records, and 3 years for general correspondence.
Security Logs: 12 months minimum (3 months hot, 9 months cold). Logs related to security incidents: 3 years.
Financial Records: 7 years (per applicable accounting regulations).
Contracts and Legal Agreements: 10 years after expiration or termination.
Incident Response Records: 5 years.
Audit Reports and Compliance Records: 7 years.
Email: 3 years for general business email, 7 years for legally significant communications.

POLICY STATEMENTS
Retention Enforcement: Data must not be retained beyond the periods defined in this schedule. Automated deletion must be configured where technically feasible. Annual data deletion runs must be conducted to remove data past its retention period. Data subject erasure requests override standard schedules where no legal retention obligation exists.

Legal Hold: When litigation, regulatory inquiry, or investigation is anticipated, Legal may issue a Legal Hold that suspends normal deletion for affected data. Legal Holds are managed by Legal and removed only by Legal when no longer necessary.

Secure Deletion: Electronic data must be securely deleted using NIST SP 800-88 compliant methods (overwrite, cryptographic erasure, or physical destruction). Cloud data deletion must be confirmed with the provider's deletion guarantees. Certificate of destruction must be obtained for physical media.

Physical Records: Paper records containing sensitive or personal data must be cross-cut shredded (DIN 66399 Level P-4 or higher) before disposal. Shredding services must provide certificates of destruction. Confidential documents must not be placed in standard recycling bins.

Third-Party Data: Data stored with third-party vendors must be returned or deleted within 30 days of contract termination. Written confirmation of deletion must be obtained.

ROLES AND RESPONSIBILITIES
DPO: Maintains retention schedule, manages legal holds, oversees compliance.
IT Operations: Implements automated deletion, manages media disposal.
Legal: Issues and removes legal holds, reviews retention schedule annually.
All Employees: Must not retain personal or confidential data beyond policy limits on personal devices.

RELATED STANDARDS
GDPR Art. 5(1)(e), Art. 17 | SOC 2 Privacy P6 | ISO 27001 A.8.3
""",
    },
    {
        "filename": "[Starter] Risk Assessment Policy.txt",
        "section": "General",
        "content": """POL-014 Information Security Risk Assessment Policy
Version: 1.0 | Owner: CISO | Classification: Internal

PURPOSE
This policy defines the process for identifying, assessing, treating, and monitoring information security risks to protect the organization's assets and ensure compliance with applicable standards.

SCOPE
Applies to all information assets, systems, processes, and third-party relationships of the organization.

POLICY STATEMENTS
Risk Assessment Frequency: A formal organization-wide risk assessment must be conducted annually. Risk assessments must also be triggered by significant changes such as new products, major system changes, mergers/acquisitions, new regulatory requirements, or significant security incidents.

Risk Identification: Risks must be identified by considering threats (internal/external, accidental/intentional), vulnerabilities in systems and processes, potential business impacts, and likelihood of occurrence. Threat intelligence must inform risk identification.

Risk Scoring: Each identified risk is scored on two dimensions: Likelihood (1–5 scale) and Impact (1–5 scale). Risk Score = Likelihood × Impact. Risk classifications: Critical (20–25), High (10–19), Medium (4–9), Low (1–3).

Risk Treatment Options: Accept: Formally accept risks below the risk appetite threshold with documentation. Mitigate: Implement controls to reduce likelihood or impact. Transfer: Purchase cyber insurance or contractually transfer risk to a third party. Avoid: Discontinue the activity or system that creates the risk.

Risk Register: A risk register must be maintained listing all identified risks with scores, treatment decisions, control owners, remediation timelines, and review dates. The risk register must be reviewed by the CISO quarterly.

Risk Appetite: The organization's risk appetite is defined as: no more than 2 Critical risks open at any time; High risks must have active remediation plans. The Board must review and approve the risk appetite statement annually.

Residual Risk Acceptance: Risks that cannot be fully mitigated must be formally accepted by the appropriate authority based on risk score: Medium by department heads, High by CISO, Critical by CEO.

Reporting: A risk summary report must be presented to senior management quarterly and to the Board annually. Material new risks must be escalated to leadership within 5 business days of identification.

ROLES AND RESPONSIBILITIES
CISO: Owns the risk management program, maintains risk register, presents to leadership.
Department Heads: Identify risks within their domains, own remediation of assigned risks.
Internal Audit: Provides independent assurance on risk management effectiveness.

RELATED STANDARDS
SOC 2 CC3 | ISO 27001 Clause 6.1 | ISO 31000 | NIST RMF
""",
    },
    {
        "filename": "[Starter] Security Awareness Training Policy.txt",
        "section": "General",
        "content": """POL-015 Security Awareness and Training Policy
Version: 1.0 | Owner: CISO | Classification: Internal

PURPOSE
This policy ensures all personnel have the knowledge and awareness needed to protect the organization's assets and recognize security threats.

SCOPE
Applies to all employees, contractors, and temporary workers with access to company systems or data.

POLICY STATEMENTS
Mandatory Training: All employees must complete security awareness training within 30 days of hire. Annual refresher training is mandatory for all staff. Completion is tracked and reported to HR and CISO. Non-completion within deadlines results in access suspension until training is complete.

Training Content: Annual training must cover phishing and social engineering recognition, password hygiene and MFA, data classification and handling, incident reporting procedures, acceptable use of company resources, mobile device security, working remotely securely, and regulatory requirements relevant to the employee's role.

Phishing Simulations: Simulated phishing campaigns must be run at least quarterly against all employees. Click rates must be tracked. Employees who click simulated phishing links must complete remedial training within 5 business days. Trends must be reported to senior management.

Role-Based Training: Additional specialized training is required for roles with elevated security responsibilities. Software engineers must complete secure coding training annually (OWASP Top 10, injection prevention, secure authentication). Administrators must complete privileged access security training. HR staff must complete GDPR/privacy training. Finance staff must complete business email compromise (BEC) awareness training.

Incident Reporting: Employees must know how to report suspected security incidents. Reporting instructions must be included in all annual training. A no-blame culture for good-faith incident reporting must be maintained.

New Threat Awareness: When significant new threat types emerge (new phishing campaigns, zero-day vulnerabilities, social engineering tactics), targeted awareness communications must be sent to all staff within 48 hours.

Training Records: Training completion records must be maintained for 3 years. Records must be available for audit.

ROLES AND RESPONSIBILITIES
CISO: Owns training program, reviews content annually, approves vendors.
HR: Tracks completion, escalates non-compliance.
Managers: Ensure their teams complete training, report completion gaps.
All Employees: Must complete all assigned training within required timeframes.

RELATED STANDARDS
SOC 2 CC1.4, CC2.2 | ISO 27001 A.7.2.2 | NIST SP 800-50
""",
    },
    {
        "filename": "[Starter] Asset Management Policy.txt",
        "section": "General",
        "content": """POL-016 Asset Management Policy
Version: 1.0 | Owner: CTO | Classification: Internal

PURPOSE
This policy establishes requirements for identifying, classifying, and managing information assets throughout their lifecycle to ensure appropriate protection.

SCOPE
Applies to all hardware, software, data, and cloud resources owned or used by the organization.

DATA CLASSIFICATION SCHEME
Public: Information approved for public release. No restrictions on handling.
Internal: Non-sensitive business information. Share within the organization only.
Confidential: Sensitive business information, including financial data, business plans, and unpublished product information. Share on a need-to-know basis.
Restricted: Personal data, customer data, credentials, and regulated information. Strictest controls apply.

POLICY STATEMENTS
Asset Inventory: A complete asset inventory must be maintained covering all hardware assets (laptops, servers, network equipment, mobile devices), software assets (licensed applications, SaaS subscriptions, open-source libraries), cloud resources (accounts, virtual machines, storage, databases), and data assets (databases, file shares, data lakes). The inventory must be reviewed and updated quarterly.

Asset Ownership: Every asset must have a designated owner responsible for its classification, protection, and lifecycle management. Asset ownership must be reassigned within 5 business days when employees leave.

Hardware Lifecycle: New hardware must be enrolled in MDM (Mobile Device Management) before use. Hardware must be refreshed on a 4-year cycle. Decommissioned hardware must follow the data disposal process in POL-013 before being returned, donated, or destroyed.

Software Approval: Only approved software may be installed on company devices. Employees must not install unauthorized applications. A software allowlist is maintained by IT. Shadow IT must be reported and evaluated for onboarding or removal.

Cloud Resource Management: Cloud accounts must be managed through the company's master cloud organization. Personally created cloud accounts used for work are prohibited. Cloud resource tagging (owner, environment, data classification) is mandatory. Unused cloud resources must be reviewed and decommissioned monthly.

Data Classification Enforcement: Data must be classified at creation and handled according to its classification. Restricted and Confidential data must not be stored in unapproved locations (personal drives, unauthorized SaaS tools). Misclassification must be reported and corrected.

ROLES AND RESPONSIBILITIES
IT Operations: Maintains hardware inventory, MDM, software approvals.
Engineering: Maintains cloud resource and software dependency inventories.
Asset Owners: Responsible for classification, proper handling, and lifecycle decisions.
All Employees: Must report unauthorized assets or data mishandling.

RELATED STANDARDS
SOC 2 CC6.1 | ISO 27001 A.8 | CIS Controls 1–2
""",
    },
    {
        "filename": "[Starter] Backup and Recovery Policy.txt",
        "section": "Backup & Recovery",
        "content": """POL-017 Backup and Recovery Policy
Version: 1.0 | Owner: CTO | Classification: Internal

PURPOSE
This policy establishes requirements for backing up critical data and systems and validating the ability to restore them to meet recovery time and point objectives.

SCOPE
Applies to all production databases, file stores, configuration data, and critical business systems.

POLICY STATEMENTS
Backup Requirements by Tier:
- Tier 1 (Customer-facing systems, production databases): Continuous replication plus point-in-time recovery (PITR). Daily full backup, hourly incremental. Offsite/cross-region storage required. Retention: 30 days.
- Tier 2 (Internal systems, secondary databases): Daily full backup, 4-hour incremental. Offsite storage required. Retention: 14 days.
- Tier 3 (Non-critical systems): Weekly full backup. Offsite storage optional. Retention: 7 days.

Backup Storage: Backups must be stored in a geographically separate location (different region for cloud, different facility for on-premises). Backup data must be encrypted at rest using AES-256. Backup storage access must be restricted to authorized operations personnel only. Backups must not be stored on the same infrastructure as the primary data.

Recovery Testing: Backup integrity must be verified by automated restore tests weekly for Tier 1 systems. Full restore drills must be conducted quarterly for Tier 1 and semi-annually for Tier 2 systems. Restore tests must validate data integrity, application functionality, and meeting RTO/RPO targets. Test results must be documented and reviewed by the CTO.

Recovery Time Objectives (RTO) and Recovery Point Objectives (RPO):
- Tier 1: RTO 4 hours, RPO 1 hour.
- Tier 2: RTO 24 hours, RPO 4 hours.
- Tier 3: RTO 72 hours, RPO 24 hours.

Backup Monitoring: Backup job success/failure must be monitored with automated alerting. Failed backups must be investigated and resolved within 4 hours for Tier 1, 24 hours for Tier 2. No more than 2 consecutive backup failures are permitted without escalation to the CTO.

Immutable Backups: At least one backup copy per system must be stored in immutable (write-once) storage to protect against ransomware. Immutable copies must be stored for a minimum of 7 days.

ROLES AND RESPONSIBILITIES
IT Operations: Configures and monitors backup jobs, performs restore tests, maintains backup infrastructure.
Engineering: Ensures application data is included in backup scope, validates application-level integrity after restores.
CTO: Reviews quarterly restore test results, approves changes to backup strategy.

RELATED STANDARDS
SOC 2 A1.2, A1.3 | ISO 27001 A.12.3 | NIST SP 800-34
""",
    },
    {
        "filename": "[Starter] Third-Party Access Policy.txt",
        "section": "Vendor Risk",
        "content": """POL-018 Third-Party and Contractor Access Policy
Version: 1.0 | Owner: CISO | Classification: Internal

PURPOSE
This policy governs access granted to third parties including contractors, consultants, auditors, and vendors to ensure that such access is controlled, monitored, and terminated appropriately.

SCOPE
Applies to all external parties granted access to company systems, networks, or data, whether on-premises or remote.

POLICY STATEMENTS
Pre-Access Requirements: Before access is granted, the third party must sign a Non-Disclosure Agreement (NDA). For access to personal data, a Data Processing Agreement (DPA) must be signed. Third parties must acknowledge and agree to comply with relevant company security policies. Background checks are required for contractors with Restricted data access.

Access Provisioning: All third-party accounts must be requested through the standard access request process with business justification and defined end date. Third-party accounts must be separate from employee accounts and clearly identifiable (e.g., username format: vendor-name@). Third parties must not share accounts with each other or with employees. MFA is required for all third-party accounts.

Least Privilege for Third Parties: Third parties are granted the minimum access required for the contracted scope of work. Access to specific systems or data beyond the agreed scope requires a new access request and approval. Privileged access (admin rights) for contractors requires CISO approval and is time-limited.

Remote Access: Third-party remote access must use the same VPN and MFA requirements as employees. Remote sessions must be monitored and may be recorded for sensitive systems. Session recording must be disclosed to the contractor. Unmonitored remote access to production systems is prohibited.

Access Duration and Review: Third-party access must have a defined end date matching the contract period. Access must be reviewed monthly for contractors engaged for more than 30 days. Access must be revoked within 4 hours of contract termination or project completion.

Monitoring: All third-party activity on company systems must be logged. Anomalous or suspicious activity by third parties must trigger the incident response process. Third parties must not disable or interfere with monitoring systems.

Data Handling: Third parties must not copy, transmit, or retain company data beyond what is strictly required for the contracted work. Data must be returned or securely deleted upon project completion with written confirmation.

ROLES AND RESPONSIBILITIES
Procurement: Initiates access requests, ensures contracts are in place before access is granted.
IT Security: Provisions accounts, monitors access, reviews access monthly.
Contract Manager: Notifies IT immediately upon contractor offboarding.
CISO: Approves privileged access for contractors, reviews third-party access quarterly.

RELATED STANDARDS
SOC 2 CC6.2 | ISO 27001 A.15 | GDPR Art. 28
""",
    },
    {
        "filename": "[Starter] Security Monitoring Policy.txt",
        "section": "Audit & Logging",
        "content": """POL-019 Security Monitoring and Operations Policy
Version: 1.0 | Owner: CISO | Classification: Internal

PURPOSE
This policy establishes requirements for continuous security monitoring to detect, analyze, and respond to threats and anomalous activity across the organization's technology environment.

SCOPE
Applies to all production systems, network infrastructure, endpoints, cloud environments, and SaaS applications used by the organization.

POLICY STATEMENTS
Security Operations Coverage: Security monitoring must operate 24 hours a day, 7 days a week. Coverage may be provided by an in-house security team, a managed security service provider (MSSP), or a combination. On-call procedures must ensure that Critical and High alerts are responded to within defined SLAs at all times including nights, weekends, and holidays.

Detection Coverage Requirements: Monitoring must cover: endpoint detection and response (EDR) on all managed devices, network intrusion detection at all perimeter points, cloud security posture management (CSPM) for all cloud accounts, identity and access management events (all authentication, privilege escalation, account changes), email security gateway (phishing, malware, BEC), and application-layer monitoring (WAF, API abuse, error rate spikes).

Alert Management: Alerts are classified by severity: Critical (active attack or confirmed compromise), High (strong indicators of attack), Medium (suspicious activity requiring investigation), Low (informational, policy violation). Response SLAs: Critical within 15 minutes, High within 1 hour, Medium within 8 hours, Low within 5 business days. Alert fatigue must be managed by tuning rules quarterly to maintain a false-positive rate below 20%.

Threat Intelligence Integration: The security team must subscribe to at least two threat intelligence feeds. Indicators of Compromise (IOCs) must be automatically ingested into SIEM and blocking controls. Threat intelligence must inform alert rule updates and hunting activities.

Threat Hunting: Proactive threat hunting exercises must be conducted at least quarterly to search for threats that evade automated detection. Hunting hypotheses must be documented with findings and any identified gaps remediated.

Metrics and Reporting: Monthly security operations metrics must be reported to the CISO including: alert volume by severity, mean time to detect (MTTD), mean time to respond (MTTR), number of confirmed incidents, false positive rate, and SLA compliance. Metrics are presented to senior management quarterly.

Tool Maintenance: Security tools (EDR, SIEM, IDS, WAF, CSPM) must be kept up to date with vendor releases. Tool health must be monitored. Gaps in coverage identified by monitoring health checks must be remediated within 30 days.

ROLES AND RESPONSIBILITIES
Security Operations: Monitors alerts, investigates incidents, maintains tools, produces metrics.
IT Operations: Ensures endpoint agents and network taps are deployed and functioning.
CISO: Reviews metrics, approves tool changes, manages MSSP relationship if applicable.

RELATED STANDARDS
SOC 2 CC7.2, CC7.3 | ISO 27001 A.12.4, A.16 | NIST SP 800-137
""",
    },
    {
        "filename": "[Starter] Acceptable Use Policy.txt",
        "section": "General",
        "content": """POL-020 Acceptable Use Policy
Version: 1.0 | Owner: CISO | Classification: Internal

PURPOSE
This policy defines acceptable and prohibited uses of company information systems, devices, networks, and data by employees and contractors.

SCOPE
Applies to all employees, contractors, consultants, and temporary workers who use company-provided or personal devices to access company systems or data.

POLICY STATEMENTS
Acceptable Use of Company Resources: Company systems, devices, and network resources are provided for business purposes. Reasonable personal use is permitted provided it does not: interfere with job performance, violate any laws or other policies, consume excessive bandwidth or storage, or create security risks.

Prohibited Activities: The following are strictly prohibited. Attempting to gain unauthorized access to any system, account, or data. Installing unauthorized software, browser extensions, or hardware on company devices. Disabling or circumventing security controls (antivirus, firewalls, MDM, MFA). Sharing credentials or granting unauthorized access to others. Storing company data in unauthorized personal cloud accounts or devices. Using company resources for illegal activities including copyright infringement, fraud, or harassment. Accessing, transmitting, or storing content that is illegal, discriminatory, or inappropriate in a professional context. Using company resources for cryptocurrency mining or other personal financial gain activities. Conducting personal business activities using company resources in a way that creates legal liability for the company.

Email and Communication: Company email must not be used to transmit confidential data to personal email accounts. Auto-forwarding company email to external accounts is prohibited. Employees must exercise caution before clicking links or opening attachments in emails. Suspected phishing must be reported to the security team immediately.

Personal Devices (BYOD): Employees using personal devices for work must enroll the device in MDM or use only approved access methods (web browser with no local data storage). Company data must not be stored on personal devices without encryption. If a personal device is lost or stolen and contains company data, IT must be notified immediately.

Social Media: Employees must not share confidential company information, customer data, or non-public business information on social media. Employees posting publicly about company matters must make clear they are sharing personal opinions, not company positions. Crisis communications and product announcements must only be made through official channels.

Data Handling: Sensitive and confidential data must only be stored in approved systems. USB drives for transferring sensitive data require encryption and CISO approval. Data must be classified and handled in accordance with the Data Classification policy.

Monitoring: Employees are informed that company systems and devices may be monitored for security and compliance purposes. Monitoring is conducted in accordance with applicable laws. This policy does not create an expectation of privacy on company-owned systems.

ROLES AND RESPONSIBILITIES
All Employees and Contractors: Must read, understand, and comply with this policy. Must complete annual acknowledgment.
IT Security: Monitors compliance, investigates violations.
HR: Manages disciplinary process for violations.
Managers: Responsible for ensuring their team understands and complies with this policy.

VIOLATIONS
Violations may result in disciplinary action including termination of employment or contract, and referral to law enforcement where appropriate.

RELATED STANDARDS
SOC 2 CC1.3 | ISO 27001 A.8.1 | Company Code of Conduct
""",
    },
]


async def seed_starter_policies(org_id: int) -> None:
    """Embed and store all starter policies for a new org. Runs as a background task."""
    from app.db import SessionLocal
    from app.models import Document, FileType, KnowledgeChunk, SourceType
    from app.services.chunking import chunk_text
    from app.services.embeddings import get_embedding_provider

    db = SessionLocal()
    try:
        provider = get_embedding_provider()
        for policy in STARTER_POLICIES:
            chunks = chunk_text(policy["content"])
            if not chunks:
                continue
            embeddings = await provider.embed(chunks)

            doc = Document(
                filename=policy["filename"],
                file_type=FileType.pdf,
                chunk_count=len(chunks),
                org_id=org_id,
                is_starter=True,
            )
            db.add(doc)
            db.flush()

            for chunk_val, emb in zip(chunks, embeddings):
                db.add(KnowledgeChunk(
                    document_id=doc.id,
                    source_document=policy["filename"],
                    source_section=policy["section"],
                    source_type=SourceType.policy,
                    text=chunk_val,
                    embedding=emb,
                ))

        db.commit()
        print(f"[starter_pack] Seeded {len(STARTER_POLICIES)} policies for org {org_id}")
    except Exception as exc:
        db.rollback()
        print(f"[starter_pack] Seeding failed for org {org_id}: {exc}")
    finally:
        db.close()
