# ============================================================
# IDAM — Intelligent Automated Retail Store Backend
# app/database/connection.py
#
# PURPOSE:
#   Manages the SQLite database connection using SQLAlchemy.
#   Provides:
#     - engine       : The SQLAlchemy engine (talks to SQLite)
#     - SessionLocal : A session factory (creates DB sessions)
#     - get_db()     : FastAPI dependency (injects a DB session into routes)
#     - init_db()    : Creates all tables on first run (called at app startup)
#
# HOW SESSIONS WORK:
#   Each API request gets its own isolated DB session.
#   The session is automatically closed after the request ends.
#   This prevents connection leaks.
#
# USAGE in a FastAPI route:
#   from app.database.connection import get_db
#   from sqlalchemy.orm import Session
#
#   @router.get("/example")
#   def example(db: Session = Depends(get_db)):
#       result = db.query(SomeModel).all()
#       return result
# ============================================================

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.config.settings import settings


# ----------------------------
# Step 1: Create the data/ directory if it doesn't exist.
# SQLite needs the directory to exist before creating the .db file.
# ----------------------------
os.makedirs("data", exist_ok=True)


# ----------------------------
# Step 2: Create the SQLAlchemy engine.
#
# The engine is the core connection to the SQLite file.
# connect_args={"check_same_thread": False} is required for SQLite
# because FastAPI runs in multiple threads and SQLite's default
# behavior rejects cross-thread connections.
# ----------------------------
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # Required for SQLite with FastAPI
    echo=settings.debug,  # Print SQL queries to console when debug=True (helpful for dev)
)


# ----------------------------
# Step 3: Create a session factory.
#
# SessionLocal is a class that creates new Session objects.
# autocommit=False : we manually commit transactions
# autoflush=False  : we manually flush changes
# ----------------------------
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# ----------------------------
# Step 4: FastAPI dependency — get_db()
#
# This function is used as a FastAPI dependency injection.
# It creates a new DB session for each request and closes it
# automatically when the request is done, even if an error occurs.
# ----------------------------
def get_db():
    """
    FastAPI dependency that provides a database session per request.

    Usage in a route:
        def my_route(db: Session = Depends(get_db)):
            ...
    """
    db: Session = SessionLocal()
    try:
        yield db          # Give the session to the route handler
    finally:
        db.close()        # Always close — prevents connection leaks


# ----------------------------
# Step 5: init_db()
#
# Called once at application startup (in main.py).
# Creates all tables defined in models.py if they don't already exist.
# Safe to call multiple times — SQLAlchemy checks before creating.
# ----------------------------
def init_db():
    """
    Create all database tables on application startup.
    Uses SQLAlchemy's metadata to detect and create missing tables.
    Existing tables are left untouched.
    """
    # Import Base here (not at top) to avoid circular imports.
    # models.py imports from this file, so we import models here lazily.
    from app.database.models import Base

    print("[DB] Initializing database...")
    Base.metadata.create_all(bind=engine)
    print("[DB] Database tables created (or already exist).")


# ----------------------------
# Step 6: Verify connection (optional utility)
# ----------------------------
def check_db_connection() -> bool:
    """
    Test if the database connection is working.
    Returns True if OK, False otherwise.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"[DB] Database connection failed: {e}")
        return False
