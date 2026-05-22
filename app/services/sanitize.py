"""Prompt-injection sanitization for knowledge base documents.

Strips lines that match known instruction-injection patterns before text
is chunked and embedded.  This is a defence-in-depth measure: it does not
guarantee perfect protection, but it removes the obvious attack surface of
embedding fake system instructions inside uploaded policy documents.

Two tiers:
  - HARD patterns  → line is removed entirely and the event is logged.
  - SOFT patterns  → line is flagged in the log but kept (reduces false
                     positives for legitimate security-policy language).
"""

import logging
import re

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pattern registry
# ---------------------------------------------------------------------------

# Each entry is a compiled regex.  Any line that *contains* a match is dropped.
_HARD_PATTERNS: list[re.Pattern] = [
    # Classic overrides — English
    re.compile(r"(?i)\bsystem\s+(instruction|prompt|override|command)\b"),
    re.compile(r"(?i)\bignore\s+(all\s+)?(previous|prior|above|earlier)\s+instructions?\b"),
    re.compile(r"(?i)\bdisregard\s+(all\s+)?(previous|prior|above)\s+instructions?\b"),
    re.compile(r"(?i)\boverride\s+(all\s+)?instructions?\b"),
    re.compile(r"(?i)\bforget\s+(all\s+)?previous\s+instructions?\b"),
    re.compile(r"(?i)\bnew\s+(system\s+)?instructions?\s*:"),
    re.compile(r"(?i)\bupdated?\s+instructions?\s*:"),
    # Behavioral hijacks
    re.compile(r"(?i)\b(you\s+(are\s+now|must|will|should)\s+always\s+(respond|answer|say|reply))"),
    re.compile(r"(?i)\b(always\s+(respond|answer|reply)\s+with)\b"),
    re.compile(r"(?i)\b(never\s+(respond|answer|reply|say))\b"),
    re.compile(r"(?i)\bfrom\s+now\s+on\s+(you\s+)?(must|will|should|are\s+to)\b"),
    re.compile(r"(?i)\byour\s+(new\s+)?role\s+is\s+(now\s+)?to\b"),
    re.compile(r"(?i)\bact\s+as\s+(if\s+you\s+(are|were)|a\s+)"),
    # Model-specific injection tokens
    re.compile(r"(?i)<\|?(system|im_start|im_end|end_of_turn)\|?>"),
    re.compile(r"(?i)\[INST\]|\[/INST\]|<<SYS>>|<</SYS>>"),
    re.compile(r"(?i)###\s*(system|instruction|human|assistant)\b"),
    # Chinese-language equivalents
    re.compile(r"系统.*?指令|系统.*?覆盖|忽略.*?指令|覆盖.*?指令|忘记.*?指令"),
    re.compile(r"从现在起.*?(必须|应该|要|都要)"),
    re.compile(r"(你|您)(现在|之后|以后)(必须|应该|要|都要)"),
]

# Softer patterns: flag but keep (legitimately appear in security policies)
_SOFT_PATTERNS: list[re.Pattern] = [
    re.compile(r"(?i)\bpretend\s+(you\s+are|to\s+be)\b"),
    re.compile(r"(?i)\brespond\s+only\s+with\b"),
    re.compile(r"(?i)\byou\s+are\s+a\s+\w+\s+(ai|assistant|bot|system)\b"),
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def sanitize_text(text: str, source_label: str = "") -> str:
    """Return a cleaned copy of *text* with injection lines removed.

    Lines matching hard patterns are dropped; soft-pattern matches are
    logged for human review but left in place.  Empty lines that result
    from removal are collapsed.
    """
    lines = text.splitlines()
    clean: list[str] = []
    removed = 0

    for line in lines:
        if _matches_any(line, _HARD_PATTERNS):
            logger.warning(
                "Prompt-injection pattern detected and removed | source=%s | line=%r",
                source_label or "unknown",
                line[:200],
            )
            removed += 1
            continue

        if _matches_any(line, _SOFT_PATTERNS):
            logger.info(
                "Soft injection pattern flagged (kept) | source=%s | line=%r",
                source_label or "unknown",
                line[:200],
            )

        clean.append(line)

    if removed:
        logger.warning(
            "Sanitization summary | source=%s | %d line(s) removed out of %d",
            source_label or "unknown",
            removed,
            len(lines),
        )

    # Collapse runs of blank lines left by removal
    result = re.sub(r"\n{3,}", "\n\n", "\n".join(clean))
    return result.strip()


def _matches_any(line: str, patterns: list[re.Pattern]) -> bool:
    return any(p.search(line) for p in patterns)
