# app/ai/vectordb/__init__.py
# Expose vector store and indexing functions at the package level.
from app.ai.vectordb.chroma_client import (
    init_chroma,
    get_collection_count,
    upsert_product,
    upsert_batch,
    query_similar,
    delete_product,
    reset_collection,
)
from app.ai.vectordb.product_index import (
    index_all_products,
    index_single_product,
)

__all__ = [
    "init_chroma",
    "get_collection_count",
    "upsert_product",
    "upsert_batch",
    "query_similar",
    "delete_product",
    "reset_collection",
    "index_all_products",
    "index_single_product",
]
