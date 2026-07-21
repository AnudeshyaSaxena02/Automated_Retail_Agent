#!/usr/bin/env python
"""
scripts/reset_and_seed.py
=========================
Drops ALL tables and re-seeds the database from scratch.

USE CASES:
  - Demo resets between presentations
  - Development resets after schema experiments
  - Starting fresh after data corruption

WARNING: This deletes ALL existing data permanently.

Usage:
    python scripts/reset_and_seed.py
    python scripts/reset_and_seed.py --yes   # Skip confirmation prompt
"""

import sys
import os

# Allow running from project root: python scripts/reset_and_seed.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import init_db, SessionLocal
from app.database.models import Base
from sqlalchemy import create_engine
from app.config.settings import settings


def reset_and_seed(skip_confirm: bool = False):
    if not skip_confirm:
        print("\n[reset_and_seed] ⚠  WARNING: This will DELETE all data and re-seed.")
        answer = input("Type 'yes' to continue: ").strip().lower()
        if answer != "yes":
            print("[reset_and_seed] Aborted.")
            return

    # ── Step 1: Drop all tables ───────────────────────────────
    print("\n[reset_and_seed] Dropping all tables...")
    engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
    Base.metadata.drop_all(bind=engine)
    print("[reset_and_seed] All tables dropped.")

    # ── Step 2: Re-create tables ──────────────────────────────
    print("[reset_and_seed] Re-creating schema...")
    Base.metadata.create_all(bind=engine)
    print("[reset_and_seed] Schema created.")

    # ── Step 3: Seed data ─────────────────────────────────────
    print("[reset_and_seed] Seeding data...")
    from app.database.seed import seed
    seed()

    # ── Step 4: Re-index ChromaDB ─────────────────────────────
    print("\n[reset_and_seed] Re-indexing products in ChromaDB...")
    try:
        from app.ai.vectordb.chroma_client import init_chroma
        from app.ai.vectordb.product_index import index_all_products

        init_chroma()
        db = SessionLocal()
        try:
            result = index_all_products(db)
            print(
                f"[reset_and_seed] ChromaDB indexing complete: "
                f"{result.indexed} indexed, {result.skipped} skipped, "
                f"{result.errors} errors."
            )
        finally:
            db.close()
    except Exception as exc:
        print(f"[reset_and_seed] WARNING: ChromaDB indexing failed: {exc}")
        print("[reset_and_seed] Run POST /search/index to index manually after starting the server.")

    print("\n[reset_and_seed] ✓ Reset complete. Run 'uvicorn main:app --reload' to start.")


if __name__ == "__main__":
    skip = "--yes" in sys.argv or "-y" in sys.argv
    reset_and_seed(skip_confirm=skip)
