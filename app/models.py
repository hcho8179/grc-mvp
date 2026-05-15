"""
SQLAlchemy ORM models.

Tables:
  knowledge_chunks  — chunked text from uploaded policies + past Q&A pairs
  questionnaires    — a single uploaded blank questionnaire file
  questions         — individual rows parsed from a questionnaire
"""

import enum
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    ARRAY,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db import Base

EMBEDDING_DIM = 1536  # text-embedding-3-small; change to 1024 for voyage-3


# ---------------------------------------------------------------------------
# KnowledgeChunk
# ---------------------------------------------------------------------------

class SourceType(str, enum.Enum):
    policy = "policy"          # PDF / DOCX upload
    past_answer = "past_answer"  # prior answered Excel questionnaire
    approved_answer = "approved_answer"  # answer the user approved in review UI


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Human-readable provenance
    source_document = Column(String(512), nullable=False)   # original filename
    source_section = Column(String(512), nullable=True)     # sheet name, heading, etc.
    source_type = Column(Enum(SourceType), nullable=False)

    text = Column(Text, nullable=False)
    embedding = Column(Vector(EMBEDDING_DIM), nullable=True)

    # Back-ref: chunks cited when answering questions
    cited_in = relationship("Question", secondary="question_citations", back_populates="cited_chunks")


# ---------------------------------------------------------------------------
# Questionnaire
# ---------------------------------------------------------------------------

class QuestionnaireStatus(str, enum.Enum):
    uploaded = "uploaded"       # parsed, questions stored
    generating = "generating"   # AI generation in progress
    in_review = "in_review"     # answers generated, awaiting review
    exported = "exported"       # answers exported to Excel


class Questionnaire(Base):
    __tablename__ = "questionnaires"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    filename = Column(String(512), nullable=False)
    customer_name = Column(String(256), nullable=True)  # optional label
    status = Column(Enum(QuestionnaireStatus), default=QuestionnaireStatus.uploaded)

    # Column indices the user chose during upload (0-based)
    question_col = Column(Integer, nullable=False)
    answer_col = Column(Integer, nullable=False)
    header_row = Column(Integer, default=0)          # 0 = first row is header

    questions = relationship("Question", back_populates="questionnaire", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Question
# ---------------------------------------------------------------------------

class ConfidenceLevel(str, enum.Enum):
    high = "high"
    medium = "medium"
    low = "low"
    insufficient = "insufficient"


class QuestionStatus(str, enum.Enum):
    pending = "pending"         # no answer yet
    draft = "draft"             # AI answer generated
    approved = "approved"       # user approved (and saved to KB)


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    questionnaire_id = Column(Integer, ForeignKey("questionnaires.id"), nullable=False)
    questionnaire = relationship("Questionnaire", back_populates="questions")

    row_index = Column(Integer, nullable=False)   # original Excel row (0-based after header)
    text = Column(Text, nullable=False)

    draft_answer = Column(Text, nullable=True)
    final_answer = Column(Text, nullable=True)    # set after user edits/approves

    confidence = Column(Enum(ConfidenceLevel), nullable=True)
    status = Column(Enum(QuestionStatus), default=QuestionStatus.pending)

    # Chunks cited by the AI when generating this answer
    cited_chunks = relationship("KnowledgeChunk", secondary="question_citations", back_populates="cited_in")


# ---------------------------------------------------------------------------
# Junction table: question ↔ knowledge_chunk citations
# ---------------------------------------------------------------------------

from sqlalchemy import Table

question_citations = Table(
    "question_citations",
    Base.metadata,
    Column("question_id", Integer, ForeignKey("questions.id"), primary_key=True),
    Column("chunk_id", Integer, ForeignKey("knowledge_chunks.id"), primary_key=True),
    Column("retrieval_score", Float, nullable=True),  # cosine similarity score
)
