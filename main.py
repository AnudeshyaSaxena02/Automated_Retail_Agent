# ============================================================
# IDAM Backend — main.py
# FastAPI application entry point.
# Registers all routers and initializes the database on startup.
# ============================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings
from app.database.connection import init_db, check_db_connection

# Phase 3 routers
from app.api import products, customers
# Phase 4 routers
from app.api import orders
# Phase 5 routers
from app.api import search
# Phase 6 routers
from app.api import llm
# Phase 5 — ChromaDB + indexing pipeline
from app.ai.vectordb.chroma_client import init_chroma
from app.ai.vectordb.product_index import index_all_products
from app.database.connection import SessionLocal

# Create the FastAPI app instance
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "IDAM — Intelligent Automated Retail Store Backend. "
        "An AI-powered shopping assistant with customer memory, "
        "dynamic budget learning, and personalized recommendations."
    ),
    docs_url="/docs",       # Swagger UI at http://localhost:8000/docs
    redoc_url="/redoc",     # ReDoc at http://localhost:8000/redoc
)

# ----------------------------
# CORS Middleware
# Allows the frontend (any origin during dev) to call this API.
# ----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Allow all origins (tighten in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------
# Startup Event
# Runs once when the server starts.
# Creates all DB tables if they don't exist.
# ----------------------------
@app.on_event("startup")
def startup_event():
    print(f"\n[IDAM] Starting {settings.app_name} v{settings.app_version}")
    print(f"[IDAM] Debug mode: {settings.debug}")

    # Phase 2 — SQLite database
    init_db()
    if check_db_connection():
        print("[IDAM] Database connection verified.")
    else:
        print("[IDAM] ERROR: Database connection failed. Check DATABASE_URL in .env")

    # Phase 5 — ChromaDB vector store
    print("[IDAM] Initializing ChromaDB vector store...")
    init_chroma()

    # Phase 5 — Auto-index all products on startup
    # Uses upsert — safe to run every time, no duplicates created.
    print("[IDAM] Auto-indexing product catalog into ChromaDB...")
    db = SessionLocal()
    try:
        result = index_all_products(db)
        print(
            f"[IDAM] Product indexing complete: "
            f"{result.indexed} indexed, "
            f"{result.skipped} skipped, "
            f"{result.errors} errors."
        )
    except Exception as exc:
        print(f"[IDAM] WARNING: Product indexing failed at startup: {exc}")
        print("[IDAM] Semantic search will be unavailable until POST /search/index is called.")
    finally:
        db.close()

    print(f"[IDAM] API docs available at: http://localhost:8000/docs\n")


# ----------------------------
# Root endpoint — quick health check
# ----------------------------
@app.get("/", tags=["Health"])
def root():
    """Root endpoint — confirms the API is running."""
    return {
        "status": "running",
        "app": settings.app_name,
        "version": settings.app_version,
        "docs": "http://localhost:8000/docs",
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint — confirms DB connection is alive."""
    db_ok = check_db_connection()
    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "error",
    }


# ----------------------------
# Register Routers
# Each router handles a group of related endpoints.
# More routers will be added in Phases 5–9.
# ----------------------------
# Phase 3
app.include_router(products.router,  prefix="/products",  tags=["Products"])
app.include_router(customers.router, prefix="/customers", tags=["Customers"])
# Phase 4
app.include_router(orders.router,    prefix="/orders",    tags=["Orders"])
# Phase 5
app.include_router(search.router,    prefix="/search",    tags=["Semantic Search"])

# Phase 6
app.include_router(llm.router,       prefix="/llm",       tags=["LLM"])

# Phase 7+:
# from app.api import chat, recommendations
# app.include_router(chat.router,            prefix="/chat",            tags=["Chat"])
# app.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])
