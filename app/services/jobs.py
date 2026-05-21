"""Postgres-backed job queue.

Jobs are rows in `job_queue`. The worker loop runs inside the web process
and polls every 10 seconds. If the server restarts, pending jobs are picked
up on next boot — nothing is lost.

Adding a job:
    enqueue("seed_starter_policies", {"org_id": 123})

Supported job types:
    seed_starter_policies   — seed 20 policy templates for a new org
    send_verification_email — send email verification link
    send_password_reset     — send password reset link (future)
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
    if job.job_type == "seed_starter_policies":
        from app.services.starter_pack import seed_starter_policies
        await seed_starter_policies(job.payload["org_id"])

    elif job.job_type == "send_verification_email":
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

    else:
        raise ValueError(f"Unknown job type: {job.job_type!r}")


async def worker_loop() -> None:
    """Runs forever — polls for pending jobs and executes them."""
    print("[jobs] Worker started")
    while True:
        await asyncio.sleep(POLL_INTERVAL)
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
                .with_for_update(skip_locked=True)  # safe for multiple workers
                .first()
            )
            if not job:
                continue

            job.status   = JobStatus.running
            job.attempts += 1
            db.commit()

        except Exception:
            db.rollback()
            continue
        finally:
            db.close()

        # Run the job outside the DB transaction so slow jobs don't hold locks
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
                # Exponential backoff: retry after 1min, 5min, 25min
                job.status   = JobStatus.pending
                job.run_after = datetime.now(timezone.utc) + timedelta(
                    minutes=5 ** (job.attempts - 1)
                )
                print(f"[jobs] {job.job_type} #{job.id} failed (attempt {job.attempts}), retrying: {exc}")

            db2.merge(job)
            db2.commit()
        finally:
            db2.close()
