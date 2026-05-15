"""
SQLAlchemy ORM models.

Tables:
  documents         — one row per uploaded source file
  knowledge_chunks  — chunked text from uploaded policies + past Q&A pairs
  questionnaires    — a single uploaded blank questionnaire file
  questions         — individual rows parsed from a questionnaire
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
    uploaded = "uploaded"       # parsed, questions stored
    generating = "generating"   # AI generation in progress
    in_review = "in_review"     # answers generated, awaiting review
    exported = "exported"       # answers exported to Excel


class Questionnaire(Base):
    __tablename__ = "questionnaires"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    filename = Column(String(512), nullable=False)
    customer_name = Column(String(256), nullable=True)
    status = Column(Enum(QuestionnaireStatus), default=QuestionnaireStatus.uploaded)

    # Column indices the user chose during upload (0-based)
    question_col = Column(Integer, nullable=False)
    answer_col = Column(Integer, nullable=False)
    header_row = Column(Integer, default=0)

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
    pending = "pending"     # no answer yet
    draft = "draft"         # AI answer generated
    approved = "approved"   # user approved (and saved to KB)


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    questionnaire_id = Column(Integer, ForeignKey("questionnaires.id"), nullable=False)
    questionnaire = relationship("Questionnaire", back_populates="questions")

    row_index = Column(Integer, nullable=False)  # original Excel row (0-based after header)
    text = Column(Text, nullable=False)

    draft_answer = Column(Text, nullable=True)
    final_answer = Column(Text, nullable=True)   # set after user edits/approves

    confidence = Column(Enum(ConfidenceLevel), nullable=True)
    status = Column(Enum(QuestionStatus), default=QuestionStatus.pending)

    cited_chunks = relationship(
        "KnowledgeChunk",
        secondary="question_citations",
        back_populates="cited_in",
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
