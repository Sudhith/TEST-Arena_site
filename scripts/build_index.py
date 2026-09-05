"""
scripts/build_index.py
───────────────────────
Scans data/images/<category>/ directories and writes data/index.json.

Run this whenever you add or remove images from the dataset:
  python scripts/build_index.py

The index format:
  [
    { "path": "images/bus/img_0001.jpg", "categories": ["bus"] },
    ...
  ]

Paths are relative to data/ so they work on any machine.
The server loads this file at startup via app/captcha_grid.py.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
IMAGES_DIR = DATA_DIR / "images"
INDEX_PATH = DATA_DIR / "index.json"

GRID_CATEGORIES = ["bus", "car", "traffic_light", "bicycle"]
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def build_index() -> list[dict]:
    index = []
    total = 0

    for cat in GRID_CATEGORIES:
        cat_dir = IMAGES_DIR / cat
        if not cat_dir.is_dir():
            print(f"  [WARN] Category dir not found: {cat_dir.relative_to(ROOT)}")
            continue

        files = sorted(f for f in cat_dir.iterdir() if f.suffix.lower() in IMAGE_EXTS)
        for f in files:
            rel = f.relative_to(DATA_DIR).as_posix()
            index.append({"path": rel, "categories": [cat]})

        total += len(files)
        print(f"  {cat:<15} {len(files):>5} images")

    return index


def main() -> None:
    print("Building data/index.json")
    print("─" * 40)

    if not IMAGES_DIR.is_dir():
        print(f"ERROR: {IMAGES_DIR} does not exist.")
        print("Run scripts/download_dataset.py first.")
        sys.exit(1)

    index = build_index()
    INDEX_PATH.write_text(json.dumps(index, indent=2))

    print("─" * 40)
    print(f"✅ Written {len(index)} entries → {INDEX_PATH.relative_to(ROOT)}")

    if len(index) < 40:
        print("\n⚠  WARNING: Fewer than 40 images total across all categories.")
        print("   The grid CAPTCHA needs at least 9 images per challenge.")
        print("   Run scripts/download_dataset.py to get more images.")


if __name__ == "__main__":
    main()
