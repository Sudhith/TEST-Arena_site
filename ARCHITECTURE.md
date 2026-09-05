# Architecture & System Design — TEST ARENA

This document details the technical architecture, security model, and data flow of the **AI CAPTCHA Solver Testbed** (`TEST ARENA`).

---

## 1. System Overview

```text
                                [ AI Agent / Browser ]
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
         [ Web Frontend ]                                 [ REST API ]
     • /login-digit (OCR track)                      • GET  /api/captcha-digit
     • /login-grid  (Vision track)                   • POST /api/verify-digit
     • /register                                     • GET  /api/captcha-grid
     • /dashboard (protected)                        • POST /api/verify-grid
                  │                                  • GET  /api/health
                  └───────────────────────┬───────────────────────┘
                                          ▼
                         [ FastAPI Application Core ]
                                          │
            ┌─────────────────────────────┼─────────────────────────────┐
            ▼                             ▼                             ▼
    [ Auth Module ]               [ Digit Engine ]              [ Grid Engine ]
  • bcrypt hashing              • ImageCaptcha lib            • 3x3 category grid
  • itsdangerous tokens         • Distortion + noise lines    • Opaque tile routing
  • Session TTL guard           • In-memory stream            • In-memory index cache
            │                             │                             │
            └─────────────────────────────┼─────────────────────────────┘
                                          ▼
                                [ Database Layer ]
                         SQLModel ORM (SQLite / Postgres)
                         • User table
                         • CaptchaSession table
```

---

## 2. Core Security Decisions

### 2.1 Zero-Leakage Opaque Tile Routing
In real-world reCAPTCHA challenges, the client receives challenge images without knowing their categories or true annotations. 

**Vulnerability Prevented:**  
If images were served via direct paths like `/static/images/bus/001.jpg`, any solver script could simply parse the URL string to extract the answer without processing computer vision.

**Our Implementation:**  
- Grid challenges are served strictly via opaque routes: `/captcha-image/{session_id}/{tile_index}`.
- The server maps the numeric index to the underlying disk file in memory using the stored session row.
- The category name **never appears in any client-accessible URL, headers, or response bodies**.

### 2.2 Replay Protection & One-Time Tokens
Every CAPTCHA challenge is assigned a UUIDv4 session identifier. When a submission is verified (via `POST /api/verify-digit` or `POST /api/verify-grid`), the session record is **immediately deleted from the database regardless of whether the answer was correct or incorrect**. This guarantees that a challenge can never be re-submitted or brute-forced.

### 2.3 Lazy TTL Session Eviction
Live challenges have a strict 10-minute time-to-live (`captcha_ttl_seconds = 600`). Whenever a new session is created, `purge_expired_sessions()` automatically runs a query to evict any stale session records, keeping memory and database table sizes bounded with zero external background worker requirements.

### 2.4 Rate Limiting Shield
The API endpoints and image streaming routes are protected with `slowapi` (backed by the `limits` library) enforcing a default of **30 requests/minute per IP address**. Requests exceeding this threshold receive HTTP `429 Too Many Requests`.

---

## 3. Dataset Architecture

1. **Starter Dataset (Bundled)**:  
   40 curated images (10 per category: `bus`, `car`, `traffic_light`, `bicycle`) committed directly to the repository and baked into Docker images. Ensures the arena functions out-of-the-box on fresh deployments.

2. **Large-Scale Training Datasets (`scripts/download_dataset.py`)**:  
   - **Digit OCR Dataset**: `project-sloth/captcha-images` on Hugging Face (10,000+ images with train/val/test splits). Used for offline agent training.
   - **Grid Vision Dataset**: `Corianas/recaptcha-v2` on Hugging Face (~29,000 real reCAPTCHA v2 tiles). Used to scale the grid challenge variety.

---

## 4. Deployment Model

- **Local Development**: SQLite file database, Uvicorn ASGI server with live reload.
- **Docker Compose**: Production container with multi-worker Uvicorn and healthcheck.
- **Cloud (Render / Fly.io / Railway)**: Ephemeral filesystem supported by baking `data/images/` into the Docker build; optional `DATABASE_URL` for durable accounts on Neon/Supabase PostgreSQL.
