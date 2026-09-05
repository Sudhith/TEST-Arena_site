# PRD — AI CAPTCHA Solver Testbed

## 1. Overview

**Product name (working title):** CAPTCHA Solver Testbed  
**Goal:** Build a free, self‑hosted website that mimics real‑world CAPTCHAs (6‑digit numeric image CAPTCHA + “select bus/car/traffic light” image‑selection CAPTCHA) to train and evaluate AI agents that solve CAPTCHAs.  
**Constraints:** Zero monetary cost (₹0). Use only free tools, datasets, and hosting tiers.  
**Primary users:** You (developer/researcher) and potentially collaborators testing CAPTCHA‑solving models.

---

## 2. Objectives & Success Metrics

### 2.1 Objectives

1. Provide a realistic but ethical environment to:
   - Generate CAPTCHAs similar to a university login (6‑digit numeric).
   - Generate image‑selection CAPTCHAs (e.g., “Select all images with buses”).
2. Enable easy integration with AI solvers:
   - Expose endpoints to fetch CAPTCHA challenges.
   - Allow automated submission of answers for evaluation.
3. Keep everything free:
   - Free hosting.
   - Free datasets.
   - Free/open‑source libraries.

### 2.2 Success metrics

- **Functional:**
  - Site is live and accessible via a public URL.
  - Both CAPTCHA types work end‑to‑end (generation → display → validation).
  - User registration/login works with CAPTCHA protection.
- **ML/Research:**
  - Can generate ≥10k 6‑digit CAPTCHA images for training.
  - Can generate ≥1k image‑selection challenges for evaluation.
  - Solver accuracy can be measured automatically (API returns success/failure).
- **Cost:**
  - Monthly cost = ₹0 (free tiers only).

---

## 3. User Flows

### 3.1 End‑user (human) flow

1. **Home page**
   - User visits `/`.
   - Sees links: “Login (Digit CAPTCHA)”, “Login (Image‑Selection CAPTCHA)”, “Register”.

2. **Registration**
   - User clicks “Register”.
   - Enters: username, password, confirm password.
   - Submits → account created.
   - Redirected to login page.

3. **Login with 6‑digit CAPTCHA**
   - User goes to `/login-digit`.
   - Sees:
     - Username, password fields.
     - CAPTCHA image (6 random digits) + input box.
   - Submits form.
   - Backend validates:
     - Credentials.
     - CAPTCHA answer.
   - On success → logged in, shown dashboard / welcome page.
   - On failure → error message, new CAPTCHA shown.

4. **Login with image‑selection CAPTCHA**
   - User goes to `/login-grid`.
   - Sees:
     - Username, password fields.
     - Instruction: “Select all images with buses” (or car/traffic light, etc.).
     - Grid of 9–12 images.
   - User selects images and submits.
   - Backend validates:
     - Credentials.
     - Selected indices vs correct set.
   - On success → logged in.
   - On failure → error, new challenge shown.

### 3.2 AI agent / solver flow

1. **Fetch challenge**
   - Agent calls:
     - `GET /api/captcha-digit` → receives:
       - `session_id`
       - `captcha_image_url`
     - or `GET /api/captcha-grid` → receives:
       - `session_id`
       - `instruction` (e.g., “bus”)
       - `image_urls: [...]`
2. **Solve**
   - Agent runs its model:
     - For digit CAPTCHA: OCR / sequence model → predicted 6‑digit string.
     - For grid CAPTCHA: object detector / classifier → selected indices.
3. **Submit answer**
   - Agent calls:
     - `POST /api/verify-digit` with `{ session_id, answer: "123456" }`
     - or `POST /api/verify-grid` with `{ session_id, selected_indices: [0, 3, 5] }`
   - Response:
     - `success: true/false`
     - Optional: `correct_answer` / `correct_indices` for analysis.

This flow allows automated benchmarking of solver accuracy and latency.

---

## 4. Functional Requirements

### 4.1 Core features

1. **User management**
   - Register, login, logout.
   - Password hashing (e.g., bcrypt).
   - Session management or JWT.

2. **6‑digit numeric CAPTCHA**
   - Generate random 6‑digit string.
   - Render as distorted image (noise, lines, warping).
   - Store correct answer tied to session.
   - Validate user input against stored answer.
   - Regenerate on each login attempt.

3. **Image‑selection CAPTCHA**
   - Maintain a local dataset of images tagged with categories:
     - bus, car, bicycle, traffic light, etc.
   - On each challenge:
     - Randomly choose target category.
     - Select N positive images (contain target) and M negative images.
     - Shuffle and send to frontend.
     - Store correct indices in session.
   - Validate selected indices vs stored correct set.

4. **APIs for AI solvers**
   - Endpoints to:
     - Fetch CAPTCHA challenges.
     - Submit answers.
     - Get success/failure + optional ground truth.

5. **Basic UI**
   - Simple, responsive pages:
     - Home, Register, Login (digit), Login (grid), Dashboard.
   - Clear error messages for wrong CAPTCHA / credentials.

### 4.2 Non‑functional requirements

- **Cost:** ₹0 monthly (free tiers only).
- **Performance:**
  - CAPTCHA generation < 500 ms per request (on free tier).
  - Page load < 2 s on typical broadband.
- **Security (basic):**
  - Passwords hashed.
  - HTTPS via hosting provider.
  - Rate limiting on CAPTCHA endpoints (to avoid abuse).
- **Maintainability:**
  - Clean separation: routes, CAPTCHA logic, auth, templates.
  - Config via environment variables.

---

## 5. Suggested Tech Stack

### 5.1 Backend

**Primary recommendation:**  
- **Language:** Python 3.11+  
- **Framework:** FastAPI or Flask  
  - FastAPI benefits:
    - Async support, automatic OpenAPI docs.
    - Good for future ML APIs.
  - Flask benefits:
    - Simpler, huge tutorial base.
- **CAPTCHA generation:**
  - 6‑digit: `captcha` (PyPI package `pip install captcha`, by lepture — `ImageCaptcha` class) or custom Pillow generator. [3]
    - Verified free, open‑source (BSD‑3‑Clause), mature, actively used, generates exactly this style: distorted/rotated digits + dot noise + curved noise lines, matching a typical "university login" numeric CAPTCHA.
    - Runs 100% locally — no API key, no rate limit, no external service. Generating 10k+ images costs nothing but local compute time.
    - `light-captcha` (previously listed here) is a real PyPI package but is very new (first release 2026), single‑maintainer, and its actual API (`CaptchaGenerator().generate("english")`) doesn't match a naive usage guess — not recommended as the primary pick.
  - Image‑selection: custom logic using COCO dataset images. [16][24][29]
- **Auth:**
  - `passlib` + `bcrypt` for password hashing.
  - Session cookies (Flask‑Login) or JWT (FastAPI + `python-jose`).

**Trade‑offs:**

- **FastAPI vs Flask**
  - FastAPI:
    - Pros: Modern, async, auto docs, great for ML APIs.
    - Cons: Slightly steeper learning curve if you’re new.
  - Flask:
    - Pros: Very simple, many tutorials, easy to start.
    - Cons: More manual setup for async and docs.

For maximum efficiency + future ML integration, **FastAPI** is recommended if you’re comfortable; otherwise **Flask** is perfectly fine.

### 5.2 Frontend

- **Stack:** Plain HTML + CSS + minimal JS.
- **Why not React/Vue?**
  - Pros of frameworks:
    - Better state management, component reuse.
  - Cons:
    - More complexity, build steps, dependencies.
- Since the UI is simple (forms + grids), **vanilla JS** is enough and keeps cost/complexity low.

### 5.3 Database

- **Option A (simplest):** SQLite
  - File‑based, no separate DB service.
  - Perfect for small user base and test project.
  - Zero cost, zero setup.
- **Option B:** Managed Postgres (Render/Railway free tiers)
  - Pros: More scalable, standard SQL.
  - Cons: Slightly more setup; free tiers have limits.

For ₹0 and simplicity, start with **SQLite**. Migrate later if needed.

### 5.4 Hosting

**Recommended options (all have free tiers):**

1. **Render**
   - Free web service (spins down after 15 min idle). [22][25][27][28]
   - Easy Git‑based deploys.
   - Good for Flask/FastAPI.
   - Trade‑off: Cold starts (~30–60s) after inactivity.

2. **Railway**
   - $5/month credit (effectively free for small apps). [22][25][28]
   - No forced sleep; always‑on within credit.
   - Simple deploy from GitHub.
   - Trade‑off: Slight learning curve; credit can run out if you scale.

3. **Fly.io**
   - 3 free shared VMs. [22][25][26]
   - Good performance, global regions.
   - Trade‑off: More config (Dockerfly), but powerful.

**Recommendation for maximum efficiency + least cost:**

- Start with **Render free tier**:
  - Simplest setup.
  - ₹0 as long as you’re okay with spin‑down.
- If cold starts annoy you, move to **Railway** or **Fly.io** later.

All provide HTTPS automatically.

### 5.5 Datasets

- **COCO (Common Objects in Context)**
  - Contains: bus, car, bicycle, traffic light, etc. [16][17][24][29]
  - Large‑scale, free for research.
  - Use a subset (e.g., 2–5k images) to keep storage low.
- **Alternative:** Roboflow Universe datasets (COCO‑style, vehicle‑focused). [20][21][23]

You don’t need the full COCO; just images with relevant categories.

### 5.6 CAPTCHA generation libraries

- **6‑digit numeric CAPTCHA:**
  - `captcha` (Python, `pip install captcha`, `from captcha.image import ImageCaptcha`):
    - Generates CAPTCHA images (any length string) with built‑in dot noise + curved noise lines.
    - Customizable size, font (`fonts=[...]` — e.g. `DejaVuSans-Bold.ttf`, free/open and preinstalled on most Linux base images), colors (`bg_color`, `fg_color`). [3]
  - Or write a small generator with Pillow:
    - Draw random digits, add noise, lines, warps.
    - Gives full control over difficulty tuning (useful since a too‑easy CAPTCHA has less value as a solver benchmark — see Section 10).
- **Image‑selection CAPTCHA:**
  - No ready‑made “reCAPTCHA clone” library needed.
  - Implement custom logic:
    - Choose category.
    - Query local image index.
    - Build grid.

This keeps cost zero and gives full control for solver experiments. [1][13]

---

## 6. Architecture Overview

```text
[Browser / AI Agent]
        |
        v
[FastAPI/Flask App]  <-->  [SQLite (users, sessions)]
        |
        +--> [CAPTCHA Generator (6-digit)]
        |       - light-captcha / Pillow
        |
        +--> [Image-Selection CAPTCHA Logic]
        |       - Local COCO subset
        |       - Category -> images mapping
        |
        +--> [Auth Module]
                - Register/Login
                - Session/JWT
```

- Static assets (CSS, JS, images) served by the same app or via hosting’s static file support.
- All logic runs on a single free‑tier service.

---

## 7. Detailed Implementation Plan

### 7.1 Project structure

Example (FastAPI):

```text
captcha-testbed/
  app/
    __init__.py
    main.py            # FastAPI app, routes
    auth.py            # registration, login, password hashing
    captcha_digit.py   # 6-digit CAPTCHA generation & verification
    captcha_grid.py    # image-selection CAPTCHA logic
    db.py              # SQLite setup, user/session tables
    config.py          # env vars
  data/
    coco_subset/       # images (bus, car, traffic light, bicycle, etc.)
    coco_index.json    # mapping: image_path -> categories
  templates/
    base.html
    home.html
    register.html
    login_digit.html
    login_grid.html
    dashboard.html
  static/
    css/
      style.css
    js/
      main.js
  requirements.txt
  README.md
  PRD.md
```

For Flask, similar structure with `templates/` and `static/`.

### 7.2 Step‑by‑step build guide

#### Step 1: Set up repo and environment

1. Create GitHub repo: `captcha-solver-testbed`.
2. Clone locally.
3. Create virtualenv:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   ```
4. Install dependencies:
   ```bash
   pip install fastapi uvicorn[standard] python-multipart \
               passlib[bcrypt] aiofiles \
               captcha pillow \
               jinja2
   ```
   (Adjust for Flask if chosen.)

5. Create `requirements.txt`:
   ```txt
   fastapi
   uvicorn[standard]
   python-multipart
   passlib[bcrypt]
   aiofiles
   captcha
   pillow
   jinja2
   ```

#### Step 2: Prepare image dataset (COCO subset)

1. Download COCO train/val images (or use a pre‑filtered subset):
   - Focus on categories: bus, car, bicycle, traffic light, motorcycle, etc. [16][24]
2. Optionally, use a tool/script to:
   - Filter images containing at least one of these categories.
   - Save a smaller subset (e.g., 2–5k images) to `data/coco_subset/`.
3. Create `data/coco_index.json`:
   - Format example:
     ```json
     [
       {
         "path": "coco_subset/000000123.jpg",
         "categories": ["bus", "car"]
       },
       ...
     ]
     ```
   - You can generate this from COCO annotations.

This index allows quick selection of positive/negative images per category.

#### Step 3: Implement database & auth

Using SQLite + `sqlite3` or `SQLModel`/`SQLAlchemy`:

- Tables:
  - `users`: id, username (unique), password_hash
  - `sessions`: id, user_id, captcha_type, captcha_answer (JSON), created_at

Basic flows:

- **Register:**
  - Hash password with bcrypt.
  - Insert into `users`.
- **Login:**
  - Verify password.
  - Create session record with CAPTCHA data.
  - Set session cookie or JWT.

Keep it minimal; no email verification needed for a testbed.

#### Step 4: Implement 6‑digit CAPTCHA module

Using `captcha` (verified working, tested against v0.7.1): [3]

```python
# app/captcha_digit.py
from captcha.image import ImageCaptcha
import io, secrets

_image = ImageCaptcha(
    width=280, height=90,
    fonts=["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],  # bold, free, on most Linux images
    font_sizes=(48, 54, 60),
)

def generate_digit_captcha() -> tuple[bytes, str]:
    text = "".join(secrets.choice("0123456789") for _ in range(6))
    image = _image.generate_image(text)  # PIL Image, built-in dot + curve noise
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue(), text
```

This runs entirely locally — no external service, no API key, no per-request cost — so hitting the ≥10k-image success metric (Section 2.2) is just a loop calling this function and saving each PNG.

Store `text` in session as `captcha_answer`.

Endpoints:

- `GET /api/captcha-digit`:
  - Create session or update existing.
  - Return `{ session_id, captcha_image_url }`.
- `POST /api/verify-digit`:
  - Check `answer` vs stored `captcha_answer`.
  - Return `{ success: bool }`.

#### Step 5: Implement image‑selection CAPTCHA module

Core logic in `app/captcha_grid.py`:

- Load `coco_index.json` into memory at startup.
- Function:

```python
import random

def generate_grid_captcha(target_category: str, grid_size: int = 9):
    # positives: images containing target_category
    # negatives: images without target_category
    positives = [item for item in coco_index if target_category in item["categories"]]
    negatives = [item for item in coco_index if target_category not in item["categories"]]

    n_pos = random.randint(2, 4)  # at least 2, at most 4 correct images
    n_neg = grid_size - n_pos

    selected_pos = random.sample(positives, n_pos)
    selected_neg = random.sample(negatives, n_neg)

    images = selected_pos + selected_neg
    random.shuffle(images)

    correct_indices = [i for i, item in enumerate(images) if target_category in item["categories"]]

    return {
        "instruction": f"Select all images with {target_category}",
        "image_paths": [item["path"] for item in images],
        "correct_indices": correct_indices,
    }
```

Endpoints:

- `GET /api/captcha-grid?category=bus`:
  - Create session, store `correct_indices`.
  - Return `{ session_id, instruction, image_urls }`.
- `POST /api/verify-grid`:
  - Compare `selected_indices` with stored `correct_indices`.
  - Return `{ success: bool }`.

You can randomize `category` on the server instead of taking it from query.

#### Step 6: Implement routes & templates

**Routes (FastAPI example):**

- `GET /` → home template.
- `GET /register`, `POST /register` → registration.
- `GET /login-digit`, `POST /login-digit` → digit CAPTCHA login.
- `GET /login-grid`, `POST /login-grid` → grid CAPTCHA login.
- `GET /dashboard` → protected page after login.
- API routes under `/api/*` for solvers.

**Templates:**

- Use Jinja2 (built into FastAPI/Flask).
- Keep design minimal:
  - Centered forms.
  - CAPTCHA image displayed with `<img>`.
  - Grid CAPTCHA: render images in a responsive grid; use checkboxes or clickable tiles.

#### Step 7: Add basic security & rate limiting

- Use HTTPS (provided by host).
- Hash passwords with bcrypt.
- Add simple rate limiting:
  - Limit CAPTCHA fetch/verify endpoints per IP (e.g., 20 requests/min).
  - Can use a small in‑memory dict or `slowapi` for FastAPI.

This prevents others from abusing your free tier.

#### Step 8: Deploy to free hosting (Render example)

1. Create a `Dockerfile` (optional but robust):

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

2. Push to GitHub.
3. On Render:
   - Create new “Web Service”.
   - Connect repo.
   - Set:
     - Runtime: Docker.
     - Environment: production.
   - Deploy.
4. Get your URL (e.g., `https://captcha-testbed.onrender.com`).

Test all flows manually, then with your solver.

---

## 8. Efficiency & Cost Optimization

### 8.1 Maximizing efficiency

- **Code simplicity:**
  - Avoid heavy frameworks on frontend.
  - Keep backend modular but small.
- **Dataset size:**
  - Use a curated subset of COCO (2–5k images) to:
    - Reduce storage.
    - Speed up image selection.
- **Caching:**
  - Load `coco_index.json` once at startup.
  - Optionally cache image lists per category.

### 8.2 Minimizing cost

- Use only free tiers:
  - Hosting: Render/Railway/Fly.io. [22][25][27]
  - DB: SQLite (file on disk).
  - Datasets: COCO (free). [24][29]
  - Libraries: open‑source (light-captcha, Pillow, FastAPI/Flask). [3]
- Avoid:
  - Paid CAPTCHA services.
  - Managed DBs unless necessary.
  - Heavy frontend builds/CDNs.

This keeps monthly cost at ₹0.

---

## 9. Risks & Mitigations

- **Risk:** Free tier limits (CPU, memory, bandwidth).
  - **Mitigation:** Keep traffic low; optimize images; use small dataset.
- **Risk:** Cold starts (Render free tier).
  - **Mitigation:** Accept delay or switch to Railway/Fly.io later. [25][28]
- **Risk:** Dataset storage grows.
  - **Mitigation:** Limit to essential categories; compress images; prune unused files.

---

## 10. Future Enhancements (Optional)

- Add more CAPTCHA types:
  - Distorted text with letters + digits.
  - Rotation‑based CAPTCHAs.
- Integrate with existing solver frameworks (e.g., CNN/LSTM solvers). [7][8][10]
- Add analytics:
  - Track solver success rate, latency.
- Containerize fully with Docker Compose for easy replication.

---

## 11. References & Resources

- `captcha` (image + audio CAPTCHA generator, Python — `pip install captcha`, GitHub: lepture/captcha). [3]
- OpenCaptcha (open‑source CAPTCHA generator & API). [11]
- COCO dataset (bus, car, traffic light, etc.). [16][24][29]
- Hosting comparisons (Render, Railway, Fly.io). [22][25][27][28]
- Existing CAPTCHA solver projects (for inspiration, not copying). [7][8][10]

---

## 12. How to Use This PRD

1. Create `PRD.md` in your repo with this content.
2. Use it as the blueprint while implementing:
   - Follow “Detailed Implementation Plan” section step‑by‑step.
3. Adjust stack choices (Flask vs FastAPI, Render vs Railway) based on your comfort.
4. Once the base is working, iterate:
   - Improve CAPTCHA visuals.
   - Expand dataset.
   - Plug in your AI solver.

This document defines the full flow, stack, trade‑offs, and build plan for a zero‑cost CAPTCHA solver testbed.