"""Shared utilities — no internal imports to avoid circular dependencies."""

from fastapi import Request


def real_ip(request: Request) -> str:
    """Return the real client IP, reading X-Forwarded-For set by Cloudflare/nginx."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
