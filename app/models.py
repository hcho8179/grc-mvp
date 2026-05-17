"""
SQLAlchemy ORM models.

Tables:
  documents         — one row per uploaded source file
  knowledge_chunks  — chunked text from uploaded policies + past Q&A pairs
  questionnaires    — a single uploaded blank questionnaire file
  questions         — individual rows parsed from a questionnaire
  llm_calls         — per-call token + cost log for the usage dashboard
"""

import enum

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    LargeBinary,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db import Base

EMBEDDING_DIM = 1024  # voyage-3; change to 1536 if switching to text-embedding-3-small


# ---------------------------------------------------------------------------
# Document  (one row per uploaded file)
# ---------------------------------------------------------------------------

class FileType(str, enum.Enum):
    pdf = "pdf"
    docx = "docx"
    xlsx = "xlsx"


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    filename = Column(String(512), nullable=False)
    file_type = Column(Enum(FileType), nullable=False)
    chunk_count = Column(Integer, default=0, nullable=False)
    content_hash = Column(String(64), nullable=True, unique=True, index=True)

    chunks = relationship(
        "KnowledgeChunk",
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


# ---------------------------------------------------------------------------
# KnowledgeChunk
# ---------------------------------------------------------------------------

class SourceType(str, enum.Enum):
    policy = "policy"             # PDF / DOCX upload
    past_answer = "past_answer"   # prior answered Excel questionnaire
    approved_answer = "approved_answer"  # answer the user approved in review UI


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    document_id = Column(
        Integer,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document = relationship("Document", back_populates="chunks")

    source_document = Column(String(512), nullable=False)   # original filename (denormalized for fast display)
    source_section = Column(String(512), nullable=True)     # sheet name, heading, etc.
    source_type = Column(Enum(SourceType), nullable=False)

    text = Column(Text, nullable=False)
    embedding = Column(Vector(EMBEDDING_DIM), nullable=True)

    cited_in = relationship(
        "Question",
        secondary="question_citations",
        back_populates="cited_chunks",
    )


# ---------------------------------------------------------------------------
# Questionnaire
# ---------------------------------------------------------------------------

class QuestionnaireStatus(str, enum.Enum):
    draft = "draft"             # parsed, questions stored, no answers yet
    in_progress = "in_progress" # AI generation in progress or partially reviewed
    complete = "complete"       # all answers approved and exported


class Questionnaire(Base):
    __tablename__ = "questionnaires"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    name = Column(String(512), nullable=False)
    customer_name = Column(String(256), nullable=True)
    source_filename = Column(String(512), nullable=False)
    status = Column(Enum(QuestionnaireStatus), default=QuestionnaireStatus.draft, nullable=False)
    question_count = Column(Integer, default=0, nullable=False)
    raw_xlsx_blob = Column(LargeBinary, nullable=True)
    answer_col_index = Column(Integer, nullable=True)  # 0-based; which column to write answers into on export

    questions = relationship(
        "Question",
        back_populates="questionnaire",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


# ---------------------------------------------------------------------------
# Question
# ---------------------------------------------------------------------------

class ConfidenceLevel(str, enum.Enum):
    high = "high"
    medium = "medium"
    low = "low"


class QuestionStatus(str, enum.Enum):
    pending = "pending"     # no answer yet
    generated = "generated" # AI draft produced
    approved = "approved"   # user approved final answer
    rejected = "rejected"   # user rejected; needs manual answer


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    questionnaire_id = Column(
        Integer,
        ForeignKey("questionnaires.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    questionnaire = relationship("Questionnaire", back_populates="questions")

    row_index = Column(Integer, nullable=False)  # original Excel row (0-based after header)
    question_text = Column(Text, nullable=False)

    draft_answer = Column(Text, nullable=True)
    final_answer = Column(Text, nullable=True)

    status = Column(Enum(QuestionStatus), default=QuestionStatus.pending, nullable=False)
    confidence = Column(Enum(ConfidenceLevel), nullable=True)
    cited_chunk_ids = Column(JSON, nullable=True)  # list[int] — populated by Phase 4
    reasoning = Column(Text, nullable=True)         # LLM confidence explanation

    cited_chunks = relationship(
        "KnowledgeChunk",
        secondary="question_citations",
        back_populates="cited_in",
    )


# ---------------------------------------------------------------------------
# LLMCall — token + cost tracking
# ---------------------------------------------------------------------------

class LLMCall(Base):
    __tablename__ = "llm_calls"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    model = Column(String(128), nullable=False)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    cost_estimate = Column(Float, nullable=True)  # USD

    questionnaire_id = Column(
        Integer, ForeignKey("questionnaires.id", ondelete="SET NULL"), nullable=True
    )
    question_id = Column(
        Integer, ForeignKey("questions.id", ondelete="SET NULL"), nullable=True
    )


# ---------------------------------------------------------------------------
# Junction table: question ↔ knowledge_chunk citations
# ---------------------------------------------------------------------------

question_citations = Table(
    "question_citations",
    Base.metadata,
    Column("question_id", Integer, ForeignKey("questions.id"), primary_key=True),
    Column("chunk_id", Integer, ForeignKey("knowledge_chunks.id"), primary_key=True),
    Column("retrieval_score", Float, nullable=True),  # cosine similarity score
)
