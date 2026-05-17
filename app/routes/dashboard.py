"""Dashboard — home page with stats and recent activity."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import ConfidenceLevel, LLMCall, Question, QuestionStatus, Questionnaire

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    total_questionnaires = db.query(Questionnaire).count()

    answered_statuses = [QuestionStatus.generated, QuestionStatus.approved]
    total_answered = (
        db.query(Question)
        .filter(Question.status.in_(answered_statuses))
        .count()
    )
    total_approved = (
        db.query(Question).filter(Question.status == QuestionStatus.approved).count()
    )

    # Confidence breakdown
    high_count = db.query(Question).filter(Question.confidence == ConfidenceLevel.high).count()
    med_count = db.query(Question).filter(Question.confidence == ConfidenceLevel.medium).count()
    low_count = db.query(Question).filter(Question.confidence == ConfidenceLevel.low).count()
    conf_total = high_count + med_count + low_count
    avg_conf_pct = round(((high_count * 3 + med_count * 2 + low_count) / (conf_total * 3)) * 100) if conf_total else 0

    hours_saved = round(total_answered * 8 / 60, 1)  # 8 min per question

    # Cost totals
    cost_row = db.query(func.sum(LLMCall.cost_estimate)).scalar()
    total_cost = round(cost_row or 0.0, 4)

    recent = (
        db.query(Questionnaire)
        .order_by(Questionnaire.created_at.desc())
        .limit(5)
        .all()
    )

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "total_questionnaires": total_questionnaires,
            "total_answered": total_answered,
            "total_approved": total_approved,
            "avg_conf_pct": avg_conf_pct,
            "hours_saved": hours_saved,
            "total_cost": total_cost,
            "recent": recent,
        },
    )
