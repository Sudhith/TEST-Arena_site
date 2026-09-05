"""
app/captcha_digit.py
────────────────────
6-digit numeric CAPTCHA generation and verification.

Uses the `captcha` PyPI package (lepture/captcha) which produces
distorted digits with dot noise and curved noise lines — matching
the visual style of typical university/bank login CAPTCHAs.

The generated PNG is never served at a URL that reveals the answer;
the route /captcha-image/{session_id} streams bytes server-side.
"""

import io
import secrets
import sys
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlmodel import Session

from app.config import get_settings
from app.db import CaptchaSession, purge_expired_sessions

settings = get_settings()

# ── ImageCaptcha setup ────────────────────────────────────────────────────────
# We try to use DejaVuSans-Bold which is pre-installed on Debian/Ubuntu base
# images (python:3.11-slim).  On Windows dev machines it may not exist at the
# same path, so we fall back to the captcha package's bundled fonts.

_LINUX_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

try:
    from captcha.image import ImageCaptcha

    import os
    _fonts = [_LINUX_FONT] if os.path.exists(_LINUX_FONT) else []
    _captcha_gen = ImageCaptcha(
        width=280,
        height=90,
        fonts=_fonts or None,           # None → use built-in fonts
        font_sizes=(46, 52, 58),
    )
except Exception as exc:  # pragma: no cover
    print(f"[captcha_digit] Failed to init ImageCaptcha: {exc}", file=sys.stderr)
    raise


# ── Public API ────────────────────────────────────────────────────────────────

def generate_digit_captcha() -> tuple[bytes, str]:
    """
    Generate a 6-digit CAPTCHA image.

    Returns:
        (png_bytes, text) where text is the ground-truth 6-digit string.
    """
    text = "".join(secrets.choice("0123456789") for _ in range(6))
    pil_image = _captcha_gen.generate_image(text)
    buf = io.BytesIO()
    pil_image.save(buf, format="PNG")
    return buf.getvalue(), text


def create_digit_session(db: Session, user_id: Optional[int] = None) -> CaptchaSession:
    """
    Generate a new digit CAPTCHA, persist it, and return the session row.
    Purges expired sessions first to keep the table lean.
    """
    purge_expired_sessions(db)

    png_bytes, text = generate_digit_captcha()
    expires_at = datetime.now(timezone.utc) + timedelta(
        seconds=settings.captcha_ttl_seconds
    )
    captcha_session = CaptchaSession(
        user_id=user_id,
        captcha_type="digit",
        captcha_answer=text,                # plain text — stored server-side only
        expires_at=expires_at,
    )
    db.add(captcha_session)
    db.commit()
    db.refresh(captcha_session)

    # Attach PNG bytes to the in-memory object so the caller can stream them
    # without a second DB hit.  This attribute is NOT persisted.
    captcha_session.__dict__["_png_bytes"] = png_bytes  # type: ignore[assignment]
    return captcha_session


def get_png_for_session(session_id: str, db: Session) -> Optional[bytes]:
    """
    Re-generate (deterministic font, but random each call) — actually we
    must regenerate because we don't store the image, only the text.

    For digit sessions we store the text answer and regenerate the image
    using a seeded approach: we just render the stored text again, which
    produces a visually different image every call (due to random noise)
    but with the same correct answer. This is intentional — it mimics
    real CAPTCHAs that redraw on refresh without changing the code.
    """
    now = datetime.now(timezone.utc)
    captcha_session = db.get(CaptchaSession, session_id)
    if captcha_session is None:
        return None
    if captcha_session.captcha_type != "digit":
        return None
    if captcha_session.expires_at.replace(tzinfo=timezone.utc) < now:
        return None

    pil_image = _captcha_gen.generate_image(captcha_session.captcha_answer)
    buf = io.BytesIO()
    pil_image.save(buf, format="PNG")
    return buf.getvalue()


def verify_digit(session_id: str, answer: str, db: Session) -> dict:
    """
    Validate a submitted digit CAPTCHA answer.

    Returns:
        {
            "success": bool,
            "correct_answer": str  (always returned — useful for solver training)
        }

    The session is deleted after verification (one-time use).
    """
    now = datetime.now(timezone.utc)
    captcha_session = db.get(CaptchaSession, session_id)

    if captcha_session is None:
        return {"success": False, "correct_answer": None, "error": "Session not found."}

    if captcha_session.captcha_type != "digit":
        return {"success": False, "correct_answer": None, "error": "Wrong session type."}

    if captcha_session.expires_at.replace(tzinfo=timezone.utc) < now:
        db.delete(captcha_session)
        db.commit()
        return {"success": False, "correct_answer": None, "error": "Session expired."}

    correct = captcha_session.captcha_answer
    success = answer.strip() == correct

    # Always delete after one attempt (prevents brute-force replay)
    db.delete(captcha_session)
    db.commit()

    return {"success": success, "correct_answer": correct}
