"""Scheduled maintenance: trash purge and due-date reminders."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import (
    ApprovedAnswer,
    Document,
    LLMCall,
    Question,
    QuestionComment,
    Questionnaire,
    QuestionnaireStatus,
    User,
    question_citations,
)
TRASH_RETENTION_DAYS = 90
DUE_REMINDER_WINDOW_DAYS = 2


def purge_expired_trash(db: Session) -> dict[str, int]:
    """Permanently delete soft-deleted items older than TRASH_RETENTION_DAYS."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=TRASH_RETENTION_DAYS)
    purged_qs = 0
    purged_docs = 0

    old_qs = (
        db.query(Questionnaire)
        .filter(Questionnaire.deleted_at != None, Questionnaire.deleted_at < cutoff)
        .all()
    )
    for qs in old_qs:
        qids = [
            row[0]
            for row in db.query(Question.id).filter(Question.questionnaire_id == qs.id).all()
        ]
        if qids:
            db.query(ApprovedAnswer).filter(ApprovedAnswer.source_question_id.in_(qids)).update(
                {ApprovedAnswer.source_question_id: None},
                synchronize_session=False,
            )
            db.execute(question_citations.delete().where(question_citations.c.question_id.in_(qids)))
            db.query(QuestionComment).filter(QuestionComment.question_id.in_(qids)).delete(
                synchronize_session=False
            )
            db.query(LLMCall).filter(LLMCall.question_id.in_(qids)).delete(synchronize_session=False)
            db.query(Question).filter(Question.questionnaire_id == qs.id).delete(
                synchronize_session=False
            )
        db.delete(qs)
        purged_qs += 1

    old_docs = (
        db.query(Document)
        .filter(Document.deleted_at != None, Document.deleted_at < cutoff)
        .all()
    )
    for doc in old_docs:
        db.delete(doc)
        purged_docs += 1

    if purged_qs or purged_docs:
        db.commit()

    return {"questionnaires": purged_qs, "documents": purged_docs}


def process_due_date_reminders(db: Session) -> int:
    """Email workspace owners when a questionnaire due date is within 48 hours."""
    now = datetime.now(timezone.utc)
    window_end = now + timedelta(days=DUE_REMINDER_WINDOW_DAYS)

    candidates = (
        db.query(Questionnaire)
        .filter(
            Questionnaire.deleted_at == None,
            Questionnaire.due_date != None,
            Questionnaire.due_date > now,
            Questionnaire.due_date <= window_end,
            Questionnaire.due_reminder_sent_at == None,
            Questionnaire.status != QuestionnaireStatus.complete,
        )
        .all()
    )
    if not candidates:
        return 0

    from app.config import get_settings
    from app.services.email import send_due_date_reminder

    settings = get_settings()
    sent = 0

    for qs in candidates:
        owners = (
            db.query(User)
            .filter(
                User.workspace_id == qs.workspace_id,
                User.is_active == True,
                User.role.in_(("owner", "admin")),
            )
            .all()
        )
        if not owners:
            continue
        url = f"{settings.app_url}/questionnaires/{qs.id}"
        due_str = qs.due_date.strftime("%d %b %Y") if qs.due_date else ""
        for owner in owners:
            try:
                send_due_date_reminder(
                    to_email=owner.email,
                    user_name=owner.full_name or "",
                    questionnaire_name=qs.name,
                    due_date=due_str,
                    questionnaire_url=url,
                )
            except Exception:
                pass
        qs.due_reminder_sent_at = now
        sent += 1

    if sent:
        db.commit()
    return sent
