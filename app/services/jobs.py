"""Postgres-backed job queue.

Jobs are rows in `job_queue`. The worker loop runs inside the web process
and polls every 10 seconds. If the server restarts, pending jobs are picked
up on next boot — nothing is lost.

Supported job types:
    send_verification_email — send email verification link
    send_password_reset     — send password reset link
    send_restore_notification — notify owner when item restored from trash
    generate_questionnaire  — background answer generation
    purge_expired_trash     — hard-delete items in trash > 90 days
    due_date_reminders      — email owners about upcoming due dates
"""

from __future__ import annotations

import asyncio
import traceback
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import JobQueue, JobStatus

MAX_ATTEMPTS = 3
POLL_INTERVAL = 10  # seconds between polls
_last_daily_maintenance: datetime | None = None


def enqueue(job_type: str, payload: dict) -> None:
    """Insert a job into the queue. Call this instead of BackgroundTasks.add_task."""
    db: Session = SessionLocal()
    try:
        db.add(JobQueue(job_type=job_type, payload=payload))
        db.commit()
    finally:
        db.close()


async def _run_job(job: JobQueue) -> None:
    """Dispatch a single job to the correct handler."""
    if job.job_type == "send_verification_email":
        from app.services.email import send_verification_email
        send_verification_email(
            job.payload["email"],
            job.payload["url"],
            job.payload.get("name", ""),
        )

    elif job.job_type == "send_password_reset":
        from app.services.email import send_password_reset
        send_password_reset(
            job.payload["email"],
            job.payload["url"],
            job.payload.get("name", ""),
        )

    elif job.job_type == "send_restore_notification":
        from app.services.email import send_restore_notification
        send_restore_notification(
            job.payload["owner_email"],
            job.payload.get("owner_name", ""),
            job.payload["item_type"],
            job.payload["item_name"],
            job.payload["restored_by_email"],
        )

    elif job.job_type == "generate_questionnaire":
        from app.services.generation_workflow import run_questionnaire_generation
        await run_questionnaire_generation(
            job.payload["questionnaire_id"],
            job.payload["user_id"],
        )

    elif job.job_type == "purge_expired_trash":
        from app.services.maintenance import purge_expired_trash
        db = SessionLocal()
        try:
            purge_expired_trash(db)
        finally:
            db.close()

    elif job.job_type == "due_date_reminders":
        from app.services.maintenance import process_due_date_reminders
        db = SessionLocal()
        try:
            process_due_date_reminders(db)
        finally:
            db.close()

    else:
        raise ValueError(f"Unknown job type: {job.job_type!r}")


async def _maybe_enqueue_daily_maintenance() -> None:
    """Enqueue trash purge + due-date reminders at most once per 24 hours."""
    global _last_daily_maintenance
    now = datetime.now(timezone.utc)
    if _last_daily_maintenance and (now - _last_daily_maintenance) < timedelta(hours=24):
        return
    _last_daily_maintenance = now
    enqueue("purge_expired_trash", {})
    enqueue("due_date_reminders", {})


async def worker_loop() -> None:
    """Runs forever — polls for pending jobs and executes them."""
    print("[jobs] Worker started")
    while True:
        await asyncio.sleep(POLL_INTERVAL)
        await _maybe_enqueue_daily_maintenance()

        db: Session = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            job = (
                db.query(JobQueue)
                .filter(
                    JobQueue.status == JobStatus.pending,
                    JobQueue.attempts < MAX_ATTEMPTS,
                    JobQueue.run_after <= now,
                )
                .order_by(JobQueue.created_at)
                .with_for_update(skip_locked=True)
                .first()
            )
            if not job:
                continue

            job.status = JobStatus.running
            job.attempts += 1
            db.commit()
            db.refresh(job)

        except Exception:
            db.rollback()
            continue
        finally:
            db.close()

        db2: Session = SessionLocal()
        try:
            await _run_job(job)
            job.status = JobStatus.done
            job.last_error = None
            db2.merge(job)
            db2.commit()
            print(f"[jobs] {job.job_type} #{job.id} done")

        except Exception as exc:
            tb = traceback.format_exc()
            job.last_error = str(exc)

            if job.attempts >= MAX_ATTEMPTS:
                job.status = JobStatus.failed
                print(f"[jobs] {job.job_type} #{job.id} failed permanently: {exc}")
            else:
                job.status = JobStatus.pending
                job.run_after = datetime.now(timezone.utc) + timedelta(
                    minutes=5 ** (job.attempts - 1)
                )
                print(f"[jobs] {job.job_type} #{job.id} failed (attempt {job.attempts}), retrying: {exc}")

            db2.merge(job)
            db2.commit()
        finally:
            db2.close()
