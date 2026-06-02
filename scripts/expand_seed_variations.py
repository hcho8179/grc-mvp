#!/usr/bin/env python
"""
Expand the 45 seeded AU GRC Q&A pairs with question-phrasing variations.

For each seed Q&A, generates 5 alternative ways an enterprise buyer might ask
the same question, then stores each variation as an additional KnowledgeChunk
(same answer, different question phrasing). This expands the day-one RAG
semantic anchor points from 45 to ~270 without touching the RAG pipeline.

Usage (from project root):
    python scripts/expand_seed_variations.py [workspace_id]

    workspace_id defaults to 1 if not provided.
    Skips variations that already exist.
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.db import SessionLocal
from app.models import Document, FileType, KnowledgeChunk, SourceType, Workspace
from app.services.embeddings import get_embedding_provider
from app.services.generation import get_llm_provider
from scripts.seed_answer_library import SEED_QA

VARIATIONS_PER_QUESTION = 5

SYSTEM_PROMPT = """You are an Australian enterprise security and procurement expert.
Your task is to generate alternative phrasings of security questionnaire questions.
Return ONLY a JSON array of strings. No explanation, no markdown, just the JSON array."""

def _user_prompt(question: str) -> str:
    return f"""Generate {VARIATIONS_PER_QUESTION} alternative ways an enterprise buyer or government agency might ask the following security questionnaire question.
Vary the phrasing, terminology, and structure. Include both formal and informal variants.
Consider Australian government, financial services (APRA), and general enterprise contexts.

Original question: {question}

Return a JSON array of {VARIATIONS_PER_QUESTION} strings only."""


async def generate_variations(question: str) -> list[str]:
    provider = get_llm_provider()
    try:
        raw, _, _ = await provider.generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=_user_prompt(question),
        )
        raw = raw.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        variations = json.loads(raw)
        if isinstance(variations, list):
            return [v for v in variations if isinstance(v, str) and v.strip()][:VARIATIONS_PER_QUESTION]
    except Exception as exc:
        print(f"  [warn] Failed to generate variations: {exc}")
    return []


async def main(workspace_id: int) -> None:
    db = SessionLocal()
    try:
        ws = db.get(Workspace, workspace_id)
        if not ws:
            print(f"Workspace {workspace_id} not found.")
            return

        print(f"Expanding seed variations for workspace: {ws.name} (id={workspace_id})")
        print(f"Processing {len(SEED_QA)} seed Q&A pairs × {VARIATIONS_PER_QUESTION} variations each...")

        provider = get_embedding_provider()

        # Get or create the "Approved Answers" document
        doc = db.query(Document).filter(
            Document.filename == "Approved Answers",
            Document.workspace_id == workspace_id,
        ).first()
        if not doc:
            doc = Document(
                filename="Approved Answers",
                file_type=FileType.xlsx,
                chunk_count=0,
                workspace_id=workspace_id,
            )
            db.add(doc)
            db.flush()

        inserted = 0
        skipped = 0

        for i, (question_text, answer_text, _) in enumerate(SEED_QA):
            print(f"[{i+1}/{len(SEED_QA)}] Generating variations for: {question_text[:60]}...")

            variations = await generate_variations(question_text)
            if not variations:
                print(f"  Skipped — no variations generated.")
                continue

            for variation in variations:
                chunk_text = f"Q: {variation}\nA: {answer_text}"
                marker = f"[variation] {variation[:80]}"

                # Skip if already exists (check by source_section marker)
                exists = db.execute(
                    select(KnowledgeChunk.id).where(
                        KnowledgeChunk.document_id == doc.id,
                        KnowledgeChunk.source_section == marker,
                    ).limit(1)
                ).scalar_one_or_none()

                if exists:
                    skipped += 1
                    continue

                chunk_ctx = f"Document: Approved Answers\n{chunk_text}"
                embeddings = await provider.embed([chunk_ctx])

                chunk = KnowledgeChunk(
                    document_id=doc.id,
                    source_document="Approved Answers",
                    source_section=marker,
                    source_type=SourceType.approved_answer,
                    text=chunk_text,
                    embedding=embeddings[0],
                    customer_name=None,
                )
                db.add(chunk)
                doc.chunk_count = (doc.chunk_count or 0) + 1
                inserted += 1

            db.commit()
            print(f"  Added {len(variations)} variations.")

            # Small delay to stay within API rate limits
            await asyncio.sleep(2)

        print(f"\nDone — {inserted} variation chunks inserted, {skipped} already existed.")

    finally:
        db.close()


if __name__ == "__main__":
    wid = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    asyncio.run(main(wid))
