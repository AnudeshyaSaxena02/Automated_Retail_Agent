# ============================================================
# IDAM — Intelligent Automated Retail Store Backend
# app/ai/vectordb/product_index.py
#
# PURPOSE:
#   The product indexing pipeline.
#   Reads every product from SQLite, generates embeddings,
#   and upserts them into ChromaDB in batch.
#
# INDEXING WORKFLOW (per product):
#   1. Load Product ORM object from SQLite
#   2. product_embedder.embed_product() →
#        a. build_document_text()  — assembles rich NL document
#        b. generate_embedding()   — encodes to 384-dim vector
#   3. chroma_client.upsert_batch() — stores vectors + metadata
#
# WHEN IS INDEXING CALLED?
#   - At application startup (main.py) — indexes all products once
#   - POST /search/index             — manual full re-index trigger
#   - POST /search/index/{id}        — single product re-index
#     (useful after adding a new product via POST /products)
#
# IDEMPOTENCY:
#   Uses upsert — calling index_all_products() multiple times is
#   safe. Existing products are updated, new ones are added.
# ============================================================

import logging
from dataclasses import dataclass, field
from typing import List, Optional

from sqlalchemy.orm import Session

from app.database.models import Product
from app.ai.embeddings.product_embedder import embed_product
from app.ai.vectordb.chroma_client import upsert_batch, upsert_product

logger = logging.getLogger(__name__)


# ── Result dataclass ─────────────────────────────────────────

@dataclass
class IndexResult:
    """
    Summary of an indexing operation.
    Returned by index_all_products() and index_single_product().
    Serialized into the API response body.
    """
    indexed: int = 0        # Successfully indexed products
    skipped: int = 0        # Skipped (e.g. no description and no tags)
    errors: int = 0         # Products that failed to embed/upsert
    error_details: List[str] = field(default_factory=list)  # Error messages for debugging


# ── Metadata builder ─────────────────────────────────────────

def _build_metadata(product: Product) -> dict:
    """
    Build the metadata dict stored alongside each vector in ChromaDB.

    These fields are returned with every query result without needing
    to hit SQLite, which speeds up search response construction.

    NOTE: ChromaDB metadata values must be str, int, float, or bool.
          No nested dicts or lists. Convert price to float, keep others as str.
    """
    return {
        "product_id": product.product_id,
        "name":       product.name,
        "category":   product.category or "",
        "brand":      product.brand or "",
        "price":      float(product.price),
        "stock":      int(product.stock),
    }


# ── Core indexing functions ───────────────────────────────────

def index_all_products(db: Session) -> IndexResult:
    """
    Index every product in the SQLite catalog into ChromaDB.

    Uses batch upsert for efficiency — all embeddings are sent
    to ChromaDB in a single call rather than one-by-one.

    This function is called:
      - At application startup in main.py (so the index is always ready)
      - Via POST /search/index for manual re-indexing

    Args:
        db : Active SQLAlchemy database session

    Returns:
        IndexResult with counts of indexed / skipped / errors
    """
    logger.info("[Indexer] Starting full product indexing pipeline...")
    result = IndexResult()

    # ── Load all products from SQLite ────────────────────────
    products: List[Product] = db.query(Product).all()

    if not products:
        logger.warning("[Indexer] No products found in database — nothing to index.")
        return result

    logger.info(f"[Indexer] Found {len(products)} products to index.")

    # ── Prepare batch lists ──────────────────────────────────
    batch_ids:      List[str]         = []
    batch_vectors:  List[List[float]] = []
    batch_metadata: List[dict]        = []
    batch_docs:     List[str]         = []

    for product in products:
        try:
            # Generate document text + embedding vector
            doc_text, embedding = embed_product(
                product_id     = product.product_id,
                name           = product.name,
                category       = product.category,
                brand          = product.brand,
                description    = product.description,
                specifications = product.specifications,
                tags           = product.tags,
            )

            # Build metadata for this product
            metadata = _build_metadata(product)

            # Accumulate into batch lists
            batch_ids.append(product.product_id)
            batch_vectors.append(embedding)
            batch_metadata.append(metadata)
            batch_docs.append(doc_text)

            result.indexed += 1

        except Exception as exc:
            # Log the error but continue — don't let one bad product stop the rest
            error_msg = f"PROD '{product.product_id}': {str(exc)}"
            logger.error(f"[Indexer] Failed to embed product — {error_msg}")
            result.errors += 1
            result.error_details.append(error_msg)

    # ── Batch upsert all successful embeddings into ChromaDB ─
    if batch_ids:
        try:
            upsert_batch(
                product_ids    = batch_ids,
                embeddings     = batch_vectors,
                metadatas      = batch_metadata,
                document_texts = batch_docs,
            )
            logger.info(
                f"[Indexer] Indexing complete. "
                f"Indexed: {result.indexed}, "
                f"Skipped: {result.skipped}, "
                f"Errors: {result.errors}"
            )
        except Exception as exc:
            # If the batch upsert itself fails, mark all as errored
            error_msg = f"Batch upsert failed: {str(exc)}"
            logger.error(f"[Indexer] {error_msg}")
            result.errors += result.indexed
            result.indexed = 0
            result.error_details.append(error_msg)

    return result


def index_single_product(db: Session, product_id: str) -> IndexResult:
    """
    Index a single product by its product_id.

    Used after a new product is added via POST /products so it
    becomes immediately searchable via semantic search.

    Args:
        db         : Active SQLAlchemy database session
        product_id : The product's string ID, e.g. "PROD021"

    Returns:
        IndexResult (indexed=1 on success, errors=1 on failure)
    """
    result = IndexResult()

    # ── Load from SQLite ─────────────────────────────────────
    product: Optional[Product] = (
        db.query(Product)
        .filter(Product.product_id == product_id)
        .first()
    )

    if not product:
        error_msg = f"Product '{product_id}' not found in database."
        logger.error(f"[Indexer] {error_msg}")
        result.errors = 1
        result.error_details.append(error_msg)
        return result

    # ── Embed and upsert ─────────────────────────────────────
    try:
        doc_text, embedding = embed_product(
            product_id     = product.product_id,
            name           = product.name,
            category       = product.category,
            brand          = product.brand,
            description    = product.description,
            specifications = product.specifications,
            tags           = product.tags,
        )

        metadata = _build_metadata(product)

        upsert_product(
            product_id    = product.product_id,
            embedding     = embedding,
            metadata      = metadata,
            document_text = doc_text,
        )

        logger.info(f"[Indexer] Successfully indexed product '{product_id}'.")
        result.indexed = 1

    except Exception as exc:
        error_msg = f"Failed to index product '{product_id}': {str(exc)}"
        logger.error(f"[Indexer] {error_msg}")
        result.errors = 1
        result.error_details.append(error_msg)

    return result
