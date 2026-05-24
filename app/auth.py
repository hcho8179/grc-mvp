"""JWT authentication utilities."""

from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
import bcrypt as _bcrypt
from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models import User

ACCESS_TOKEN_EXPIRE_DAYS = 7
COOKIE_NAME = "greenlight_token"

_ph = PasswordHasher()  # Argon2id, OWASP-recommended defaults


def hash_password(plain: str) -> str:
    return _ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify against Argon2 first. If the stored hash looks like a legacy bcrypt
    hash (starts with $2b$ or $2a$), fall back to bcrypt so existing users
    can still log in. The caller is responsible for re-hashing with Argon2
    on successful bcrypt verification (transparent migration).
    """
    # Argon2 hashes start with $argon2
    if hashed.startswith("$argon2"):
        try:
            return _ph.verify(hashed, plain)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False

    # Legacy bcrypt hash — used by accounts created before the Argon2 migration
    if hashed.startswith(("$2b$", "$2a$")):
        try:
            return _bcrypt.checkpw(plain.encode(), hashed.encode())
        except Exception:
            return False

    return False


def needs_rehash(hashed: str) -> bool:
    """Returns True if the stored hash is legacy bcrypt and should be upgraded."""
    return hashed.startswith(("$2b$", "$2a$"))


def create_access_token(user_id: int, workspace_id: int) -> str:
    settings = get_settings()
    payload = {
        "sub": str(user_id),
        "workspace": workspace_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    settings = get_settings()
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user
