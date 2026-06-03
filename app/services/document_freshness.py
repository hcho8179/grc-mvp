"""Policy document freshness — age nudges + answer staleness when content changes."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import ApprovedAnswer

# Calendar nudges only — does not block RAG or generation.
REVIEW_WARN_DAYS = 90
REVIEW_URGENT_DAYS = 180


def effective_updated_at(
    content_updated_at: datetime | None,
    created_at: datetime | None,
) -> datetime | None:
    if content_updated_at:
        return content_updated_at
    return created_at


def days_since(dt: datetime | None, *, now: datetime | None = None) -> int | None:
    if not dt:
        return None
    ref = now or datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return max(0, (ref - dt).days)


def review_level(
    content_updated_at: datetime | None,
    created_at: datetime | None,
    *,
    now: datetime | None = None,
) -> str | None:
    """warn = verify still current; urgent = refresh recommended; None = fine."""
    days = days_since(effective_updated_at(content_updated_at, created_at), now=now)
    if days is None:
        return None
    if days >= REVIEW_URGENT_DAYS:
        return "urgent"
    if days >= REVIEW_WARN_DAYS:
        return "warn"
    return None


def review_meta(
    content_updated_at: datetime | None,
    created_at: datetime | None,
    *,
    now: datetime | None = None,
) -> dict | None:
    level = review_level(content_updated_at, created_at, now=now)
    if not level:
        return None
    days = days_since(effective_updated_at(content_updated_at, created_at), now=now)
    labels = {
        "warn": "Not confirmed in 3+ months — verify this policy is still current",
        "urgent": "Not confirmed in 6+ months — consider uploading a refreshed version",
    }
    return {"level": level, "days": days, "message": labels[level]}


def mark_answers_stale_for_chunk_ids(
    db: Session,
    workspace_id: int,
    chunk_ids: list[int],
) -> int:
    """Mark library answers that cited these chunks. Returns newly flagged count."""
    if not chunk_ids:
        return 0
    chunk_set = set(chunk_ids)
    marked = 0
    answers = (
        db.query(ApprovedAnswer)
        .filter(
            ApprovedAnswer.workspace_id == workspace_id,
            ApprovedAnswer.status == "active",
            ApprovedAnswer.is_stale == False,
        )
        .all()
    )
    for answer in answers:
        cited = answer.cited_chunk_ids or []
        if any(cid in chunk_set for cid in cited):
            answer.is_stale = True
            marked += 1
    if marked:
        db.flush()
    return marked


def count_stale_answers(db: Session, workspace_id: int) -> int:
    return (
        db.query(ApprovedAnswer)
        .filter(
            ApprovedAnswer.workspace_id == workspace_id,
            ApprovedAnswer.status == "active",
            ApprovedAnswer.is_stale == True,
        )
        .count()
    )
