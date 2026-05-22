"""Email delivery via Resend."""

import resend
from app.config import get_settings


def _send(payload: dict) -> None:
    settings = get_settings()
    resend.api_key = settings.resend_api_key
    resend.Emails.send(payload)


def send_restore_notification(owner_email: str, owner_name: str, item_type: str, item_name: str, restored_by_email: str) -> None:
    settings = get_settings()
    _send({
        "from": settings.resend_from_email,
        "to": [owner_email],
        "subject": f"[Greenlight] {item_type} restored — {item_name}",
        "html": f"""
        <div style="font-family:Inter,sans-serif;max-width:480px;margin:0 auto;padding:32px 24px;color:#111827">
          <div style="margin-bottom:24px">
            <span style="background:#2563eb;color:white;padding:6px 14px;border-radius:8px;font-weight:700;font-size:14px">
              Greenlight
            </span>
          </div>
          <h1 style="font-size:22px;font-weight:700;margin:0 0 8px">Item restored</h1>
          <p style="color:#6b7280;margin:0 0 16px">
            Hi {owner_name or owner_email}, this is an automatic security notice.
          </p>
          <div style="background:#fefce8;border:1px solid #fde047;border-radius:10px;padding:16px;margin-bottom:24px">
            <p style="margin:0;font-size:14px;color:#713f12">
              <strong>{restored_by_email}</strong> restored a deleted {item_type.lower()}:<br/>
              <strong>{item_name}</strong>
            </p>
          </div>
          <p style="color:#6b7280;font-size:13px">
            If you did not authorise this action, review your team's access immediately and contact support.
          </p>
        </div>
        """,
    })


def send_verification_email(to_email: str, verify_url: str, full_name: str) -> None:
    settings = get_settings()
    _send({
        "from": settings.resend_from_email,
        "to": [to_email],
        "subject": "Verify your Greenlight email address",
        "html": f"""
        <div style="font-family:Inter,sans-serif;max-width:480px;margin:0 auto;padding:32px 24px;color:#111827">
          <div style="margin-bottom:24px">
            <span style="background:#2563eb;color:white;padding:6px 14px;border-radius:8px;font-weight:700;font-size:14px">
              Greenlight
            </span>
          </div>

          <h1 style="font-size:22px;font-weight:700;margin:0 0 8px">Verify your email</h1>
          <p style="color:#6b7280;margin:0 0 24px">
            Hi {full_name or to_email}, click the button below to verify your email address.
            This link expires in <strong>24 hours</strong>.
          </p>

          <a href="{verify_url}"
             style="display:inline-block;background:#2563eb;color:white;padding:12px 28px;
                    border-radius:10px;font-weight:600;font-size:14px;text-decoration:none">
            Verify Email
          </a>

          <p style="color:#9ca3af;font-size:12px;margin-top:32px">
            If you didn't create a Greenlight account, you can ignore this email.
          </p>
        </div>
        """,
    })


def send_password_reset(to_email: str, reset_url: str, full_name: str) -> None:
    settings = get_settings()
    _send({
        "from": settings.resend_from_email,
        "to": [to_email],
        "subject": "Reset your Greenlight password",
        "html": f"""
        <div style="font-family:Inter,sans-serif;max-width:480px;margin:0 auto;padding:32px 24px;color:#111827">
          <div style="margin-bottom:24px">
            <span style="background:#2563eb;color:white;padding:6px 14px;border-radius:8px;font-weight:700;font-size:14px">
              Greenlight
            </span>
          </div>

          <h1 style="font-size:22px;font-weight:700;margin:0 0 8px">Reset your password</h1>
          <p style="color:#6b7280;margin:0 0 24px">
            Hi {full_name or to_email}, we received a request to reset your password.
            This link expires in <strong>15 minutes</strong>.
          </p>

          <a href="{reset_url}"
             style="display:inline-block;background:#2563eb;color:white;padding:12px 28px;
                    border-radius:10px;font-weight:600;font-size:14px;text-decoration:none">
            Reset Password
          </a>

          <p style="color:#9ca3af;font-size:12px;margin-top:32px">
            If you didn't request this, ignore this email — your password won't change.<br>
            Link: {reset_url}
          </p>
        </div>
        """,
    })


def send_generation_complete(
    to_email: str,
    user_name: str,
    questionnaire_name: str,
    total: int,
    conflicts: int,
    questionnaire_url: str,
) -> None:
    settings = get_settings()
    conflict_note = (
        f'<div style="background:#fef3c7;border:1px solid #fcd34d;border-radius:10px;padding:14px;margin-bottom:20px">'
        f'<p style="margin:0;font-size:13px;color:#92400e">'
        f'⚠ <strong>{conflicts} question{"s" if conflicts != 1 else ""}</strong> flagged a potential conflict with a '
        f'previously approved answer. Review these carefully before approving.</p></div>'
        if conflicts else ""
    )
    _send({
        "from": settings.resend_from_email,
        "to": [to_email],
        "subject": f"[Greenlight] Drafts ready — {questionnaire_name}",
        "html": f"""
        <div style="font-family:Inter,sans-serif;max-width:480px;margin:0 auto;padding:32px 24px;color:#111827">
          <div style="margin-bottom:24px">
            <span style="background:#2563eb;color:white;padding:6px 14px;border-radius:8px;font-weight:700;font-size:14px">
              Greenlight
            </span>
          </div>
          <h1 style="font-size:22px;font-weight:700;margin:0 0 8px">Drafts ready for review</h1>
          <p style="color:#6b7280;margin:0 0 20px">
            Hi {user_name or to_email}, draft answers are ready for <strong>{questionnaire_name}</strong>.
            {total} question{"s are" if total != 1 else " is"} ready for your review.
          </p>
          {conflict_note}
          <a href="{questionnaire_url}"
             style="display:inline-block;background:#2563eb;color:white;padding:12px 28px;
                    border-radius:10px;font-weight:600;font-size:14px;text-decoration:none">
            Review Answers
          </a>
          <p style="color:#9ca3af;font-size:12px;margin-top:32px">
            Remember: no answer is included in your export until you explicitly approve it.
          </p>
        </div>
        """,
    })


def send_question_assigned(
    to_email: str,
    assignee_name: str,
    assignor_name: str,
    questionnaire_name: str,
    question_text: str,
    questionnaire_url: str,
) -> None:
    settings = get_settings()
    short_q = question_text[:160] + ("…" if len(question_text) > 160 else "")
    _send({
        "from": settings.resend_from_email,
        "to": [to_email],
        "subject": f"You've been assigned a question — {questionnaire_name}",
        "html": f"""
        <div style="font-family:Inter,sans-serif;max-width:480px;margin:0 auto;padding:32px 24px;color:#111827">
          <div style="margin-bottom:24px">
            <span style="background:#2563eb;color:white;padding:6px 14px;border-radius:8px;font-weight:700;font-size:14px">
              Greenlight
            </span>
          </div>

          <h1 style="font-size:22px;font-weight:700;margin:0 0 8px">Question assigned to you</h1>
          <p style="color:#6b7280;margin:0 0 20px">
            Hi {assignee_name or to_email}, <strong>{assignor_name}</strong> assigned you a question
            in <strong>{questionnaire_name}</strong>.
          </p>

          <div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:10px;padding:16px;margin-bottom:24px">
            <p style="font-size:13px;color:#374151;margin:0;font-style:italic">"{short_q}"</p>
          </div>

          <a href="{questionnaire_url}"
             style="display:inline-block;background:#2563eb;color:white;padding:12px 28px;
                    border-radius:10px;font-weight:600;font-size:14px;text-decoration:none">
            View &amp; Answer
          </a>

          <p style="color:#9ca3af;font-size:12px;margin-top:32px">
            You can find all your assigned questions under <em>My Assignments</em> in Greenlight.
          </p>
        </div>
        """,
    })
