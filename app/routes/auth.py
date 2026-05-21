"""Auth routes: register, login, me, invite."""

import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from app.limiter import limiter
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import COOKIE_NAME, create_access_token, get_current_user, hash_password, verify_password, needs_rehash
from app.db import get_db
from app.models import Organization, User
from app.services.audit import log_event
from app.services.email import send_password_reset, send_verification_email

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
    org_name: str = ""
    invite_slug: str = ""


class LoginRequest(BaseModel):
    email: str
    password: str


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug[:64] or "org"


def _set_auth_cookie(response: Response, token: str) -> None:
    from app.config import get_settings
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=get_settings().https_only,  # True in production, False in dev/test
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
        path="/",
    )


def _user_payload(user: User, org: Organization) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name or "",
        "role": user.role,
        "org_id": user.org_id,
        "org_name": org.name if org else "",
        "org_slug": org.slug if org else "",
        "email_verified": user.email_verified,
    }


@router.post("/register")
@limiter.limit("5/minute")
async def register(request: Request, req: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    if not req.email.strip() or "@" not in req.email:
        raise HTTPException(status_code=400, detail="Valid email required")
    _check_password(req.password)
    if db.query(User).filter(User.email == req.email.lower().strip()).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    new_org_id: int | None = None
    if req.invite_slug:
        org = db.query(Organization).filter(Organization.slug == req.invite_slug.strip()).first()
        if not org:
            raise HTTPException(status_code=404, detail="Invite code not found")
        role = "member"
    else:
        if not req.org_name.strip():
            raise HTTPException(status_code=400, detail="Organization name required")
        base_slug = _slugify(req.org_name)
        slug = base_slug
        counter = 1
        while db.query(Organization).filter(Organization.slug == slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        org = Organization(name=req.org_name.strip(), slug=slug)
        db.add(org)
        db.flush()
        role = "owner"
        new_org_id = org.id

    user = User(
        email=req.email.lower().strip(),
        hashed_password=hash_password(req.password),
        full_name=req.full_name.strip() or None,
        role=role,
        org_id=org.id,
    )
    db.add(user)
    db.flush()
    log_event(db, org_id=org.id, user_id=user.id, user_email=user.email,
              action="auth.register", resource_type="auth",
              detail={"role": role, "org_name": org.name})
    db.commit()
    db.refresh(user)

    from app.services.jobs import enqueue
    if new_org_id is not None:
        enqueue("seed_starter_policies", {"org_id": new_org_id})

    # Send verification email via persistent job queue
    verification_token = secrets.token_urlsafe(32)
    user.verification_token_hash    = _hash_token(verification_token)
    user.verification_token_expires = datetime.now(timezone.utc) + timedelta(hours=24)
    db.commit()

    from app.config import get_settings
    verify_url = f"{get_settings().app_url}/verify-email?token={verification_token}"
    enqueue("send_verification_email", {"email": user.email, "url": verify_url, "name": user.full_name or ""})

    token = create_access_token(user.id, user.org_id)
    _set_auth_cookie(response, token)
    return {"user": _user_payload(user, org)}


@router.post("/login")
@limiter.limit("10/minute")
def login(request: Request, req: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email.lower().strip()).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    # Transparent migration: upgrade legacy bcrypt hash to Argon2 on login
    if needs_rehash(user.hashed_password):
        user.hashed_password = hash_password(req.password)

    org = db.query(Organization).filter(Organization.id == user.org_id).first()
    log_event(db, org_id=user.org_id, user_id=user.id, user_email=user.email,
              action="auth.login", resource_type="auth")
    db.commit()
    token = create_access_token(user.id, user.org_id)
    _set_auth_cookie(response, token)
    return {"user": _user_payload(user, org)}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key=COOKIE_NAME, path="/")
    return {"status": "ok"}


@router.get("/me")
def me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == current_user.org_id).first()
    return _user_payload(current_user, org)


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
    log_event(db, org_id=user.org_id, user_id=user.id, user_email=user.email,
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
    log_event(db, org_id=current_user.org_id, user_id=current_user.id, user_email=current_user.email,
              action="auth.password_changed", resource_type="auth")
    db.commit()
    return {"status": "ok"}


# ── Team management ───────────────────────────────────────────────────────────

@router.get("/team")
def list_team(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    members = (
        db.query(User)
        .filter(User.org_id == current_user.org_id, User.is_active == True)
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
        User.org_id == current_user.org_id,
    ).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    old_role = target.role

    # Ownership transfer: demote current owner to admin first
    if req.role == "owner":
        current_user.role = "admin"

    target.role = req.role

    log_event(db, org_id=current_user.org_id, user_id=current_user.id, user_email=current_user.email,
              action="team.role_changed", resource_type="auth",
              detail={"target_email": target.email, "from": old_role, "to": req.role})
    db.commit()

    org = db.query(Organization).filter(Organization.id == current_user.org_id).first()
    return {
        "updated": {"id": target.id, "email": target.email, "role": target.role},
        "you": _user_payload(current_user, org),
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
    log_event(db, org_id=user.org_id, user_id=user.id, user_email=user.email,
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
    from app.services.jobs import enqueue
    verify_url = f"{get_settings().app_url}/verify-email?token={token}"
    enqueue("send_verification_email", {"email": current_user.email, "url": verify_url, "name": current_user.full_name or ""})
    return {"status": "ok"}
