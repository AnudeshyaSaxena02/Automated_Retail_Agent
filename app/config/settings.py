# ============================================================
# IDAM — Intelligent Automated Retail Store Backend
# app/config/settings.py
#
# PURPOSE:
#   Single source of truth for all configuration values.
#   Reads from the .env file automatically.
#   Every part of the application imports from here.
#
# HOW IT WORKS:
#   Pydantic BaseSettings reads environment variables from .env
#   and validates their types. If a required variable is missing,
#   the app will raise a clear error at startup.
#
# USAGE (in any file):
#   from app.config.settings import settings
#   print(settings.database_url)
# ============================================================

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Application settings loaded from the .env file.

    All fields have types and defaults defined here.
    Pydantic validates them automatically when the app starts.
    """

    # ----------------------------
    # Application
    # ----------------------------
    app_name: str = Field(default="IDAM Retail Store Backend", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    debug: bool = Field(default=True, alias="DEBUG")

    # ----------------------------
    # Database
    # ----------------------------
    database_url: str = Field(
        default="sqlite:///./data/idam.db",
        alias="DATABASE_URL"
    )

    # ----------------------------
    # LLM — Provider Selection (Phase 6)
    # ----------------------------
    llm_provider: str = Field(
        default="groq",
        alias="LLM_PROVIDER",
        description="Active LLM provider: 'groq' or 'gemini'. Groq is primary, Gemini is fallback.",
    )

    llm_timeout: int = Field(
        default=30,
        alias="LLM_TIMEOUT",
        ge=5,
        le=120,
        description="Seconds to wait for an LLM response before raising a timeout error.",
    )

    # ----------------------------
    # LLM — Groq (Primary)
    # ----------------------------
    groq_api_key: str = Field(default="your_groq_api_key_here", alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", alias="GROQ_MODEL")

    # ----------------------------
    # LLM — Gemini (Fallback)
    # ----------------------------
    gemini_api_key: str = Field(default="your_gemini_api_key_here", alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-1.5-flash", alias="GEMINI_MODEL")

    # ----------------------------
    # Embeddings
    # ----------------------------
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        alias="EMBEDDING_MODEL"
    )

    # ----------------------------
    # ChromaDB Vector Store
    # ----------------------------
    chroma_db_path: str = Field(default="./data/chroma_db", alias="CHROMA_DB_PATH")

    # ----------------------------
    # Semantic Search
    #
    # similarity_threshold: minimum cosine similarity score (0.0–1.0) a
    # product must reach to appear in search results.
    #
    # HOW TO CHOOSE A VALUE:
    #   0.0  — No filter. Everything returned (good for debugging).
    #   0.25 — Loose filter. Cuts off truly unrelated products.
    #   0.30 — Recommended default. Keeps semantic matches, drops noise.
    #   0.50 — Strict filter. Only high-confidence matches.
    #
    # Callers can override per-request via the min_score query param.
    # Set SIMILARITY_THRESHOLD in .env to change the server-wide default.
    # ----------------------------
    similarity_threshold: float = Field(
        default=0.3,
        alias="SIMILARITY_THRESHOLD",
        ge=0.0,
        le=1.0,
    )

    # ----------------------------
    # RAG Pipeline (Phase 7)
    # ----------------------------
    rag_top_k: int = Field(
        default=5,
        alias="RAG_TOP_K",
        ge=1,
        le=20,
        description=(
            "Number of products to retrieve from ChromaDB per RAG query. "
            "Higher values give the LLM more context but increase prompt length."
        ),
    )

    # ----------------------------
    # Recommendation Engine (Phase 8)
    # ----------------------------
    recommendation_top_k: int = Field(
        default=10,
        alias="RECOMMENDATION_TOP_K",
        ge=1,
        le=50,
        description=(
            "Number of products to return from the recommendation engine. "
            "Higher values give more recommendations but slow scoring slightly."
        ),
    )

    recommendation_recency_days: int = Field(
        default=30,
        alias="RECOMMENDATION_RECENCY_DAYS",
        ge=1,
        le=365,
        description=(
            "Products purchased within this many days are excluded from recommendations. "
            "Default 30 days — avoids re-recommending very recent purchases."
        ),
    )

    class Config:
        """
        Tell Pydantic where to find the .env file.
        env_file: path to the .env file (relative to where the app is run from)
        extra: ignore any unknown variables in .env — keeps things flexible
        """
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        populate_by_name = True


# ----------------------------
# Create a singleton settings instance.
# Import this everywhere: from app.config.settings import settings
# ----------------------------
settings = Settings()
