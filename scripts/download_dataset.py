"""
scripts/download_dataset.py
----------------------------
Downloads real reCAPTCHA v2 grid tiles and 6-digit training samples.

Sources:
1. nobodyPerfecZ/recaptchav2-29k (Hugging Face)
   Real Google reCAPTCHA v2 image tiles (bicycle, bus, car, hydrant).
2. Wikimedia Commons API
   Real public domain urban traffic light tiles.
3. project-sloth/captcha-images (Hugging Face)
   Synthetic distorted numeric CAPTCHAs for offline OCR training.
"""

import io
import json
import os
import sys
import urllib.request
from pathlib import Path
from PIL import Image

# Force UTF-8 on Windows stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
IMAGES_DIR = DATA_DIR / "images"
INDEX_PATH = DATA_DIR / "index.json"

TARGET_PER_CAT = int(os.environ.get("GRID_LIMIT", 25))
CATEGORIES = ["bus", "car", "bicycle", "hydrant", "traffic_light"]


def resize_crop_150(img: Image.Image) -> Image.Image:
    """Center crop and resize PIL image to 150x150 RGB."""
    img = img.convert("RGB")
    width, height = img.size
    min_dim = min(width, height)
    left = (width - min_dim) // 2
    top = (height - min_dim) // 2
    cropped = img.crop((left, top, left + min_dim, top + min_dim))
    return cropped.resize((150, 150), Image.Resampling.LANCZOS)


def download_recaptcha_tiles():
    """Stream real reCAPTCHA v2 tiles from nobodyPerfecZ/recaptchav2-29k."""
    print("Connecting to Hugging Face dataset: nobodyPerfecZ/recaptchav2-29k...")
    from datasets import load_dataset

    ds = load_dataset("nobodyPerfecZ/recaptchav2-29k", split="train", streaming=True)
    
    # Label index mapping from dataset readme:
    # 0: bicycle, 1: bus, 2: car, 3: crosswalk, 4: hydrant
    index_to_cat = {
        0: "bicycle",
        1: "bus",
        2: "car",
        4: "hydrant",
    }

    counts = {cat: 0 for cat in index_to_cat.values()}
    
    # Clean out old synthetic starter files
    for cat in index_to_cat.values():
        cat_dir = IMAGES_DIR / cat
        cat_dir.mkdir(parents=True, exist_ok=True)
        for old in cat_dir.glob("starter_*.jpg"):
            old.unlink(missing_ok=True)

    print(f"Streaming {TARGET_PER_CAT} real images per category...")
    for item in ds:
        labels = item.get("labels", [])
        raw_img = item.get("image")
        if not raw_img or not labels:
            continue

        for idx, val in enumerate(labels):
            if val == 1 and idx in index_to_cat:
                cname = index_to_cat[idx]
                if counts[cname] < TARGET_PER_CAT:
                    tile = resize_crop_150(raw_img)
                    out_path = IMAGES_DIR / cname / f"real_{counts[cname]:04d}.jpg"
                    tile.save(out_path, format="JPEG", quality=92)
                    counts[cname] += 1

        if all(cnt >= TARGET_PER_CAT for cnt in counts.values()):
            break

    print("reCAPTCHA v2 tiles acquired:")
    for cat, cnt in counts.items():
        print(f"  {cat:<15}: {cnt} real photos")


def download_traffic_lights():
    """Fetch real urban traffic light images from Wikimedia Commons."""
    print("\nFetching real traffic light photos from Wikimedia Commons...")
    cat_dir = IMAGES_DIR / "traffic_light"
    cat_dir.mkdir(parents=True, exist_ok=True)
    for old in cat_dir.glob("starter_*.jpg"):
        old.unlink(missing_ok=True)

    url = (
        "https://commons.wikimedia.org/w/api.php?"
        "action=query&generator=search&gsrnamespace=6&"
        "gsrsearch=traffic+light+intersection&gsrlimit=50&"
        "prop=imageinfo&iiprop=url&iiurlwidth=300&format=json"
    )
    req = urllib.request.Request(
        url, headers={"User-Agent": "TestArenaResearcher/1.0 (academic-eval)"}
    )
    
    count = 0
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", {})
            for page in pages.values():
                if count >= TARGET_PER_CAT:
                    break
                ii = page.get("imageinfo", [{}])[0]
                thumb = ii.get("thumburl") or ii.get("url")
                if not thumb:
                    continue
                try:
                    img_req = urllib.request.Request(
                        thumb, headers={"User-Agent": "TestArenaResearcher/1.0"}
                    )
                    with urllib.request.urlopen(img_req, timeout=10) as ir:
                        raw = Image.open(io.BytesIO(ir.read()))
                        tile = resize_crop_150(raw)
                        out_path = cat_dir / f"real_{count:04d}.jpg"
                        tile.save(out_path, format="JPEG", quality=92)
                        count += 1
                except Exception:
                    continue
    except Exception as err:
        print(f"Wikimedia fetch warning: {err}")

    print(f"  traffic_light  : {count} real photos")


def build_index():
    """Rebuild data/index.json with real images."""
    print("\nRebuilding data/index.json...")
    index = []
    for cat in CATEGORIES:
        cat_dir = IMAGES_DIR / cat
        if not cat_dir.exists():
            continue
        files = sorted(cat_dir.glob("*.jpg")) + sorted(cat_dir.glob("*.png"))
        for f in files:
            rel = f.relative_to(DATA_DIR).as_posix()
            index.append({"path": rel, "categories": [cat]})

    INDEX_PATH.write_text(json.dumps(index, indent=2))
    print(f"Total indexed tiles: {len(index)} across {len(CATEGORIES)} categories")
    print("data/index.json updated successfully.")


if __name__ == "__main__":
    download_recaptcha_tiles()
    download_traffic_lights()
    build_index()
