# ============================================================
# IDAM — Intelligent Automated Retail Store Backend
# app/ai/vectordb/chroma_client.py
#
# PURPOSE:
#   Manages the ChromaDB persistent vector store.
#   Acts as the SINGLE interface between the rest of the app
#   and ChromaDB — no other file should import chromadb directly.
#
# DESIGN:
#   - Singleton pattern: one ChromaDB client for the app lifetime
#   - One collection: "products"
#   - All product vectors stored with product_id as the document ID
#   - Supports upsert (add or update), batch upsert, query, delete
#   - Uses ChromaDB's local persistent mode (no server needed)
#
# CHROMA CONCEPTS:
#   - Collection  : A named group of embeddings (like a DB table)
#   - Document ID : The unique key per embedding (we use product_id)
#   - Embedding   : The float vector (384 dimensions)
#   - Metadata    : Extra fields stored alongside the vector
#   - Distance    : How far apart two vectors are (lower = more similar)
#
# ChromaDB uses cosine distance for text embeddings.
# Similarity = 1 - distance  (0.0 = totally different, 1.0 = identical)
# ============================================================

import logging
import os
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config.settings import settings

logger = logging.getLogger(__name__)

# ── Collection name constant ─────────────────────────────────
PRODUCTS_COLLECTION = "products"

# ── Singleton client and collection ─────────────────────────
_client: Optional[chromadb.PersistentClient] = None
_collection: Optional[chromadb.Collection] = None


def _get_client() -> chromadb.PersistentClient:
    """
    Return the singleton ChromaDB persistent client.
    Creates and connects on first call, reuses on every subsequent call.

    Data is stored on disk at chroma_db_path (./data/chroma_db).
    Survives server restarts automatically.
    """
    global _client
    if _client is None:
        chroma_path = settings.chroma_db_path  # "./data/chroma_db"
        os.makedirs(chroma_path, exist_ok=True)
        logger.info(f"[ChromaDB] Connecting to persistent store at: {chroma_path}")
        _client = chromadb.PersistentClient(
            path=chroma_path,
            settings=ChromaSettings(
                anonymized_telemetry=False,  # Disable telemetry (privacy)
                allow_reset=True,            # Allow collection resets during dev
            )
        )
        logger.info("[ChromaDB] Client initialized successfully.")
    return _client


def get_or_create_collection() -> chromadb.Collection:
    """
    Return the singleton 'products' collection.
    Creates it if it doesn't exist yet.

    Using cosine distance metric because:
    - sentence-transformers produces normalized vectors by default
    - Cosine similarity is the standard metric for text embeddings
    - It focuses on direction (meaning), not magnitude (length)
    """
    global _collection
    if _collection is None:
        client = _get_client()
        _collection = client.get_or_create_collection(
            name=PRODUCTS_COLLECTION,
            metadata={"hnsw:space": "cosine"},  # Cosine distance for text embeddings
        )
        count = _collection.count()
        logger.info(
            f"[ChromaDB] Collection '{PRODUCTS_COLLECTION}' ready. "
            f"Currently indexed: {count} products."
        )
    return _collection


def init_chroma() -> None:
    """
    Initialize ChromaDB at application startup.
    Called from main.py startup_event() after init_db().

    Creates the client and the products collection so they are
    ready before the first API request arrives.
    """
    logger.info("[ChromaDB] Initializing vector store...")
    get_or_create_collection()
    logger.info("[ChromaDB] Vector store ready.")


# ── Upsert operations ────────────────────────────────────────

def upsert_product(
    product_id: str,
    embedding: List[float],
    metadata: Dict[str, Any],
    document_text: str,
) -> None:
    """
    Add or update a single product embedding in ChromaDB.

    'Upsert' = insert if product_id is new, update if it already exists.
    This makes indexing idempotent — safe to call multiple times for
    the same product without creating duplicates.

    Args:
        product_id    : e.g. "PROD001" — used as the ChromaDB document ID
        embedding     : 384-dim float vector from product_embedder
        metadata      : Dict stored with the vector (name, category, brand, price)
                        These fields are returned in query results alongside the ID
        document_text : The raw text that was embedded (stored for inspection)
    """
    collection = get_or_create_collection()
    collection.upsert(
        ids=[product_id],
        embeddings=[embedding],
        metadatas=[metadata],
        documents=[document_text],
    )


def upsert_batch(
    product_ids: List[str],
    embeddings: List[List[float]],
    metadatas: List[Dict[str, Any]],
    document_texts: List[str],
) -> None:
    """
    Batch upsert multiple products in a single ChromaDB call.

    Much more efficient than calling upsert_product() in a loop —
    ChromaDB handles batch writes atomically and with less overhead.
    Used by the full catalog indexing pipeline.

    Args:
        product_ids    : List of product ID strings
        embeddings     : Parallel list of embedding vectors (same order)
        metadatas      : Parallel list of metadata dicts (same order)
        document_texts : Parallel list of document texts (same order)
    """
    if not product_ids:
        logger.warning("[ChromaDB] upsert_batch called with empty list — skipping.")
        return

    collection = get_or_create_collection()
    collection.upsert(
        ids=product_ids,
        embeddings=embeddings,
        metadatas=metadatas,
        documents=document_texts,
    )
    logger.info(f"[ChromaDB] Batch upserted {len(product_ids)} products into collection.")


# ── Query operation ──────────────────────────────────────────

def query_similar(
    query_embedding: List[float],
    n_results: int = 10,
) -> Dict[str, Any]:
    """
    Find the most semantically similar products to a query embedding.

    ChromaDB returns results sorted by cosine distance (ascending).
    Distance 0.0 = identical meaning, 1.0 = completely unrelated.
    search_service converts this to similarity score = 1 - distance.

    Args:
        query_embedding : The embedded search query (384-dim vector)
        n_results       : Maximum number of results to return

    Returns:
        Dict with keys:
          - ids       : List[List[str]]   — product_ids (outer = one query)
          - distances : List[List[float]] — cosine distances per result
          - metadatas : List[List[dict]]  — stored metadata per result
          - documents : List[List[str]]   — stored document texts per result
    """
    collection = get_or_create_collection()
    count = collection.count()

    if count == 0:
        logger.warning("[ChromaDB] Collection is empty — no products indexed yet.")
        return {"ids": [[]], "distances": [[]], "metadatas": [[]], "documents": [[]]}

    # Cap n_results at the actual collection size to avoid a ChromaDB error
    actual_n = min(n_results, count)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=actual_n,
        include=["distances", "metadatas", "documents"],
    )
    return results


# ── Delete operation ─────────────────────────────────────────

def delete_product(product_id: str) -> None:
    """
    Remove a product from ChromaDB by its product_id.

    Called when a product is removed from the catalog to keep
    ChromaDB in sync with SQLite. Not currently exposed in the API
    but available for future use.

    Args:
        product_id : e.g. "PROD001"
    """
    collection = get_or_create_collection()
    collection.delete(ids=[product_id])
    logger.info(f"[ChromaDB] Deleted product '{product_id}' from index.")


# ── Status / inspection ──────────────────────────────────────

def get_collection_count() -> int:
    """
    Return the number of products currently indexed in ChromaDB.
    Used by the GET /search/status endpoint.
    """
    collection = get_or_create_collection()
    return collection.count()


def reset_collection() -> None:
    """
    Delete and recreate the products collection.

    WARNING: This removes ALL indexed embeddings.
    Use only for a full clean re-index during development
    or if the collection becomes corrupted.

    In normal operation, prefer upsert_batch() which is idempotent.
    """
    global _collection
    client = _get_client()
    logger.warning("[ChromaDB] Resetting products collection — all embeddings will be deleted.")
    client.delete_collection(name=PRODUCTS_COLLECTION)
    _collection = None
    get_or_create_collection()
    logger.info("[ChromaDB] Collection reset and recreated successfully.")
