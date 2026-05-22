"""Shared utilities — no internal imports to avoid circular dependencies."""

import time
from collections import defaultdict
from fastapi import Request


def real_ip(request: Request) -> str:
    """Return the real client IP, reading X-Forwarded-For set by Cloudflare/nginx."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class LoginVelocityGuard:
    """Per-email sliding-window failed-login counter.

    Blocks credential stuffing: attacker rotates IPs but targets the same
    email. Even across 100 different source IPs, 10 failures against the
    same email within 15 minutes triggers a lockout.

    State is in-memory. Resets on server restart (acceptable for MVP;
    replace with Redis for multi-instance deployments).
    """

    _WINDOW_SECS: float = 900.0   # 15-minute sliding window
    _THRESHOLD:   int   = 10      # failures before lockout
    _store: dict[str, list[float]] = defaultdict(list)

    @classmethod
    def record_failure(cls, email: str) -> None:
        now = time.monotonic()
        cls._store[email].append(now)
        cls._store[email] = [t for t in cls._store[email] if now - t < cls._WINDOW_SECS]

    @classmethod
    def is_locked(cls, email: str) -> bool:
        now = time.monotonic()
        recent = [t for t in cls._store.get(email, []) if now - t < cls._WINDOW_SECS]
        cls._store[email] = recent
        return len(recent) >= cls._THRESHOLD

    @classmethod
    def reset_on_success(cls, email: str) -> None:
        cls._store.pop(email, None)


class IPSprayGuard:
    """Per-IP global failed-login counter across ALL email addresses.

    Blocks password spraying: attacker keeps the same IP but rotates
    through many email addresses so no single account hits its lockout
    threshold. This layer watches the IP's total failure count regardless
    of which emails are being targeted.

    Threshold is set higher than LoginVelocityGuard (20 vs 10) to avoid
    false-positives from a shared NAT/office IP where multiple legitimate
    users happen to mistype passwords around the same time.

    State is in-memory. Replace with Redis for multi-instance deployments.
    """

    _WINDOW_SECS: float = 900.0   # 15-minute sliding window
    _THRESHOLD:   int   = 20      # total failures across any emails before IP block
    _store: dict[str, list[float]] = defaultdict(list)

    @classmethod
    def record_failure(cls, ip: str) -> None:
        now = time.monotonic()
        cls._store[ip].append(now)
        cls._store[ip] = [t for t in cls._store[ip] if now - t < cls._WINDOW_SECS]

    @classmethod
    def is_blocked(cls, ip: str) -> bool:
        now = time.monotonic()
        recent = [t for t in cls._store.get(ip, []) if now - t < cls._WINDOW_SECS]
        cls._store[ip] = recent
        return len(recent) >= cls._THRESHOLD
