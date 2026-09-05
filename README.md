# TEST ARENA &mdash; Autonomous AI CAPTCHA Solver Testbed

<div align="center">

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-10b981.svg?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-059669.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-10b981.svg?style=for-the-badge&logo=docker&logoColor=white)](Dockerfile)
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Sudhith/TEST-Arena_site)
[![License: MIT](https://img.shields.io/badge/License-MIT-f59e0b.svg?style=for-the-badge)](LICENSE)
[![Cost](https://img.shields.io/badge/Cost-₹0%20Zero%20Tier-10b981.svg?style=for-the-badge)](#zero-cost-architecture)

**A high-performance, self-hosted test arena to train, evaluate, and benchmark autonomous AI agents against real-world CAPTCHAs.**

[Live Workbench](#interactive-workbench) &bull; [Quick Start](#quick-start) &bull; [API Reference](#api-integration) &bull; [Architecture](ARCHITECTURE.md) &bull; [Contributing](CONTRIBUTING.md)

</div>

---

## ⚡ Overview

The **AI CAPTCHA Solver Testbed** (`TEST ARENA`) is an open-source, ethical research platform providing pixel-accurate replicas of the two most prevalent CAPTCHA styles on the modern web:

| Challenge Type | Target Real-World System | Benchmark Objective | API Route |
|---|---|---|---|
| **6-Digit Distortion** | University & Banking Logins | Character OCR, CRNNs, Sequence Models | `GET /api/captcha-digit` |
| **3&times;3 Image Grid** | Google reCAPTCHA v2 ("Select all buses") | Multi-label Vision, CLIP, Object Detection | `GET /api/captcha-grid` |

### Key Engineering Features
- 🛡️ **Zero-Leak Opaque Routing**: Tile URLs (`/captcha-image/{session_id}/{index}`) never reveal category names, forcing agents to use vision.
- 🔁 **Instant Training Signals**: Every verification call returns `success: true/false` **plus ground-truth labels** for immediate reinforcement learning.
- ⚡ **Sub-15ms Challenge Generation**: Pure Python local rendering with zero external API dependencies or latency bottlenecks.
- 🔒 **One-Time Token Security**: Session records self-destruct after verification to prevent replay attacks.
- 💸 **100% Free Hosting Tier**: Zero monetary cost (₹0). Deployable to Render, Fly.io, or any VPS with 1 command.

---

## 🚀 Quick Start

### Option A: Local Development

```bash
# 1. Clone the repository
git clone https://github.com/Sudhith/TEST-Arena_site.git
cd TEST-Arena_site

# 2. Setup virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the live testbed
uvicorn app.main:app --reload
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.  
Interactive OpenAPI documentation is live at **[http://localhost:8000/docs](http://localhost:8000/docs)**.

---

### Option B: Docker Compose (1 Command)

```bash
docker compose up --build -d
```
The testbed will start automatically with health checks enabled at `http://localhost:8000`.

---

### Option C: 1-Click Render Cloud Deploy

This repository includes a native [`render.yaml`](render.yaml) Blueprint:
1. Fork or push this repository to your GitHub account.
2. Log in to [Render](https://render.com) &rarr; **Blueprints** &rarr; **New Blueprint Instance**.
3. Connect this repository &rarr; Click **Apply**.
4. Render will automatically build the container and deploy your live public instance with free HTTPS.

---

## 🤖 API Integration for AI Solvers

### 1. 6-Digit Distortion CAPTCHA Pipeline

```python
import requests

BASE = "http://localhost:8000"

# Step 1: Fetch challenge
challenge = requests.get(f"{BASE}/api/captcha-digit").json()
session_id = challenge["session_id"]
image_bytes = requests.get(f"{BASE}{challenge['captcha_image_url']}").content

# Step 2: Feed image_bytes into your model (CRNN / TrOCR / Vision Model)
predicted_digits = "580608"

# Step 3: Verify and receive ground-truth feedback
result = requests.post(f"{BASE}/api/verify-digit", json={
    "session_id": session_id,
    "answer": predicted_digits
}).json()

print("Solved:", result["success"])
print("Ground truth:", result["correct_answer"])
```

### 2. 3&times;3 Image Selection Grid Pipeline

```python
import requests

BASE = "http://localhost:8000"

# Step 1: Fetch challenge
challenge = requests.get(f"{BASE}/api/captcha-grid").json()
session_id = challenge["session_id"]
instruction = challenge["instruction"]  # e.g., "Select all images with a bus"
tile_urls = challenge["image_urls"]     # 9 opaque URLs

# Step 2: Classify each tile with your model
selected_indices = [0, 3, 7]

# Step 3: Submit and receive evaluation metrics
result = requests.post(f"{BASE}/api/verify-grid", json={
    "session_id": session_id,
    "selected_indices": selected_indices
}).json()

print("Solved:", result["success"])
print("Correct tile indices:", result["correct_indices"])
```

---

## 📦 Large-Scale Training Datasets

The repository comes pre-loaded with **40 starter tiles** so it works immediately. To download massive pre-labelled datasets for training your models offline:

```bash
python scripts/download_dataset.py
```

| Dataset | Source | Images | License | Purpose |
|---|---|---|---|---|
| `project-sloth/captcha-images` | Hugging Face | 10,000+ | MIT | 6-digit numeric OCR training splits |
| `Corianas/recaptcha-v2` | Hugging Face | ~29,000 | CC BY 4.0 | Real reCAPTCHA v2 visual tile corpus |

---

## 🛡️ Architecture & Security

For an in-depth explanation of session lifecycle, URL opacity, and rate limiting mechanics, please read the **[System Architecture Document](ARCHITECTURE.md)**.

---

## 📄 License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for more details.
