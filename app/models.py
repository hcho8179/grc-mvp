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
    Boolean,
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
# Organization  (tenant)
# ---------------------------------------------------------------------------

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    name = Column(String(256), nullable=False)
    slug = Column(String(64), unique=True, index=True, nullable=False)
    white_label_export = Column(Boolean, default=False, nullable=False, server_default="false")

    users = relationship("User", back_populates="org", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    email = Column(String(256), unique=True, index=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    full_name = Column(String(256), nullable=True)
    role = Column(String(32), default="member", nullable=False)  # owner | admin | member
    is_active = Column(Boolean, default=True, nullable=False)

    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    org = relationship("Organization", back_populates="users")

    # Email verification
    email_verified             = Column(Boolean, default=False, nullable=False, server_default="false")
    verification_token_hash    = Column(String(256), nullable=True, index=True)
    verification_token_expires = Column(DateTime(timezone=True), nullable=True)

    # Password reset — token stored as SHA-256 hash, never plaintext
    reset_token_hash    = Column(String(256), nullable=True, index=True)
    reset_token_expires = Column(DateTime(timezone=True), nullable=True)


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
    is_starter = Column(Boolean, default=False, nullable=False, server_default="false")
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)

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


class QuestionnaireTemplate(Base):
    """Saved layout + format for a customer's questionnaire format."""
    __tablename__ = "questionnaire_templates"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    name = Column(String(256), nullable=False)
    customer_name = Column(String(256), nullable=True, index=True)
    question_col = Column(Integer, nullable=False)   # 0-based
    answer_col = Column(Integer, nullable=True)      # 0-based
    format_config = Column(JSON, nullable=True)      # merged_cells, column_widths, row_heights
    times_used = Column(Integer, default=0, nullable=False)

    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)


class Questionnaire(Base):
    __tablename__ = "questionnaires"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    name = Column(String(512), nullable=False)
    customer_name = Column(String(256), nullable=True)
    source_filename = Column(String(512), nullable=False)
    status = Column(Enum(QuestionnaireStatus), default=QuestionnaireStatus.draft, nullable=False)
    question_count = Column(Integer, default=0, nullable=False)
    raw_xlsx_blob = Column(LargeBinary, nullable=True)  # legacy — new uploads use raw_xlsx_key
    raw_xlsx_key  = Column(String(512), nullable=True)  # S3 object key
    deleted_at    = Column(DateTime(timezone=True), nullable=True, index=True)
    share_token   = Column(String(64), unique=True, nullable=True, index=True)
    answer_col_index = Column(Integer, nullable=True)            # 0-based; primary answer col (Yes/No when two cols selected)
    secondary_answer_col_index = Column(Integer, nullable=True)  # 0-based; evidence/comments col (full answer goes here)
    question_col_index = Column(Integer, nullable=True)          # 0-based; which column has questions
    template_id = Column(
        Integer,
        ForeignKey("questionnaire_templates.id", ondelete="SET NULL"),
        nullable=True,
    )

    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)

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
    short_answer = Column(String(32), nullable=True)  # "Yes" | "No" | "Partial" | "N/A" — for Yes/No columns
    final_answer = Column(Text, nullable=True)

    status = Column(Enum(QuestionStatus), default=QuestionStatus.pending, nullable=False)
    confidence = Column(Enum(ConfidenceLevel), nullable=True)
    cited_chunk_ids = Column(JSON, nullable=True)  # list[int] — populated by Phase 4
    reasoning = Column(Text, nullable=True)         # LLM confidence explanation
    conflict_warning = Column(Text, nullable=True)  # set when draft contradicts a prior approved answer
    category = Column(String(64), nullable=True, index=True)  # embedding-classified topic

    # Assignment — nullable; SET NULL when user is deleted
    assigned_to_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    cited_chunks = relationship(
        "KnowledgeChunk",
        secondary="question_citations",
        back_populates="cited_in",
    )
    comments = relationship(
        "QuestionComment",
        back_populates="question",
        cascade="all, delete-orphan",
        passive_deletes=True,
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
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)


# ---------------------------------------------------------------------------
# ApprovedAnswer — persistent answer library (Phase 7)
# ---------------------------------------------------------------------------

class ApprovedAnswer(Base):
    __tablename__ = "approved_answers"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    question_text = Column(Text, nullable=False)
    answer_text = Column(Text, nullable=False)
    short_answer = Column(String(32), nullable=True)        # Yes | No | Partial | N/A
    answer_category = Column(String(100), nullable=True)   # auto-detected from question text
    cited_chunk_ids = Column(JSON, nullable=True)
    confidence_score = Column(Float, nullable=True)        # 0-1 float
    times_reused = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="active", nullable=False)  # active | archived

    # Embedding of question_text only — used for answer-reuse similarity search
    embedding = Column(Vector(EMBEDDING_DIM), nullable=True)

    source_question_id = Column(
        Integer,
        ForeignKey("questions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)


# ---------------------------------------------------------------------------
# AuditLog — immutable event trail
# ---------------------------------------------------------------------------

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user_email = Column(String(256), nullable=True)   # denormalized so it survives user deletion

    action = Column(String(64), nullable=False, index=True)   # e.g. "question.approved"
    resource_type = Column(String(64), nullable=True)         # "question" | "questionnaire" | "document" | "auth"
    resource_id = Column(Integer, nullable=True)
    detail = Column(JSON, nullable=True)                       # arbitrary extra context


# ---------------------------------------------------------------------------
# QuestionComment — threaded comments on a single question
# ---------------------------------------------------------------------------

class QuestionComment(Base):
    __tablename__ = "question_comments"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    questionnaire_id = Column(Integer, ForeignKey("questionnaires.id", ondelete="CASCADE"), nullable=False, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user_email = Column(String(256), nullable=True)   # denormalized — survives user deletion
    user_name = Column(String(256), nullable=True)

    body = Column(Text, nullable=False)

    question = relationship("Question", back_populates="comments")


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


# ---------------------------------------------------------------------------
# Invite — one-time expiring invite links
# ---------------------------------------------------------------------------

class Invite(Base):
    __tablename__ = "invites"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    used_at = Column(DateTime(timezone=True), nullable=True)
    used_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    # Denormalised so the invite page can show who created the invite
    created_by_email = Column(String(256), nullable=True)


# ---------------------------------------------------------------------------
# Job queue  (Postgres-backed — survives server restarts)
# ---------------------------------------------------------------------------

class AnswerVersion(Base):
    __tablename__ = "answer_versions"

    id         = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    org_id      = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id     = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user_email  = Column(String(256), nullable=True)
    user_name   = Column(String(256), nullable=True)

    action       = Column(String(32), nullable=False)  # "edited" | "approved" | "rejected"
    draft_answer = Column(Text, nullable=True)
    short_answer = Column(String(32), nullable=True)


class JobStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    done    = "done"
    failed  = "failed"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    org_id  = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id",         ondelete="CASCADE"), nullable=False, index=True)

    type  = Column(String(64), nullable=False)   # "generation_complete" | "question_assigned"
    title = Column(Text, nullable=False)
    body  = Column(Text, nullable=True)
    read  = Column(Boolean, default=False, nullable=False, server_default="false")

    resource_type = Column(String(64), nullable=True)   # "questionnaire" | "question"
    resource_id   = Column(Integer, nullable=True)


class JobQueue(Base):
    __tablename__ = "job_queue"

    id         = Column(Integer, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    job_type   = Column(String(64), nullable=False, index=True)
    payload    = Column(JSON, nullable=False, default=dict)
    status     = Column(Enum(JobStatus), default=JobStatus.pending, nullable=False, index=True)
    attempts   = Column(Integer, default=0, nullable=False)
    last_error = Column(Text, nullable=True)
    run_after  = Column(DateTime(timezone=True), server_default=func.now())  # for retry backoff
