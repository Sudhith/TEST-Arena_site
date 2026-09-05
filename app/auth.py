"""
app/auth.py
───────────
User registration, login (digit + grid variants), logout,
and the get_current_user dependency used by protected routes.

Session cookies are signed with itsdangerous.URLSafeTimedSerializer
so they can't be forged, and they expire after settings.session_ttl_seconds.
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request, Response, status
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from passlib.context import CryptContext
from sqlmodel import Session, select

from app.config import get_settings
from app.db import User, get_session

settings = get_settings()

# ── Password hashing ──────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── Signed session cookie ─────────────────────────────────────────────────────
_COOKIE_NAME = "captcha_session"
_serializer = URLSafeTimedSerializer(settings.secret_key)


def set_session_cookie(response: Response, user_id: int) -> None:
    """Sign and set the session cookie on the response."""
    token = _serializer.dumps({"user_id": user_id})
    response.set_cookie(
        key=_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=(settings.environment == "production"),
        max_age=settings.session_ttl_seconds,
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(_COOKIE_NAME)


def _decode_cookie(request: Request) -> Optional[int]:
    """
    Read and verify the session cookie.
    Returns user_id on success, None on missing / expired / tampered cookie.
    """
    token = request.cookies.get(_COOKIE_NAME)
    if not token:
        return None
    try:
        data = _serializer.loads(token, max_age=settings.session_ttl_seconds)
        return data.get("user_id")
    except (SignatureExpired, BadSignature):
        return None


# ── FastAPI dependencies ──────────────────────────────────────────────────────

def get_current_user(
    request: Request,
    db: Session = Depends(get_session),
) -> User:
    """
    Protected-route dependency.
    Raises 401 if the cookie is missing, expired, or invalid.
    """
    user_id = _decode_cookie(request)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please log in.",
        )
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found.",
        )
    return user


def get_optional_user(
    request: Request,
    db: Session = Depends(get_session),
) -> Optional[User]:
    """Like get_current_user but returns None instead of raising."""
    user_id = _decode_cookie(request)
    if user_id is None:
        return None
    return db.get(User, user_id)


# ── Core auth logic ───────────────────────────────────────────────────────────

def register_user(username: str, password: str, db: Session) -> User:
    """
    Create a new user.
    Raises ValueError if the username is already taken.
    """
    existing = db.exec(select(User).where(User.username == username)).first()
    if existing:
        raise ValueError(f"Username '{username}' is already taken.")
    user = User(username=username, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(username: str, password: str, db: Session) -> Optional[User]:
    """
    Verify credentials.
    Returns the User on success, None on failure.
    """
    user = db.exec(select(User).where(User.username == username)).first()
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
