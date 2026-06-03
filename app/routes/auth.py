"""Auth routes: register, login, me, invite."""

import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from app.limiter import limiter
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import COOKIE_NAME, create_access_token, get_current_user, hash_password, verify_password, needs_rehash
from app.config import get_settings
from app.db import get_db
from app.models import Invite, Workspace, User
from app.services.audit import log_event
from app.services.email import send_password_reset, send_verification_email
from app.services.jobs import enqueue
from app.utils import LoginVelocityGuard, IPSprayGuard, real_ip

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _check_password(password: str) -> None:
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if not re.search(r'[A-Z]', password):
        raise HTTPException(status_code=400, detail="Password must contain at least one uppercase letter")
    if not re.search(r'[0-9]', password):
        raise HTTPException(status_code=400, detail="Password must contain at least one number")
    if not re.search(r'[^A-Za-z0-9]', password):
        raise HTTPException(status_code=400, detail="Password must contain at least one symbol (e.g. !@#$)")


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    workspace_name: str = ""
    org_name: str = ""
    invite_token: str = ""
    workspace_type: str = "consultant"
class LoginRequest(BaseModel):
    email: str
    password: str


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug[:64] or "workspace"


CSRF_COOKIE_NAME = "greenlight_csrf"


def _set_auth_cookie(response: Response, token: str) -> None:
    import secrets
    from app.config import get_settings
    settings = get_settings()
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.https_only,
        samesite="strict",
        max_age=7 * 24 * 60 * 60,
        path="/",
    )
    # CSRF token: readable by JS so the frontend can send it as a header.
    # SameSite=Strict already blocks cross-site cookie delivery; this adds
    # a second layer (double-submit cookie pattern).
    csrf_token = secrets.token_urlsafe(32)
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,   # must be readable by JS
        secure=settings.https_only,
        samesite="strict",
        max_age=7 * 24 * 60 * 60,
        path="/",
    )


def _user_payload(user: User, workspace: Workspace) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name or "",
        "role": user.role,
        "workspace_id": user.workspace_id,
        "workspace_name": workspace.name if workspace else "",
        "org_name": workspace.name if workspace else "",
        "workspace_slug": workspace.slug if workspace else "",
        "workspace_type": workspace.workspace_type if workspace else "consultant",
        "email_verified": user.email_verified,
    }


async def _seed_answer_library(workspace_id: int) -> None:
    """Seed the AU-focused answer library for a new workspace. Runs as a background task."""
    try:
        from scripts.seed_answer_library import main as _seed_main
        await _seed_main(workspace_id)
        # After seeding, expand with question phrasing variations
        try:
            from scripts.expand_seed_variations import main as _expand_main
            await _expand_main(workspace_id)
        except Exception as expand_exc:
            print(f"[seed] Variation expansion failed for workspace {workspace_id}: {expand_exc}")
    except Exception as exc:
        print(f"[seed] Answer library seeding failed for workspace {workspace_id}: {exc}")


@router.post("/register")
@limiter.limit("5/minute")
async def register(request: Request, req: RegisterRequest, response: Response, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if not req.email.strip() or "@" not in req.email:
        raise HTTPException(status_code=400, detail="Valid email required")
    _check_password(req.password)
    if db.query(User).filter(User.email == req.email.lower().strip()).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    new_workspace_id: int | None = None
    invite: Invite | None = None
    if req.invite_token:
        token_hash = hashlib.sha256(req.invite_token.strip().encode()).hexdigest()
        invite = db.query(Invite).filter(Invite.token_hash == token_hash).first()
        if not invite:
            raise HTTPException(status_code=404, detail="Invite link not found or already used")
        if invite.revoked_at:
            raise HTTPException(status_code=400, detail="This invite link has been revoked")
        if invite.used_at:
            raise HTTPException(status_code=400, detail="This invite link has already been used")
        if invite.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="This invite link has expired")
        workspace = db.query(Workspace).filter(Workspace.id == invite.workspace_id).first()
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        role = "member"
    else:
        workspace_name = (req.workspace_name or req.org_name).strip()
        if not workspace_name:
            raise HTTPException(status_code=400, detail="Workspace name required")
        base_slug = _slugify(workspace_name)
        slug = base_slug
        counter = 1
        while db.query(Workspace).filter(Workspace.slug == slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        workspace = Workspace(name=workspace_name, slug=slug, workspace_type=req.workspace_type if req.workspace_type in ("consultant", "company") else "consultant")
        db.add(workspace)
        db.flush()
        role = "owner"
        new_workspace_id = workspace.id

    user = User(
        email=req.email.lower().strip(),
        hashed_password=hash_password(req.password),
        full_name=req.full_name.strip() or None,
        role=role,
        workspace_id=workspace.id,
    )
    db.add(user)
    db.flush()
    if invite:
        invite.used_at = datetime.now(timezone.utc)
        invite.used_by_id = user.id
    log_event(db, workspace_id=workspace.id, user_id=user.id, user_email=user.email,
              action="auth.register", resource_type="auth",
              detail={"role": role, "workspace_name": workspace.name})
    db.commit()
    db.refresh(user)

    # Seed AU answer library for new workspaces
    if new_workspace_id is not None:
        background_tasks.add_task(_seed_answer_library, new_workspace_id)

    # Send verification email via persistent job queue
    verification_token = secrets.token_urlsafe(32)
    user.verification_token_hash    = _hash_token(verification_token)
    user.verification_token_expires = datetime.now(timezone.utc) + timedelta(hours=24)
    db.commit()

    from app.config import get_settings
    verify_url = f"{get_settings().app_url}/verify-email?token={verification_token}"
    enqueue("send_verification_email", {"email": user.email, "url": verify_url, "name": user.full_name or ""})

    token = create_access_token(user.id, user.workspace_id)
    _set_auth_cookie(response, token)
    return {"user": _user_payload(user, workspace)}


@router.post("/login")
@limiter.limit("10/minute")
def login(request: Request, req: LoginRequest, response: Response, db: Session = Depends(get_db)):
    email = req.email.lower().strip()
    ip    = real_ip(request)

    # Layer 1 — per-IP spray guard: blocks password spraying across many emails
    if IPSprayGuard.is_blocked(ip):
        log_event(db, workspace_id=0, user_id=None, user_email=email,
                  action="auth.login_blocked", resource_type="auth",
                  detail={"reason": "ip_spray_guard", "ip": ip})
        raise HTTPException(status_code=429, detail="Too many failed attempts — try again in 15 minutes")

    # Layer 2 — per-email velocity guard: blocks credential stuffing across rotating IPs
    if LoginVelocityGuard.is_locked(email):
        log_event(db, workspace_id=0, user_id=None, user_email=email,
                  action="auth.login_blocked", resource_type="auth",
                  detail={"reason": "email_velocity_guard", "ip": ip})
        raise HTTPException(status_code=429, detail="Too many failed attempts — try again in 15 minutes")

    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        LoginVelocityGuard.record_failure(email)
        IPSprayGuard.record_failure(ip)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    # Successful login: clear the per-email failure counter
    # (IPSprayGuard is intentionally NOT reset — one success doesn't undo spray activity)
    LoginVelocityGuard.reset_on_success(email)

    # Transparent migration: upgrade legacy bcrypt hash to Argon2 on login
    if needs_rehash(user.hashed_password):
        user.hashed_password = hash_password(req.password)

    workspace = db.query(Workspace).filter(Workspace.id == user.workspace_id).first()
    log_event(db, workspace_id=user.workspace_id, user_id=user.id, user_email=user.email,
              action="auth.login", resource_type="auth")
    db.commit()
    token = create_access_token(user.id, user.workspace_id)
    _set_auth_cookie(response, token)
    return {"user": _user_payload(user, workspace)}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key=COOKIE_NAME, path="/")
    return {"status": "ok"}


@router.get("/me")
def me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    workspace = db.query(Workspace).filter(Workspace.id == current_user.workspace_id).first()
    return _user_payload(current_user, workspace)


# ── Password reset ────────────────────────────────────────────────────────────

class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


@router.post("/forgot-password")
@limiter.limit("3/minute;5/hour")
def forgot_password(request: Request, req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email.lower().strip()).first()

    # Always return success — never reveal whether email exists
    if not user or not user.is_active:
        return {"status": "ok"}

    # Generate cryptographically random token, store only its hash
    token = secrets.token_urlsafe(32)
    user.reset_token_hash    = _hash_token(token)
    user.reset_token_expires = datetime.now(timezone.utc) + timedelta(minutes=15)
    db.commit()

    from app.config import get_settings
    reset_url = f"{get_settings().app_url}/reset-password?token={token}"
    try:
        send_password_reset(user.email, reset_url, user.full_name or "")
    except Exception as e:
        print(f"[email] Failed to send reset email: {e}")

    return {"status": "ok"}


@router.post("/reset-password")
@limiter.limit("5/minute")
def reset_password(request: Request, req: ResetPasswordRequest, db: Session = Depends(get_db)):
    _check_password(req.new_password)

    token_hash = _hash_token(req.token)
    user = db.query(User).filter(User.reset_token_hash == token_hash).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")

    if not user.reset_token_expires or datetime.now(timezone.utc) > user.reset_token_expires:
        raise HTTPException(status_code=400, detail="Reset link has expired — request a new one")

    user.hashed_password     = hash_password(req.new_password)
    user.reset_token_hash    = None   # single-use — invalidate immediately
    user.reset_token_expires = None
    log_event(db, workspace_id=user.workspace_id, user_id=user.id, user_email=user.email,
              action="auth.password_reset", resource_type="auth")
    db.commit()
    return {"status": "ok"}


@router.post("/change-password")
def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_password(req.new_password)

    if not verify_password(req.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    current_user.hashed_password = hash_password(req.new_password)
    log_event(db, workspace_id=current_user.workspace_id, user_id=current_user.id, user_email=current_user.email,
              action="auth.password_changed", resource_type="auth")
    db.commit()
    return {"status": "ok"}


# ── Team management ───────────────────────────────────────────────────────────

@router.get("/team")
def list_team(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    members = (
        db.query(User)
        .filter(User.workspace_id == current_user.workspace_id, User.is_active == True)
        .order_by(User.created_at)
        .all()
    )
    return [
        {
            "id": m.id,
            "email": m.email,
            "full_name": m.full_name or "",
            "role": m.role,
            "created_at": m.created_at.isoformat(),
        }
        for m in members
    ]


class ChangeRoleRequest(BaseModel):
    role: str  # "owner" | "admin" | "member"


@router.patch("/team/{user_id}/role")
def change_role(
    user_id: int,
    req: ChangeRoleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if req.role not in ("owner", "admin", "member"):
        raise HTTPException(status_code=400, detail="Invalid role")

    # Only owner can change roles
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only the workspace owner can change roles")

    # Can't change your own role
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot change your own role")

    target = db.query(User).filter(
        User.id == user_id,
        User.workspace_id == current_user.workspace_id,
    ).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    old_role = target.role

    # Ownership transfer: demote current owner to admin first
    if req.role == "owner":
        current_user.role = "admin"

    target.role = req.role

    log_event(db, workspace_id=current_user.workspace_id, user_id=current_user.id, user_email=current_user.email,
              action="team.role_changed", resource_type="auth",
              detail={"target_email": target.email, "from": old_role, "to": req.role})
    db.commit()

    workspace = db.query(Workspace).filter(Workspace.id == current_user.workspace_id).first()
    return {
        "updated": {"id": target.id, "email": target.email, "role": target.role},
        "you": _user_payload(current_user, workspace),
    }


# ── Email verification ────────────────────────────────────────────────────────

class VerifyEmailRequest(BaseModel):
    token: str


@router.post("/verify-email")
def verify_email(req: VerifyEmailRequest, db: Session = Depends(get_db)):
    token_hash = _hash_token(req.token)
    user = db.query(User).filter(User.verification_token_hash == token_hash).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired verification link")
    if not user.verification_token_expires or datetime.now(timezone.utc) > user.verification_token_expires:
        raise HTTPException(status_code=400, detail="Verification link has expired — request a new one")

    user.email_verified             = True
    user.verification_token_hash    = None
    user.verification_token_expires = None
    log_event(db, workspace_id=user.workspace_id, user_id=user.id, user_email=user.email,
              action="auth.email_verified", resource_type="auth")
    db.commit()
    return {"status": "ok"}


@router.post("/resend-verification")
@limiter.limit("3/hour")
def resend_verification(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.email_verified:
        return {"status": "ok"}

    token = secrets.token_urlsafe(32)
    current_user.verification_token_hash    = _hash_token(token)
    current_user.verification_token_expires = datetime.now(timezone.utc) + timedelta(hours=24)
    db.commit()

    from app.config import get_settings
    verify_url = f"{get_settings().app_url}/verify-email?token={token}"
    enqueue("send_verification_email", {"email": current_user.email, "url": verify_url, "name": current_user.full_name or ""})
    return {"status": "ok"}


# ── Invites ───────────────────────────────────────────────────────────────────

@router.post("/invites")
def create_invite(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Only owners and admins can create invites")

    token = secrets.token_hex(32)  # 64-char hex, shown once
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    invite = Invite(
        workspace_id=current_user.workspace_id,
        created_by_id=current_user.id,
        created_by_email=current_user.email,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=48),
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)

    settings = get_settings()
    return {
        "id": invite.id,
        "url": f"{settings.app_url}/invite/{token}",
        "expires_at": invite.expires_at.isoformat(),
    }


@router.get("/invites")
def list_invites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Only owners and admins can view invites")

    invites = (
        db.query(Invite)
        .filter(Invite.workspace_id == current_user.workspace_id)
        .order_by(Invite.created_at.desc())
        .limit(50)
        .all()
    )
    now = datetime.now(timezone.utc)
    return [
        {
            "id": i.id,
            "created_at": i.created_at.isoformat(),
            "expires_at": i.expires_at.isoformat(),
            "created_by_email": i.created_by_email,
            "status": (
                "used"    if i.used_at    else
                "revoked" if i.revoked_at else
                "expired" if i.expires_at < now else
                "active"
            ),
        }
        for i in invites
    ]


@router.delete("/invites/{invite_id}")
def revoke_invite(
    invite_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Only owners and admins can revoke invites")

    invite = db.query(Invite).filter(
        Invite.id == invite_id,
        Invite.workspace_id == current_user.workspace_id,
    ).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    if invite.used_at:
        raise HTTPException(status_code=400, detail="Cannot revoke an already-used invite")

    invite.revoked_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "revoked"}


@router.get("/invites/validate/{token}")
def validate_invite(token: str, db: Session = Depends(get_db)):
    """Public endpoint — returns workspace name so the invite page can greet the user."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    invite = db.query(Invite).filter(Invite.token_hash == token_hash).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite link not found")
    if invite.revoked_at:
        raise HTTPException(status_code=400, detail="This invite link has been revoked")
    if invite.used_at:
        raise HTTPException(status_code=400, detail="This invite link has already been used")
    if invite.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="This invite link has expired")

    workspace = db.query(Workspace).filter(Workspace.id == invite.workspace_id).first()
    return {"workspace_name": workspace.name if workspace else "Unknown", "expires_at": invite.expires_at.isoformat()}
