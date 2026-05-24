"""Thin helper to record audit events. Always call before db.commit()."""

from sqlalchemy.orm import Session

from app.models import AuditLog


def log_event(
    db: Session,
    *,
    workspace_id: int,
    user_id: int | None,
    user_email: str | None,
    action: str,
    resource_type: str | None = None,
    resource_id: int | None = None,
    detail: dict | None = None,
) -> None:
    db.add(AuditLog(
        workspace_id=workspace_id,
        user_id=user_id,
        user_email=user_email,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        detail=detail,
    ))
