"""
load_data.py — One-time data seeding script.

Usage:
    export GEMINI_API_KEY=your_key_here
    python load_data.py [--json ../dataset/products.json] [--reset]

This script:
  1. Parses products.json
  2. Inserts all 100 products into SQLite
  3. Generates a multimodal embedding for each product
  4. Stores embeddings in ChromaDB
"""

import sys
import os
import json
import argparse
import time

# Ensure backend package is importable when run from project root
sys.path.insert(0, os.path.dirname(__file__))

from database import init_db, insert_product, get_product
from vector_store import upsert_product, delete_product as vs_delete, vector_count
from ingest import generate_multimodal_embedding


def load_data(json_path: str, reset: bool = False):
    print("=" * 60)
    print("  E-Commerce Multimodal RAG — Data Loader")
    print("=" * 60)

    # Validate API key
    if not os.environ.get("GEMINI_API_KEY"):
        print("[ERROR] GEMINI_API_KEY environment variable not set.")
        sys.exit(1)

    # Initialize database
    print("\n[1/4] Initializing SQLite database...")
    init_db()
    print("      ✓ Database schema ready")

    # Load JSON
    print(f"\n[2/4] Loading products from {json_path}...")
    with open(json_path, "r") as f:
        data = json.load(f)

    products = data.get("products", [])
    print(f"      ✓ Found {len(products)} products")

    # Validate schema
    required_fields = {
        "product_id", "title", "category", "brand", "price",
        "rating", "review_count", "description", "features", "image_url"
    }
    for p in products:
        missing = required_fields - set(p.keys())
        if missing:
            print(f"[ERROR] Product {p.get('product_id', '?')} missing fields: {missing}")
            sys.exit(1)
        if not p.get("description") or len(p["description"]) < 50:
            print(f"[WARN]  Product {p['product_id']} has short description")
        if not isinstance(p.get("features"), list) or len(p["features"]) < 3:
            print(f"[WARN]  Product {p['product_id']} has fewer than 3 features")

    # Insert into SQLite
    print("\n[3/4] Inserting products into SQLite...")
    inserted = 0
    skipped = 0
    for p in products:
        existing = get_product(p["product_id"])
        if existing and not reset:
            skipped += 1
            continue
        try:
            insert_product(p)
            inserted += 1
        except Exception as e:
            print(f"  [ERROR] Failed to insert {p['product_id']}: {e}")

    print(f"      ✓ Inserted: {inserted}, Skipped (already exist): {skipped}")

    # Generate embeddings and store in ChromaDB
    print("\n[4/4] Generating multimodal embeddings and indexing in ChromaDB...")
    print(f"      (This may take several minutes for {len(products)} products)\n")

    success = 0
    failed = 0
    start_time = time.time()

    for i, p in enumerate(products, 1):
        pid = p["product_id"]
        print(f"  [{i:3d}/{len(products)}] {pid} — {p['title'][:45]}...")

        try:
            embedding = generate_multimodal_embedding(p)
            upsert_product(pid, embedding, p)
            success += 1
            print(f"         ✓ Embedded ({len(embedding)} dims)")
        except Exception as e:
            failed += 1
            print(f"         ✗ FAILED: {e}")

        # Small delay to respect API rate limits
        if i % 10 == 0:
            elapsed = time.time() - start_time
            eta = (elapsed / i) * (len(products) - i)
            print(f"\n  --- Progress: {i}/{len(products)} | "
                  f"Elapsed: {elapsed:.0f}s | ETA: {eta:.0f}s ---\n")

    elapsed_total = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"  DONE in {elapsed_total:.1f}s")
    print(f"  SQLite products : {inserted + skipped}")
    print(f"  Vectors indexed : {success} (failed: {failed})")
    print(f"  Vector store    : {vector_count()} total vectors")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load products into DB and vector store")
    parser.add_argument(
        "--json",
        default=os.path.join(os.path.dirname(__file__), "../dataset/products.json"),
        help="Path to products.json",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Re-insert products even if they already exist",
    )
    args = parser.parse_args()
    load_data(args.json, args.reset)
