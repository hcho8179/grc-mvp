"""Answer Library routes — browse, suggest reuse, apply, archive."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import ApprovedAnswer, Question, QuestionStatus
from app.services.answer_library import detect_category, find_similar_answers

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _render_question_row(request: Request, question: Question, questionnaire_id: int) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "questionnaires/_row.html",
        {"q": question, "questionnaire_id": questionnaire_id},
    )


# ---------------------------------------------------------------------------
# Library — browse page
# ---------------------------------------------------------------------------

@router.get("", response_class=HTMLResponse)
@router.get("/library", response_class=HTMLResponse)
async def library(
    request: Request,
    q: str = "",
    category: str = "",
    db: Session = Depends(get_db),
):
    query = db.query(ApprovedAnswer).filter(ApprovedAnswer.status == "active")

    if q.strip():
        term = f"%{q.strip()}%"
        query = query.filter(
            ApprovedAnswer.question_text.ilike(term) | ApprovedAnswer.answer_text.ilike(term)
        )

    if category.strip():
        query = query.filter(ApprovedAnswer.answer_category == category.strip())

    answers = query.order_by(ApprovedAnswer.times_reused.desc(), ApprovedAnswer.created_at.desc()).all()

    # Stats
    total = db.query(func.count(ApprovedAnswer.id)).filter(ApprovedAnswer.status == "active").scalar() or 0
    total_reuses = db.query(func.sum(ApprovedAnswer.times_reused)).filter(ApprovedAnswer.status == "active").scalar() or 0

    categories = (
        db.query(ApprovedAnswer.answer_category, func.count(ApprovedAnswer.id).label("cnt"))
        .filter(ApprovedAnswer.status == "active", ApprovedAnswer.answer_category.isnot(None))
        .group_by(ApprovedAnswer.answer_category)
        .order_by(func.count(ApprovedAnswer.id).desc())
        .all()
    )

    return templates.TemplateResponse(
        request,
        "answers/library.html",
        {
            "answers": answers,
            "total": total,
            "total_reuses": int(total_reuses),
            "categories": categories,
            "q": q,
            "active_category": category,
        },
    )


# ---------------------------------------------------------------------------
# Suggest — HTMX fragment: similar answers for a question
# ---------------------------------------------------------------------------

@router.get("/suggest/{question_id}", response_class=HTMLResponse)
async def suggest(
    question_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        return HTMLResponse('<p class="text-xs text-red-400">Question not found.</p>')

    results = await find_similar_answers(question.question_text, db)

    if not results:
        return HTMLResponse(
            '<p class="text-xs text-slate-400 italic px-1">No similar answers in library yet.</p>'
        )

    parts = ['<div class="space-y-1.5 mb-2">',
             '<p class="text-xs font-semibold text-slate-500 mb-1">From your library:</p>']

    for s in results:
        safe_a = s.answer_text[:160].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        ellipsis = "…" if len(s.answer_text) > 160 else ""
        pct = round(s.similarity * 100)
        cat_badge = (
            f'<span class="mr-1 px-1.5 py-0.5 rounded text-xs bg-indigo-50 text-indigo-600">'
            f'{s.answer_category}</span>'
        ) if s.answer_category else ""

        parts.append(f"""
<div class="border border-indigo-100 bg-indigo-50 rounded-md p-2">
  <p class="text-xs text-slate-700 leading-snug">{safe_a}{ellipsis}</p>
  <div class="flex items-center justify-between mt-1.5 gap-2">
    <span class="text-xs text-slate-400">{cat_badge}{pct}% match · {s.times_reused}× reused</span>
    <button
      hx-post="/answers/{s.answer_id}/use/{question_id}"
      hx-target="#q-{question_id}"
      hx-swap="outerHTML"
      hx-disabled-elt="this"
      class="text-xs px-2 py-0.5 rounded bg-indigo-600 text-white hover:bg-indigo-700
             font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
      Use<span class="htmx-indicator"> …</span>
    </button>
  </div>
</div>""")

    parts.append("</div>")
    return HTMLResponse("".join(parts))


# ---------------------------------------------------------------------------
# Use — apply an approved answer to a question's draft
# ---------------------------------------------------------------------------

@router.post("/{answer_id}/use/{question_id}", response_class=HTMLResponse)
async def use_answer(
    answer_id: int,
    question_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    approved = db.query(ApprovedAnswer).filter(ApprovedAnswer.id == answer_id).first()
    question = db.query(Question).filter(Question.id == question_id).first()

    if not approved or not question:
        return HTMLResponse("", status_code=404)

    question.draft_answer = approved.answer_text
    if question.status == QuestionStatus.pending:
        question.status = QuestionStatus.generated

    approved.times_reused += 1
    db.commit()

    return _render_question_row(request, question, question.questionnaire_id)


# ---------------------------------------------------------------------------
# Archive — remove an answer from active library
# ---------------------------------------------------------------------------

@router.post("/{answer_id}/archive")
async def archive_answer(answer_id: int, db: Session = Depends(get_db)):
    answer = db.query(ApprovedAnswer).filter(ApprovedAnswer.id == answer_id).first()
    if answer:
        answer.status = "archived"
        db.commit()
    return RedirectResponse(url="/answers/library", status_code=303)
