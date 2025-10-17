#!/usr/bin/env python3
"""
import_recipes.py

Reads the Epicurious-derived CSV (exactly as referenced in your .env), uploads images
to Cloudinary (folder from .env), and upserts recipe documents into MongoDB.

Usage:
    python import_recipes.py            # uses .env for config
    python import_recipes.py --workers 4 --force
"""

import os
import argparse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional, Dict
import time
import urllib3

import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv
from pymongo import MongoClient
import cloudinary
import cloudinary.uploader

# ---- Logging ----
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-6s | %(message)s"
)
logger = logging.getLogger("import_recipes")

# Suppress urllib3 connection pool warnings
logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)

# ---- Load .env ----
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
CLOUD_NAME = os.getenv("CLOUD_NAME")
CLOUD_API_KEY = os.getenv("CLOUD_API_KEY")
CLOUD_API_SECRET = os.getenv("CLOUD_API_SECRET")
CLOUD_FOLDER = os.getenv("CLOUD_FOLDER", "recipes")
CSV_PATH = os.getenv("CSV_PATH", "Food Ingredients and Recipe Dataset with Image Name Mapping.csv")
IMAGE_DIR = os.getenv("IMAGE_DIR", "Food Images/Food Images")
DEFAULT_CONCURRENCY = int(os.getenv("CONCURRENCY", "4"))  # Reduced default from 8 to 4

if not all([MONGO_URI, CLOUD_NAME, CLOUD_API_KEY, CLOUD_API_SECRET]):
    logger.error("Missing one of MONGO_URI or CLOUD_* env vars. Fill .env and retry.")
    raise SystemExit(1)

# ---- Configure Cloudinary ----
cloudinary.config(
    cloud_name=CLOUD_NAME,
    api_key=CLOUD_API_KEY,
    api_secret=CLOUD_API_SECRET,
    secure=True
)

# ---- MongoDB client ----
mongo_client = MongoClient(MONGO_URI)
db = mongo_client.get_default_database()
recipes_col = db.get_collection("recipes")

# ---- Helpers ----
def normalize_public_id(image_name: str) -> str:
    """Deterministic public_id: CLOUD_FOLDER/<image-stem>"""
    return f"{CLOUD_FOLDER}/{Path(image_name).stem}"

def upload_image(local_path: Path, image_name: str) -> Optional[Dict]:
    """Upload single image to Cloudinary. Returns metadata dict or None on failure."""
    try:
        # use folder param (Cloudinary will prefix public_id with folder)
        public_id = Path(image_name).stem  # we pass folder separately
        res = cloudinary.uploader.upload(
            str(local_path),
            folder=CLOUD_FOLDER,
            public_id=public_id,
            use_filename=True,
            unique_filename=False,
            overwrite=False,
        )
        return {
            "url": res.get("secure_url"),
            "public_id": res.get("public_id"),
            "width": res.get("width"),
            "height": res.get("height"),
            "format": res.get("format"),
        }
    except Exception as e:
        logger.warning(f"Cloudinary upload failed for {image_name}: {e}")
        return None

def make_doc(row: pd.Series, image_meta: Optional[Dict]) -> Dict:
    """Construct MongoDB document from CSV row and image metadata."""
    cleaned_raw = row.get("Cleaned_Ingredients") or ""
    # Some cleaned fields may already be stringified lists or comma-joined
    if isinstance(cleaned_raw, str) and cleaned_raw.strip():
        cleaned_list = [s.strip() for s in cleaned_raw.split(",") if s.strip()]
    else:
        cleaned_list = []

    doc = {
        "title": row.get("Title") or "",
        "ingredients_raw": row.get("Ingredients") or "",
        "ingredients_cleaned": cleaned_list,
        "instructions": row.get("Instructions") or "",
        "source_meta": {
            "image_name": row.get("Image_Name") or ""
        }
    }
    if image_meta:
        doc["image"] = image_meta
    return doc

def process_row(row: pd.Series, image_dir: Path, force: bool = False) -> Dict:
    """Process a single CSV row: upload image (if present) and upsert doc into MongoDB."""
    img_name = row.get("Image_Name") or ""
    title = row.get("Title") or "<no-title>"

    try:
        # If image_name provided, try to find an existing record by source_meta.image_name
        if img_name:
            existing = recipes_col.find_one({"source_meta.image_name": img_name})
            if existing and existing.get("image") and not force:
                return {"status": "skipped", "reason": "exists_with_image", "title": title, "image": img_name}

        image_meta = None
        if img_name:
            # Try multiple variations to find the image file
            possible_paths = [
                image_dir / f"{img_name}.jpg",              # original + .jpg
                image_dir / img_name,                        # original as-is
                image_dir / f"-{img_name}.jpg",             # with leading hyphen + .jpg
                image_dir / f"-{img_name}",                 # with leading hyphen
            ]

            local_path = None
            for path in possible_paths:
                if path.exists() and path.is_file():
                    local_path = path
                    break

            if local_path is None:
                return {"status": "fail", "reason": "image_missing", "title": title, "image": img_name}

            image_meta = upload_image(local_path, img_name)
            if image_meta is None:
                return {"status": "fail", "reason": "upload_failed", "title": title, "image": img_name}

        doc = make_doc(row, image_meta)
        filter_q = {"source_meta.image_name": img_name} if img_name else {"title": doc["title"]}
        update = {"$set": doc}
        recipes_col.update_one(filter_q, update, upsert=True)
        return {"status": "ok", "title": title, "image": img_name}
    except Exception as e:
        logger.exception(f"Exception processing {title} / {img_name}")
        return {"status": "error", "reason": str(e), "title": title, "image": img_name}

# ---- Main ----
def main(args):
    csv_path = Path(args.csv or CSV_PATH)
    image_dir = Path(args.images or IMAGE_DIR)

    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        return
    if not image_dir.exists():
        logger.error(f"Image directory not found: {image_dir}")
        return

    logger.info(f"Loading CSV: {csv_path}")
    # safe read: explicit encoding and dtype to avoid surprises
    df = pd.read_csv(csv_path, dtype=str, encoding='utf-8', keep_default_na=False)

    # Limit rows if specified
    if args.limit and args.limit > 0:
        df = df.head(args.limit)
        logger.info(f"Limiting to first {args.limit} rows for testing")

    total = len(df)
    batch_size = args.batch_size
    logger.info(f"Rows to process: {total}  |  Batch size: {batch_size}  |  Workers: {args.workers}")

    failures = []
    skipped = 0
    processed = 0

    # Process in batches
    num_batches = (total + batch_size - 1) // batch_size

    for batch_num in range(num_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, total)
        batch_df = df.iloc[start_idx:end_idx]

        logger.info(f"Processing batch {batch_num + 1}/{num_batches} (rows {start_idx} to {end_idx-1})")

        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futures = {ex.submit(process_row, batch_df.iloc[i], image_dir, args.force): i for i in range(len(batch_df))}
            for fut in tqdm(as_completed(futures), total=len(batch_df), desc=f"Batch {batch_num + 1}/{num_batches}"):
                try:
                    res = fut.result()
                except Exception as e:
                    logger.exception("Unexpected thread exception")
                    failures.append({"status": "error", "reason": str(e)})
                    continue

                if res.get("status") in ("fail", "error"):
                    failures.append(res)
                elif res.get("status") == "skipped":
                    skipped += 1
                else:
                    processed += 1

        # Small delay between batches to avoid rate limits
        if batch_num < num_batches - 1:
            logger.info(f"Batch {batch_num + 1} complete. Waiting 2 seconds before next batch...")
            time.sleep(2)

    logger.info(f"Finished. inserted/updated: {processed}, skipped: {skipped}, failures: {len(failures)}")

    if failures:
        import csv
        out = Path("import_failures.csv")
        keys = set().union(*(f.keys() for f in failures))
        with out.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(keys))
            writer.writeheader()
            writer.writerows(failures)
        logger.info(f"Wrote failures to {out.resolve()}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import recipes CSV + images -> Cloudinary + MongoDB")
    parser.add_argument("--csv", help="Path to CSV (overrides .env CSV_PATH)")
    parser.add_argument("--images", help="Path to images dir (overrides .env IMAGE_DIR)")
    parser.add_argument("--workers", type=int, default=DEFAULT_CONCURRENCY, help="Concurrent worker threads")
    parser.add_argument("--force", action="store_true", help="Force upload & upsert even if record exists")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of rows to process (for testing)")
    parser.add_argument("--batch-size", type=int, default=30, help="Number of rows to process per batch")
    args = parser.parse_args()
    main(args)
