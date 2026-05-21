"""Answer library helpers: category detection and similarity search."""

import math
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session


_CATEGORY_MAP: list[tuple[str, list[str]]] = [
    ("Data Encryption",       ["encrypt", "aes", "tls", "ssl", "cryptograph", "cipher", "key management"]),
    ("Access Control",        ["access control", "mfa", "multi-factor", "authentication", "authorization", "permission", "rbac", "iam", "least privilege", "privileged", "sso", "single sign"]),
    ("Audit & Logging",       ["audit", "log", "monitor", "siem", "event trail", "logging", "alerting"]),
    ("Incident Response",     ["incident", "breach", "response plan", "forensic", "playbook", "escalation"]),
    ("Backup & Recovery",     ["backup", "recovery", "restore", "rto", "rpo", "disaster", "replication"]),
    ("Vulnerability Mgmt",    ["vulnerability", "patch", "cve", "penetration", "pentest", "scan", "remediat"]),
    ("Data Privacy",          ["privacy", "gdpr", "ccpa", "pii", "personal data", "data subject", "data protection"]),
    ("Vendor Risk",           ["vendor", "third party", "third-party", "supplier", "subprocessor", "supply chain"]),
    ("Business Continuity",   ["business continuity", "bcp", "continuity plan", "operational resili"]),
    ("Physical Security",     ["physical", "datacenter", "data center", "facility", "on-premise", "hardware"]),
    ("Network Security",      ["network", "firewall", "segmentation", "intrusion", "ids", "ips", "dmz", "vpn"]),
]

# One descriptive sentence per category — embedded once, cached for the process lifetime
_CATEGORY_ANCHORS: dict[str, str] = {
    "Data Encryption":    "data encryption key management AES TLS SSL cryptography protect data in transit and at rest cipher",
    "Access Control":     "access control authentication authorization MFA multi-factor permissions RBAC IAM least privilege single sign-on SSO",
    "Audit & Logging":    "audit logging monitoring SIEM event trail alerting security logs activity records",
    "Incident Response":  "incident response security breach escalation playbook forensics incident management notification",
    "Backup & Recovery":  "backup disaster recovery restore RTO RPO replication data recovery business recovery",
    "Vulnerability Mgmt": "vulnerability management patch management CVE penetration testing security scanning remediation",
    "Data Privacy":       "data privacy GDPR CCPA PII personal data data subject rights data protection regulation",
    "Vendor Risk":        "vendor risk third party supplier subprocessor supply chain vendor assessment due diligence",
    "Business Continuity":"business continuity plan BCP operational resilience continuity planning",
    "Physical Security":  "physical security data center facility hardware on-premise physical access controls",
    "Network Security":   "network security firewall network segmentation intrusion detection IDS IPS DMZ VPN perimeter",
    "General":            "general security policy information security governance risk compliance",
}

# Module-level cache — populated once per process, never re-computed
_anchor_cache: dict[str, list[float]] = {}


def detect_category(question_text: str) -> str:
    """Fast keyword-based fallback — used for questions without a cached category."""
    lower = question_text.lower()
    for category, keywords in _CATEGORY_MAP:
        if any(kw in lower for kw in keywords):
            return category
    return "General"


def _cosine(a: list[float], b: list[float]) -> float:
    dot   = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    return dot / (mag_a * mag_b) if mag_a and mag_b else 0.0


async def classify_category(question_text: str) -> str:
    """Embed-based category classification. Result should be cached on the Question row."""
    from app.services.embeddings import get_embedding_provider

    provider = get_embedding_provider()

    # Embed anchor sentences once per process lifetime
    if not _anchor_cache:
        categories = list(_CATEGORY_ANCHORS.keys())
        sentences  = [_CATEGORY_ANCHORS[c] for c in categories]
        embeddings = await provider.embed(sentences, input_type="document")
        for cat, emb in zip(categories, embeddings):
            _anchor_cache[cat] = emb

    # Embed the question
    q_emb = await provider.embed([question_text], input_type="query")
    q_vec = q_emb[0]

    # Find closest anchor
    best_cat   = "General"
    best_score = -1.0
    for cat, anchor_vec in _anchor_cache.items():
        score = _cosine(q_vec, anchor_vec)
        if score > best_score:
            best_score = score
            best_cat   = cat

    return best_cat


@dataclass
class LibrarySuggestion:
    answer_id: int
    question_text: str
    answer_text: str
    answer_category: str | None
    times_reused: int
    similarity: float


async def find_similar_answers(
    question_text: str,
    db: Session,
    top_k: int = 3,
    threshold: float = 0.75,
) -> list[LibrarySuggestion]:
    from app.models import ApprovedAnswer
    from app.services.embeddings import get_embedding_provider

    provider = get_embedding_provider()
    embeddings = await provider.embed([question_text], input_type="query")
    query_vec = embeddings[0]
    vec_str = "[" + ",".join(str(float(v)) for v in query_vec) + "]"

    rows = db.execute(
        text("""
            SELECT id,
                   1 - (embedding <=> :vec::vector) AS similarity
            FROM   approved_answers
            WHERE  embedding IS NOT NULL
              AND  status = 'active'
            ORDER  BY embedding <=> :vec::vector
            LIMIT  :k
        """),
        {"vec": vec_str, "k": top_k},
    ).fetchall()

    if not rows:
        return []

    above = [(row.id, float(row.similarity)) for row in rows if float(row.similarity) >= threshold]
    if not above:
        return []

    ids = [r[0] for r in above]
    sim_by_id = {r[0]: r[1] for r in above}

    answers = db.query(ApprovedAnswer).filter(ApprovedAnswer.id.in_(ids)).all()
    answer_by_id = {a.id: a for a in answers}

    results = []
    for aid, sim in above:
        if aid not in answer_by_id:
            continue
        a = answer_by_id[aid]
        results.append(LibrarySuggestion(
            answer_id=a.id,
            question_text=a.question_text,
            answer_text=a.answer_text,
            answer_category=a.answer_category,
            times_reused=a.times_reused,
            similarity=sim,
        ))
    return results
