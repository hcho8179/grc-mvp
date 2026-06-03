"""Background questionnaire answer generation (shared by API + job worker)."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import (
    ConfidenceLevel,
    GenerationStatus,
    Notification,
    Question,
    Questionnaire,
    QuestionnaireStatus,
    QuestionStatus,
    User,
)
from app.services.audit import log_event
from app.services.generation import classify_category, generate_answer
from app.services.retrieval import check_answer_conflict, retrieve_relevant_chunks
from app.services.citations import save_citation_scores


async def run_questionnaire_generation(questionnaire_id: int, user_id: int) -> None:
    """Generate draft answers for all pending questions on a questionnaire."""
    db: Session = SessionLocal()
    try:
        qs = db.query(Questionnaire).filter(Questionnaire.id == questionnaire_id).first()
        user = db.query(User).filter(User.id == user_id).first()
        if not qs or not user:
            return

        qs.generation_status = GenerationStatus.running.value
        qs.generation_started_at = datetime.now(timezone.utc)
        qs.generation_error = None
        qs.generation_done_count = 0
        db.commit()

        pending = (
            db.query(Question)
            .filter(
                Question.questionnaire_id == questionnaire_id,
                Question.status == QuestionStatus.pending,
            )
            .order_by(Question.row_index)
            .all()
        )
        updated = 0
        conflict_count = 0

        for q in pending:
            try:
                chunks = await retrieve_relevant_chunks(
                    q.question_text,
                    db,
                    workspace_id=qs.workspace_id,
                    customer_name=qs.customer_name,
                )
                result = await generate_answer(q.question_text, chunks)
                q.draft_answer = result.answer
                q.short_answer = result.short_answer
                q.confidence = ConfidenceLevel(result.confidence)
                q.cited_chunk_ids = result.cited_chunk_ids
                q.reasoning = result.reasoning
                q.status = QuestionStatus.generated
                if not q.category:
                    q.category = await classify_category(q.question_text)
                save_citation_scores(db, q.id, chunks, result.cited_chunk_ids)
                log_event(
                    db,
                    workspace_id=qs.workspace_id,
                    user_id=user.id,
                    user_email=user.email,
                    action="answer.generated",
                    resource_type="question",
                    resource_id=q.id,
                    detail={"questionnaire_id": questionnaire_id, "confidence": result.confidence},
                )
                updated += 1
                qs.generation_done_count = updated
                db.commit()
            except Exception as exc:
                db.rollback()
                print(f"[generate] Failed on question {q.id}: {exc}")
                await asyncio.sleep(6)
                continue

            try:
                warning = await check_answer_conflict(
                    q.question_text,
                    result.short_answer or "",
                    db,
                    qs.workspace_id,
                )
                if warning:
                    q.conflict_warning = warning
                    conflict_count += 1
                    db.commit()
            except Exception:
                db.rollback()
            await asyncio.sleep(6)

        if qs.status == QuestionnaireStatus.draft:
            qs.status = QuestionnaireStatus.in_progress

        qs.generation_status = GenerationStatus.complete.value
        qs.generation_error = None
        db.add(
            Notification(
                workspace_id=qs.workspace_id,
                user_id=user.id,
                type="generation_complete",
                title=f"Drafts ready — {qs.name}",
                body=f"{updated} answer{'s' if updated != 1 else ''} drafted."
                + (
                    f" {conflict_count} conflict{'s' if conflict_count != 1 else ''} flagged."
                    if conflict_count
                    else ""
                ),
                resource_type="questionnaire",
                resource_id=questionnaire_id,
            )
        )
        db.commit()

        try:
            from app.config import get_settings
            from app.services.email import send_generation_complete

            settings = get_settings()
            url = f"{settings.app_url}/questionnaires/{questionnaire_id}"
            send_generation_complete(
                to_email=user.email,
                user_name=user.full_name or "",
                questionnaire_name=qs.name,
                total=updated,
                conflicts=conflict_count,
                questionnaire_url=url,
            )
        except Exception:
            pass

    except Exception as exc:
        db.rollback()
        qs = db.query(Questionnaire).filter(Questionnaire.id == questionnaire_id).first()
        if qs:
            qs.generation_status = GenerationStatus.failed.value
            qs.generation_error = str(exc)[:2000]
            db.commit()
        print(f"[generate] Questionnaire {questionnaire_id} failed: {exc}")
    finally:
        db.close()
