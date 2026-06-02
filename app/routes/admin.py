"""Admin routes — usage and cost tracking."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models import LLMCall, Questionnaire

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

_LOCALHOST = {"127.0.0.1", "::1"}


def _require_admin_access(request: Request) -> None:
    """Allow only localhost or requests with the correct ADMIN_SECRET header.

    Uses request.client.host (not X-Forwarded-For) for the localhost check
    to prevent IP spoofing. Uses secrets.compare_digest for constant-time
    comparison to prevent timing attacks.
    """
    import secrets as _secrets
    settings = get_settings()
    client_ip = request.client.host if request.client else ""
    if client_ip in _LOCALHOST:
        return
    secret = settings.admin_secret
    provided = request.headers.get("X-Admin-Secret", "")
    if secret and provided and _secrets.compare_digest(provided, secret):
        return
    raise HTTPException(status_code=403, detail="Forbidden")


@router.get("/usage", response_class=HTMLResponse)
async def usage(request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin_access)):
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # This month totals
    month_calls = db.query(LLMCall).filter(LLMCall.created_at >= month_start).all()
    month_input = sum(c.input_tokens or 0 for c in month_calls)
    month_output = sum(c.output_tokens or 0 for c in month_calls)
    month_cost = sum(c.cost_estimate or 0 for c in month_calls)

    # Per-questionnaire cost
    per_q = (
        db.query(
            Questionnaire.name,
            func.count(LLMCall.id).label("calls"),
            func.sum(LLMCall.input_tokens).label("input_tokens"),
            func.sum(LLMCall.output_tokens).label("output_tokens"),
            func.sum(LLMCall.cost_estimate).label("cost"),
        )
        .join(LLMCall, LLMCall.questionnaire_id == Questionnaire.id, isouter=True)
        .group_by(Questionnaire.id, Questionnaire.name)
        .order_by(func.sum(LLMCall.cost_estimate).desc().nullslast())
        .all()
    )

    # All-time totals
    totals = db.query(
        func.count(LLMCall.id),
        func.sum(LLMCall.input_tokens),
        func.sum(LLMCall.output_tokens),
        func.sum(LLMCall.cost_estimate),
    ).first()

    return templates.TemplateResponse(
        request,
        "admin/usage.html",
        {
            "month_calls": len(month_calls),
            "month_input": month_input,
            "month_output": month_output,
            "month_cost": round(month_cost, 4),
            "per_q": per_q,
            "total_calls": totals[0] or 0,
            "total_input": totals[1] or 0,
            "total_output": totals[2] or 0,
            "total_cost": round(totals[3] or 0, 4),
            "month_label": now.strftime("%B %Y"),
        },
    )
