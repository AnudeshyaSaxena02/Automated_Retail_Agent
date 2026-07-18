# ============================================================
# app/api/products.py
#
# PURPOSE:
#   FastAPI router for all product-related endpoints.
#   Routes are thin — they only handle HTTP concerns
#   (validation, status codes, error responses).
#   All logic lives in product_service.py.
#
# ENDPOINTS:
#   GET  /products              — List all products (with filters)
#   POST /products              — Add a new product
#   GET  /products/{product_id} — Get a single product
#   GET  /products/search       — Keyword search (text match)
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database.connection import get_db
from app.schemas.product import ProductCreate, ProductResponse, ProductListResponse
from app.services import product_service

router = APIRouter()


@router.get("", response_model=ProductListResponse, summary="List all products")
def list_products(
    category: Optional[str] = Query(None, description="Filter by category, e.g. 'Laptops'"),
    brand: Optional[str] = Query(None, description="Filter by brand, e.g. 'Lenovo'"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price in INR"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price in INR"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Results to skip"),
    db: Session = Depends(get_db),
):
    """
    List all products with optional filters and pagination.

    Examples:
    - /products?category=Laptops&max_price=60000
    - /products?brand=Samsung&limit=10
    """
    products, total = product_service.get_all_products(
        db, category=category, brand=brand,
        min_price=min_price, max_price=max_price,
        limit=limit, offset=offset,
    )
    return {"total": total, "products": products}


@router.get("/search", response_model=ProductListResponse, summary="Keyword search products")
def search_products(
    q: str = Query(..., min_length=1, description="Search keyword"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Simple keyword search across product name, description, category, and brand.

    NOTE: This is a basic text-match search (Phase 3).
    Semantic search using ChromaDB vector similarity is added in Phase 4.
    After Phase 4, this endpoint will be enhanced to use embeddings.

    Example: /products/search?q=gaming+laptop
    """
    results = product_service.search_products_by_name(db, query=q, limit=limit)
    return {"total": len(results), "products": results}


@router.get("/{product_id}", response_model=ProductResponse, summary="Get a single product")
def get_product(
    product_id: str,
    db: Session = Depends(get_db),
):
    """
    Get full details for a single product by its product_id.

    Example: /products/PROD001
    """
    product = product_service.get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=404,
            detail=f"Product '{product_id}' not found."
        )
    return product


@router.post("", response_model=ProductResponse, status_code=201, summary="Add a new product")
def add_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
):
    """
    Add a new product to the catalog.

    After creating, the product should also be indexed in ChromaDB
    (Phase 4) for semantic search. That step will be done separately
    via the /products/{product_id}/index endpoint added in Phase 4.
    """
    # Check for duplicate product_id
    existing = product_service.get_product_by_id(db, data.product_id)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Product with ID '{data.product_id}' already exists."
        )
    product = product_service.create_product(db, data)
    return product
