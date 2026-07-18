# app/ai/embeddings/__init__.py
# Expose core embedding functions at the package level.
from app.ai.embeddings.product_embedder import (
    embed_product,
    generate_embedding,
    build_document_text,
    get_model_info,
)

__all__ = [
    "embed_product",
    "generate_embedding",
    "build_document_text",
    "get_model_info",
]
