"""
scripts/download_dataset.py
────────────────────────────
Downloads two public research datasets using the HuggingFace `datasets` library.
No API key required for either — both are publicly accessible.

Dataset 1 — 6-digit numeric CAPTCHA images (for AGENT TRAINING)
  Source : project-sloth/captcha-images (HuggingFace)
  License: MIT
  Output : data/digit_samples/{train,validation,test}/<label>.png
  Purpose: Offline training corpus for your CAPTCHA-solving agent.
           The live site generates its own CAPTCHAs via ImageCaptcha;
           this dataset gives the agent a large pre-labelled set to
           train on before hitting the live API.

Dataset 2 — reCAPTCHA v2 grid tiles (for GRID CAPTCHA images)
  Source : huggingface.co/datasets/Corianas/recaptcha-v2  (29k images,
           classes: bicycle, bus, car, crosswalk, hydrant, motorcycle,
           palm, traffic_light, stair, bridge, chimney)
  License: CC BY 4.0
  Output : data/images/{bus,car,traffic_light,bicycle}/img_<n>.jpg
  Purpose: Replaces the Wikimedia Commons download. These are real
           reCAPTCHA tiles — same size, same visual style — so the
           grid CAPTCHA challenges on this site are pixel-accurate
           replicas of Google reCAPTCHA v2.

Usage
─────
  pip install datasets pillow
  python scripts/download_dataset.py

Options (env vars):
  DIGIT_LIMIT   Max digit images to download (default: 10000)
  GRID_LIMIT    Max grid images per category  (default: 500)
  HF_DATASETS_CACHE  Standard HuggingFace cache dir override
"""

import json
import os
import sys
from pathlib import Path

# Force utf-8 encoding on standard output for Windows cp1252 consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── Paths (project root is one level above scripts/) ─────────────────────────
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DIGIT_DIR = DATA_DIR / "digit_samples"
IMAGES_DIR = DATA_DIR / "images"
INDEX_PATH = DATA_DIR / "index.json"

DIGIT_LIMIT = int(os.environ.get("DIGIT_LIMIT", 10_000))
GRID_LIMIT  = int(os.environ.get("GRID_LIMIT", 500))

# Grid CAPTCHA categories we care about (must match config.py grid_categories)
GRID_CATEGORIES = ["bus", "car", "traffic_light", "bicycle"]

# Mapping from dataset label -> our folder name
LABEL_MAP = {
    "bus":           "bus",
    "car":           "car",
    "traffic light": "traffic_light",
    "traffic_light": "traffic_light",
    "bicycle":       "bicycle",
    "bike":          "bicycle",
}


def banner(msg: str) -> None:
    print(f"\n{'-'*60}\n  {msg}\n{'-'*60}")


# ═════════════════════════════════════════════════════════════════════════════
# Dataset 1 — 6-digit numeric CAPTCHA (project-sloth/captcha-images)
# ═════════════════════════════════════════════════════════════════════════════

def download_digit_dataset() -> None:
    banner("Downloading 6-digit CAPTCHA dataset (project-sloth/captcha-images)")
    try:
        from datasets import load_dataset
    except ImportError:
        print("ERROR: Install the 'datasets' package:  pip install datasets")
        sys.exit(1)

    try:
        ds = load_dataset("project-sloth/captcha-images", trust_remote_code=False)
    except Exception as exc:
        print(f"ERROR loading digit dataset: {exc}")
        print("Tip: check your internet connection or try: pip install -U datasets")
        return

    total_saved = 0
    for split_name in ("train", "validation", "test"):
        split = ds.get(split_name)
        if split is None:
            continue

        out_dir = DIGIT_DIR / split_name
        out_dir.mkdir(parents=True, exist_ok=True)

        limit = DIGIT_LIMIT if split_name == "train" else min(DIGIT_LIMIT // 5, 2000)
        count = 0

        for item in split:
            if count >= limit:
                break
            label: str = item["solution"]        # e.g. "384729"
            image = item["image"]                # PIL Image
            fname = f"{label}_{count:06d}.png"
            image.save(out_dir / fname)
            count += 1

        total_saved += count
        print(f"  [{split_name}] saved {count} images → {out_dir.relative_to(ROOT)}")

    print(f"\n[OK] Digit dataset done. Total: {total_saved} images")
    print("   Label is encoded in the filename, e.g. '384729_000001.png'")
    print("   Use data/digit_samples/ to train your OCR/CRNN solver agent.\n")


# ═════════════════════════════════════════════════════════════════════════════
# Dataset 2 — reCAPTCHA v2 grid tiles (Corianas/recaptcha-v2)
# ═════════════════════════════════════════════════════════════════════════════

def download_grid_dataset() -> None:
    banner("Downloading reCAPTCHA v2 grid tiles (Corianas/recaptcha-v2)")
    try:
        from datasets import load_dataset
    except ImportError:
        print("ERROR: Install the 'datasets' package:  pip install datasets")
        sys.exit(1)

    try:
        ds = load_dataset("Corianas/recaptcha-v2", trust_remote_code=False)
    except Exception as exc:
        print(f"  WARNING: Primary grid dataset failed ({exc})")
        print("  Falling back to manual category scan of data/images/ ...")
        _ensure_fallback_images()
        return

    # Create output dirs
    for cat in GRID_CATEGORIES:
        (IMAGES_DIR / cat).mkdir(parents=True, exist_ok=True)

    counts: dict[str, int] = {cat: 0 for cat in GRID_CATEGORIES}
    skipped = 0

    split = ds.get("train") or ds.get("test") or next(iter(ds.values()))

    for item in split:
        raw_label: str = str(item.get("label", "")).lower().strip()
        our_cat = LABEL_MAP.get(raw_label)
        if our_cat is None:
            skipped += 1
            continue
        if counts[our_cat] >= GRID_LIMIT:
            continue

        image = item["image"]  # PIL Image
        n = counts[our_cat]
        image.save(IMAGES_DIR / our_cat / f"img_{n:04d}.jpg")
        counts[our_cat] += 1

    print("\n  Grid images saved:")
    for cat, n in counts.items():
        print(f"    {cat:<15} {n} images")
    print(f"  Skipped (other categories): {skipped}")

    total = sum(counts.values())
    if total == 0:
        print("\n  WARNING: Zero grid images saved. The dataset schema may have changed.")
        print("  Run scripts/build_index.py to check what's in data/images/")
        _ensure_fallback_images()
    else:
        print(f"\n[OK] Grid dataset done. {total} real reCAPTCHA tiles saved.")
        _rebuild_index(counts)


def _ensure_fallback_images() -> None:
    """
    If the HuggingFace download fails entirely, create sample
    images so the site still starts without crashing. The dev can replace
    these later with the real dataset or use Wikimedia Commons manually.
    """
    from PIL import Image, ImageDraw
    print("\n  Creating starter images (10 per category)...")
    for cat in GRID_CATEGORIES:
        out_dir = IMAGES_DIR / cat
        out_dir.mkdir(parents=True, exist_ok=True)
        existing = list(out_dir.glob("*.jpg")) + list(out_dir.glob("*.png"))
        if len(existing) >= 10:
            print(f"    {cat}: already has {len(existing)} images, skipping")
            continue
        for i in range(10):
            img = Image.new("RGB", (150, 150), color=(30 + i * 5, 60 + i * 4, 90 + i * 3))
            draw = ImageDraw.Draw(img)
            draw.text((20, 65), f"{cat} #{i+1}", fill=(255, 255, 255))
            img.save(out_dir / f"starter_{i:02d}.jpg")
        print(f"    {cat}: 10 starter images created")
    _rebuild_index()


def _rebuild_index(counts: dict | None = None) -> None:
    """Scan data/images/<category>/ and write data/index.json."""
    banner("Rebuilding data/index.json")
    index = []
    for cat in GRID_CATEGORIES:
        cat_dir = IMAGES_DIR / cat
        if not cat_dir.exists():
            continue
        files = sorted(cat_dir.glob("*.jpg")) + sorted(cat_dir.glob("*.png"))
        for f in files:
            # Store path relative to data/ dir so it's portable
            rel = f.relative_to(DATA_DIR).as_posix()
            index.append({"path": rel, "categories": [cat]})

    INDEX_PATH.write_text(json.dumps(index, indent=2))
    print(f"  Written {len(index)} entries -> {INDEX_PATH.relative_to(ROOT)}")


# ═════════════════════════════════════════════════════════════════════════════
# Entry point
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("CAPTCHA Solver Testbed - Dataset Downloader")
    print("============================================")
    print(f"Root     : {ROOT}")
    print(f"Data dir : {DATA_DIR}")
    print(f"Digit limit : {DIGIT_LIMIT} images (train split)")
    print(f"Grid limit  : {GRID_LIMIT} images per category")

    download_digit_dataset()
    download_grid_dataset()

    print("\nAll done! Next steps:")
    print("   1.  Start the site:  uvicorn app.main:app --reload")
    print("   2.  Train your agent on: data/digit_samples/")
    print("   3.  Benchmark via the API:  GET /api/captcha-digit  etc.")
