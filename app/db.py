"""
app/db.py
─────────
SQLite (or Postgres) database setup using SQLModel.
Tables:
  - User           — registered accounts
  - CaptchaSession — live CAPTCHA challenges (expires after TTL)
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, Session, SQLModel, create_engine, select

from app.config import get_settings

settings = get_settings()

# ── Engine ────────────────────────────────────────────────────────────────────
# SQLite needs check_same_thread=False for FastAPI's async handlers.
# For Postgres, connect_args is ignored.
connect_args = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    echo=(settings.environment == "development"),
)


# ── Models ────────────────────────────────────────────────────────────────────

class User(SQLModel, table=True):
    """Registered user account."""

    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, max_length=64)
    password_hash: str = Field(max_length=128)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CaptchaSession(SQLModel, table=True):
    """
    A live CAPTCHA challenge.

    - For the digit CAPTCHA: captcha_answer stores the 6-digit string.
    - For the grid CAPTCHA:  captcha_answer stores JSON of the shuffled
      image list (path + categories per tile).

    user_id is nullable so that API-only solver flows (no logged-in user)
    can fetch and verify challenges without registering.
    """

    __tablename__ = "captcha_sessions"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        max_length=36,
    )
    user_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    captcha_type: str = Field(max_length=8)          # "digit" | "grid"
    captcha_answer: str = Field()                     # digit string or JSON blob
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field()                    # set to now + TTL on creation


# ── Helpers ───────────────────────────────────────────────────────────────────

def create_db_and_tables() -> None:
    """Create all tables if they don't exist yet. Called once at startup."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI dependency: yields a DB session, closes it after the request."""
    with Session(engine) as session:
        yield session


def purge_expired_sessions(db: Session) -> int:
    """
    Delete all CaptchaSession rows whose expires_at is in the past.
    Called lazily before creating a new session to keep the table lean.
    Returns the number of rows deleted.
    """
    now = datetime.now(timezone.utc)
    expired = db.exec(
        select(CaptchaSession).where(CaptchaSession.expires_at < now)
    ).all()
    for row in expired:
        db.delete(row)
    db.commit()
    return len(expired)
