# ============================================================
# IDAM — Intelligent Automated Retail Store Backend
# app/ai/embeddings/product_embedder.py
#
# PURPOSE:
#   Converts product data into dense vector embeddings for
#   semantic similarity search.
#
# DESIGN:
#   - Loads the embedding model ONCE at module import time
#     (singleton pattern — avoids repeated 90MB model loading)
#   - build_document_text() assembles a rich natural-language
#     document from all product fields (name, category, brand,
#     description, specs, tags) so that semantic queries like
#     "gaming laptop for AI" match even if those words aren't
#     in the product name directly
#   - generate_embedding() returns a flat List[float] (384-dim)
#     ready to be stored in ChromaDB
#
# MODEL:
#   all-MiniLM-L6-v2 from sentence-transformers
#   - 384 dimensions, ~90MB
#   - Downloads on first run, cached locally afterwards
#   - No API key required
#   - CPU-friendly, fast enough for 20-100 products at startup
# ============================================================

import json
import logging
from typing import List, Optional

from sentence_transformers import SentenceTransformer
from app.config.settings import settings

logger = logging.getLogger(__name__)


# ── Singleton model instance ─────────────────────────────────
# The model is loaded once when this module is first imported.
# Every subsequent call reuses the same in-memory model object.
# This avoids reloading 90MB from disk on every embedding request.
_model: Optional[SentenceTransformer] = None


def _get_model() -> SentenceTransformer:
    """
    Return the shared SentenceTransformer model instance.
    Loads the model on first call, returns the cached instance thereafter.
    """
    global _model
    if _model is None:
        model_name = settings.embedding_model  # "all-MiniLM-L6-v2"
        logger.info(f"[Embedder] Loading embedding model: {model_name}")
        _model = SentenceTransformer(model_name)
        dim = _model.get_sentence_embedding_dimension()
        logger.info(f"[Embedder] Model loaded successfully. Vector dimensions: {dim}")
    return _model


# ── Document construction ────────────────────────────────────

def build_document_text(
    product_id: str,
    name: str,
    category: str,
    brand: Optional[str],
    description: Optional[str],
    specifications: Optional[str],   # Raw JSON string from DB
    tags: Optional[str],             # Raw JSON string from DB
) -> str:
    """
    Construct a rich natural-language document from product fields.

    WHY THIS MATTERS:
        The quality of semantic search depends entirely on what text
        gets embedded. A sparse document like "Dell Laptop" will miss
        queries like "portable computer for machine learning students".

        By combining ALL product fields into one structured paragraph,
        we give the model enough context to bridge the gap between
        natural-language queries and structured product catalog data.

    EXAMPLE OUTPUT for PROD003 (gaming laptop):
        Product: Lenovo IdeaPad Gaming 3
        Category: Laptops
        Brand: Lenovo
        Description: High-performance gaming laptop with NVIDIA RTX 3050...
        Specifications: RAM: 16GB, Storage: 512GB SSD, Display: 15.6 inch FHD
        Tags: gaming, laptop, high-performance, nvidia, students
        Use for: gaming, laptop, high-performance, nvidia, students

    This ensures a query like "gaming laptop for AI" correctly maps to
    this product even though the word "AI" isn't in the product name.
    The tags and specs provide the semantic bridge.

    Args:
        product_id    : e.g. "PROD003"
        name          : e.g. "Lenovo IdeaPad Gaming 3"
        category      : e.g. "Laptops"
        brand         : e.g. "Lenovo"
        description   : Full product description text
        specifications: JSON string — {"RAM": "16GB", "Storage": "512GB SSD"}
        tags          : JSON string — ["gaming", "laptop", "high-performance"]

    Returns:
        A single multi-line string ready for embedding.
    """

    # -- Parse JSON fields safely --------------------------------
    specs_dict: dict = {}
    if specifications:
        try:
            specs_dict = json.loads(specifications)
        except (json.JSONDecodeError, TypeError):
            specs_dict = {}

    tags_list: list = []
    if tags:
        try:
            tags_list = json.loads(tags)
        except (json.JSONDecodeError, TypeError):
            tags_list = []

    # -- Build the document lines --------------------------------
    parts = []

    parts.append(f"Product: {name}")
    parts.append(f"Category: {category}")

    if brand:
        parts.append(f"Brand: {brand}")

    if description and description.strip():
        parts.append(f"Description: {description.strip()}")

    # Convert specs dict into a readable "Key: Value, Key: Value" string
    if specs_dict:
        specs_str = ", ".join(f"{k}: {v}" for k, v in specs_dict.items())
        parts.append(f"Specifications: {specs_str}")

    # Tags appear twice — once labeled "Tags" and once as "Use for" —
    # to give them slightly more semantic weight during embedding.
    if tags_list:
        tags_str = ", ".join(str(t) for t in tags_list)
        parts.append(f"Tags: {tags_str}")
        parts.append(f"Use for: {tags_str}")

    return "\n".join(parts)


# ── Embedding generation ─────────────────────────────────────

def generate_embedding(text: str) -> List[float]:
    """
    Generate a 384-dimensional embedding vector for the given text.

    Uses the singleton sentence-transformers model.
    Converts from numpy array to plain Python list for ChromaDB
    compatibility and JSON serializability.

    Args:
        text : Any string — a product document OR a search query.
               The same function handles both cases, which is correct:
               embeddings are only comparable when generated by the
               same model from both sides (query and document).

    Returns:
        List[float] with 384 elements (all-MiniLM-L6-v2 output size).
    """
    model = _get_model()
    vector = model.encode(text, convert_to_numpy=True)
    return vector.tolist()


# ── Convenience wrapper ──────────────────────────────────────

def embed_product(
    product_id: str,
    name: str,
    category: str,
    brand: Optional[str],
    description: Optional[str],
    specifications: Optional[str],
    tags: Optional[str],
) -> tuple:
    """
    Build the document text and generate its embedding in one call.

    Returns:
        (document_text: str, embedding_vector: List[float])

    The document_text is returned alongside the vector so callers
    can store it in ChromaDB for debugging / inspection.
    """
    doc_text = build_document_text(
        product_id=product_id,
        name=name,
        category=category,
        brand=brand,
        description=description,
        specifications=specifications,
        tags=tags,
    )
    embedding = generate_embedding(doc_text)
    return doc_text, embedding


def get_model_info() -> dict:
    """
    Return metadata about the currently loaded embedding model.
    Used by the GET /search/status endpoint.
    """
    model = _get_model()
    return {
        "model_name": settings.embedding_model,
        "vector_dimensions": model.get_sentence_embedding_dimension(),
        "status": "loaded",
    }
