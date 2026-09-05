"""
app/main.py
───────────
FastAPI application entry point.

Registers all routes:
  HTML pages (Jinja2):
    GET  /                → home
    GET  /register        → registration form
    POST /register        → create account
    GET  /login-digit     → digit CAPTCHA login form
    POST /login-digit     → validate credentials + digit CAPTCHA
    GET  /login-grid      → grid CAPTCHA login form
    POST /login-grid      → validate credentials + grid CAPTCHA
    GET  /dashboard       → protected dashboard
    GET  /logout          → clear session cookie

  REST API (JSON):
    GET  /api/captcha-digit          → fetch digit challenge
    GET  /captcha-image/{session_id} → stream digit PNG
    POST /api/verify-digit           → verify digit answer

    GET  /api/captcha-grid                          → fetch grid challenge
    GET  /captcha-image/{session_id}/{tile_index}   → stream grid tile
    POST /api/verify-grid                           → verify grid answer

    GET  /api/health                 → health check
"""

from typing import Optional

from fastapi import Depends, FastAPI, Form, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlmodel import Session

from app.auth import (
    authenticate_user,
    clear_session_cookie,
    register_user,
    set_session_cookie,
)
from app.captcha_digit import create_digit_session, get_png_for_session, verify_digit
from app.captcha_grid import _load_index, create_grid_session, get_tile_path, verify_grid
from app.config import get_settings
from app.db import create_db_and_tables, get_session
from app.dependencies import flash, get_flashed, get_optional_user, require_login

settings = get_settings()

# ── Rate limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit])

# ── App init ──────────────────────────────────────────────────────────────────
app = FastAPI(
    title="CAPTCHA Solver Testbed",
    description=(
        "A self-hosted test arena to train and benchmark AI agents against "
        "real-world CAPTCHA challenges. Two CAPTCHA types: 6-digit numeric and "
        "image-selection (reCAPTCHA v2 style). Full REST API with ground-truth "
        "responses for solver training."
    ),
    version="1.0.0",
)

# ── Middleware ─────────────────────────────────────────────────────────────────

# Attach slowapi rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security headers on every response
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if settings.environment == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Static files + templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ── Startup / Shutdown ────────────────────────────────────────────────────────

@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()
    _load_index()   # load data/index.json into memory for grid CAPTCHA


# ── Template helper ───────────────────────────────────────────────────────────

def _render(request: Request, template: str, db: Session, **ctx):
    """Render a Jinja2 template with common context (current_user, messages)."""
    current_user = get_optional_user(request, db)
    messages = get_flashed(request)
    return templates.TemplateResponse(
        template,
        {"request": request, "current_user": current_user, "messages": messages, **ctx},
    )


# ── Error handlers ────────────────────────────────────────────────────────────

@app.exception_handler(404)
async def not_found(request: Request, exc: HTTPException):
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "status_code": 404, "title": "Page Not Found",
         "detail": "The page you're looking for doesn't exist.", "current_user": None, "messages": []},
        status_code=404,
    )


@app.exception_handler(401)
async def unauthorised(request: Request, exc: HTTPException):
    return RedirectResponse(url="/login-digit", status_code=302)


# ═══════════════════════════════════════════════════════════════════════════════
# HTML ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

# ── Home ──────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_session)):
    return _render(request, "home.html", db)


# ── Register ──────────────────────────────────────────────────────────────────

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request, db: Session = Depends(get_session)):
    return _render(request, "register.html", db)


@app.post("/register", response_class=HTMLResponse)
def register_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_session),
):
    if password != confirm_password:
        flash(request, "Passwords do not match.")
        return _render(request, "register.html", db, form_username=username)

    if len(password) < 8:
        flash(request, "Password must be at least 8 characters.")
        return _render(request, "register.html", db, form_username=username)

    try:
        register_user(username.strip(), password, db)
    except ValueError as e:
        flash(request, str(e))
        return _render(request, "register.html", db, form_username=username)

    flash(request, "Account created! Please log in.", category="success")
    return RedirectResponse(url="/login-digit", status_code=302)


# ── Login — Digit CAPTCHA ─────────────────────────────────────────────────────

@app.get("/login-digit", response_class=HTMLResponse)
def login_digit_page(request: Request, db: Session = Depends(get_session)):
    cs = create_digit_session(db)
    return _render(
        request, "login_digit.html", db,
        session_id=cs.id,
    )


@app.post("/login-digit", response_class=HTMLResponse)
def login_digit_submit(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    session_id: str = Form(...),
    captcha_answer: str = Form(...),
    db: Session = Depends(get_session),
):
    # Verify CAPTCHA first (one-time use — deletes session regardless)
    captcha_result = verify_digit(session_id, captcha_answer, db)

    if not captcha_result["success"]:
        # Create new CAPTCHA for the retry
        cs = create_digit_session(db)
        error = captcha_result.get("error", "Wrong CAPTCHA. Please try again.")
        flash(request, error)
        return _render(request, "login_digit.html", db,
                       session_id=cs.id, form_username=username)

    # CAPTCHA passed — now verify credentials
    user = authenticate_user(username.strip(), password, db)
    if user is None:
        cs = create_digit_session(db)
        flash(request, "Invalid username or password.")
        return _render(request, "login_digit.html", db,
                       session_id=cs.id, form_username=username)

    # Success — set cookie and redirect
    redirect = RedirectResponse(url="/dashboard", status_code=302)
    set_session_cookie(redirect, user.id)
    return redirect


# ── Login — Grid CAPTCHA ──────────────────────────────────────────────────────

@app.get("/login-grid", response_class=HTMLResponse)
def login_grid_page(request: Request, db: Session = Depends(get_session)):
    cs = create_grid_session(db)
    import json
    payload = json.loads(cs.captcha_answer)
    image_urls = [
        f"/captcha-image/{cs.id}/{i}"
        for i in range(len(payload["tiles"]))
    ]
    return _render(
        request, "login_grid.html", db,
        session_id=cs.id,
        instruction=payload["instruction"],
        image_urls=image_urls,
    )


@app.post("/login-grid", response_class=HTMLResponse)
async def login_grid_submit(
    request: Request,
    response: Response,
    db: Session = Depends(get_session),
):
    import json as _json

    form = await request.form()
    username = form.get("username", "").strip()
    password = form.get("password", "")
    session_id = form.get("session_id", "")
    raw_indices = form.getlist("selected_indices")

    try:
        selected = [int(i) for i in raw_indices]
    except ValueError:
        selected = []

    # Verify CAPTCHA
    captcha_result = verify_grid(session_id, selected, db)

    if not captcha_result["success"]:
        cs = create_grid_session(db)
        payload = _json.loads(cs.captcha_answer)
        image_urls = [f"/captcha-image/{cs.id}/{i}" for i in range(len(payload["tiles"]))]
        error = captcha_result.get("error", "Wrong selection. Please try again.")
        flash(request, error)
        return _render(request, "login_grid.html", db,
                       session_id=cs.id, instruction=payload["instruction"],
                       image_urls=image_urls, form_username=username)

    user = authenticate_user(username, password, db)
    if user is None:
        cs = create_grid_session(db)
        payload = _json.loads(cs.captcha_answer)
        image_urls = [f"/captcha-image/{cs.id}/{i}" for i in range(len(payload["tiles"]))]
        flash(request, "Invalid username or password.")
        return _render(request, "login_grid.html", db,
                       session_id=cs.id, instruction=payload["instruction"],
                       image_urls=image_urls, form_username=username)

    redirect = RedirectResponse(url="/dashboard", status_code=302)
    set_session_cookie(redirect, user.id)
    return redirect


# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_session),
              user=Depends(require_login)):
    return _render(request, "dashboard.html", db)


# ── Logout ────────────────────────────────────────────────────────────────────

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=302)
    clear_session_cookie(response)
    return response


# ═══════════════════════════════════════════════════════════════════════════════
# IMAGE STREAMING ROUTES (shared for digit and grid)
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/captcha-image/{session_id}", include_in_schema=False)
def stream_digit_image(session_id: str, db: Session = Depends(get_session)):
    """
    Stream the digit CAPTCHA PNG for the given session.
    The URL contains only the opaque session_id — no answer, no text.
    """
    png = get_png_for_session(session_id, db)
    if png is None:
        raise HTTPException(status_code=404, detail="CAPTCHA session not found or expired.")
    return StreamingResponse(iter([png]), media_type="image/png",
                             headers={"Cache-Control": "no-store"})


@app.get("/captcha-image/{session_id}/{tile_index}", include_in_schema=False)
def stream_grid_tile(session_id: str, tile_index: int,
                     db: Session = Depends(get_session)):
    """
    Stream a grid CAPTCHA tile image.
    URL contains only session_id + numeric index — category is NEVER exposed.
    """
    path = get_tile_path(session_id, tile_index, db)
    if path is None:
        raise HTTPException(status_code=404, detail="Tile not found or session expired.")

    def _iter():
        with open(path, "rb") as f:
            yield from iter(lambda: f.read(65536), b"")

    suffix = path.suffix.lower()
    media_type = "image/jpeg" if suffix in (".jpg", ".jpeg") else "image/png"
    return StreamingResponse(_iter(), media_type=media_type,
                             headers={"Cache-Control": "no-store"})


# ═══════════════════════════════════════════════════════════════════════════════
# REST API — for AI solvers
# ═══════════════════════════════════════════════════════════════════════════════

# ── Pydantic request/response models ──────────────────────────────────────────

class DigitVerifyRequest(BaseModel):
    session_id: str
    answer: str


class GridVerifyRequest(BaseModel):
    session_id: str
    selected_indices: list[int]


# ── Digit CAPTCHA API ─────────────────────────────────────────────────────────

@app.get("/api/captcha-digit", tags=["Digit CAPTCHA"])
@limiter.limit(settings.rate_limit)
def fetch_digit_captcha(request: Request, db: Session = Depends(get_session)):
    """
    Generate a new 6-digit CAPTCHA challenge.

    Returns a session_id and the URL to fetch the CAPTCHA image.
    The image URL does NOT contain the answer.
    """
    cs = create_digit_session(db)
    return {
        "session_id": cs.id,
        "captcha_image_url": f"/captcha-image/{cs.id}",
        "expires_in_seconds": settings.captcha_ttl_seconds,
    }


@app.post("/api/verify-digit", tags=["Digit CAPTCHA"])
@limiter.limit(settings.rate_limit)
def submit_digit_answer(request: Request, body: DigitVerifyRequest, db: Session = Depends(get_session)):
    """
    Submit an answer for a digit CAPTCHA challenge.

    Returns success status and the correct answer (for solver training/analysis).
    The session is invalidated after one attempt.
    """
    result = verify_digit(body.session_id, body.answer, db)
    return result


# ── Grid CAPTCHA API ──────────────────────────────────────────────────────────

@app.get("/api/captcha-grid", tags=["Grid CAPTCHA"])
@limiter.limit(settings.rate_limit)
def fetch_grid_captcha(
    request: Request,
    category: Optional[str] = None,
    db: Session = Depends(get_session),
):
    """
    Generate a new image-selection CAPTCHA challenge.

    - `category` (optional): target category (bus, car, traffic_light, bicycle).
      If omitted, chosen randomly.

    Returns session_id, instruction text, and opaque image URLs.
    **The category name does NOT appear in any image URL.**
    """
    import json as _json

    try:
        cs = create_grid_session(db, target_category=category)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))

    payload = _json.loads(cs.captcha_answer)
    n_tiles = len(payload["tiles"])

    return {
        "session_id": cs.id,
        "instruction": payload["instruction"],
        "image_urls": [f"/captcha-image/{cs.id}/{i}" for i in range(n_tiles)],
        "grid_size": n_tiles,
        "expires_in_seconds": settings.captcha_ttl_seconds,
    }


@app.post("/api/verify-grid", tags=["Grid CAPTCHA"])
@limiter.limit(settings.rate_limit)
def submit_grid_answer(request: Request, body: GridVerifyRequest, db: Session = Depends(get_session)):
    """
    Submit selected tile indices for a grid CAPTCHA challenge.

    Returns success status and the correct indices (for solver training/analysis).
    The session is invalidated after one attempt.
    """
    return verify_grid(body.session_id, body.selected_indices, db)


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/api/health", tags=["Meta"])
def health():
    """Service liveness check."""
    return {"status": "ok", "version": app.version}
