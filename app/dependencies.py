"""
app/dependencies.py
───────────────────
Shared FastAPI dependencies and request helpers used across routes.
Centralised here to avoid circular imports.
"""

from fastapi import Depends, Request
from sqlmodel import Session

from app.auth import get_current_user, get_optional_user
from app.db import User, get_session

# Re-export for convenience so routes import from one place
__all__ = [
    "get_session",
    "get_current_user",
    "get_optional_user",
    "require_login",
    "flash",
    "get_flashed",
]


def require_login(user: User = Depends(get_current_user)) -> User:
    """
    Dependency alias for routes that require an authenticated user.
    Usage:  user: User = Depends(require_login)
    """
    return user


# ── Flash messages (lightweight, cookie-free) ─────────────────────────────────
# We store flash messages in request.state so they're available within
# the same request/redirect cycle.  The template reads them via get_flashed().

def flash(request: Request, message: str, category: str = "error") -> None:
    """Attach a flash message to the current request state."""
    if not hasattr(request.state, "flash_messages"):
        request.state.flash_messages = []
    request.state.flash_messages.append({"message": message, "category": category})


def get_flashed(request: Request) -> list[dict]:
    """Return and clear all flash messages from request state."""
    messages = getattr(request.state, "flash_messages", [])
    request.state.flash_messages = []
    return messages
