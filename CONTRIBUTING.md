# Contributing to TEST ARENA

Thank you for your interest in contributing to the **AI CAPTCHA Solver Testbed** (`TEST ARENA`)!

This project is an open-source research platform designed to train and benchmark autonomous AI agents against real-world CAPTCHAs under ethical, self-hosted conditions.

---

## 🛠️ Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/Sudhith/TEST-Arena_site.git
   cd TEST-Arena_site
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```

3. **Install pinned dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the development server:**
   ```bash
   uvicorn app.main:app --reload
   ```

---

## 🌿 Git Branching & Commit Conventions

We follow a structured Gitflow branch strategy:
- `main` — Production release branch (tagged releases only).
- `develop` — Active integration branch.
- `feature/<name>` — Feature development branches branched from and merged into `develop`.
- `fix/<name>` — Bugfix branches.

### Commit Message Format
Use semantic commit prefixes:
- `feat(...)` — New features or endpoints.
- `fix(...)` — Bug fixes.
- `docs(...)` — Documentation updates.
- `chore(...)` — Housekeeping, dependency bumps.

---

## 🧪 Running Automated Tests

Always run the full test suite before submitting a pull request:

```bash
python -c "
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)
assert client.get('/api/health').status_code == 200
print('Health check passed!')
"
```

---

## 🎨 UI Style Guidelines

- **Strict Zero-Blue Palette**: All interface components must follow the Cyber-Obsidian & Electric Emerald palette (`#10b981`, `#00f59b`, `#f59e0b`, `#12141c`). Blue or indigo colors are strictly prohibited.
- **Typography**: Headings use `Space Grotesk`, UI body uses `Plus Jakarta Sans`, code and CAPTCHA numbers use `JetBrains Mono`.
- **Responsive**: All views must be test-verified on desktop (1920px, 1440px) and mobile (375px).

---

## 📄 License
By contributing, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).
