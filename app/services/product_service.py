# ============================================================
# app/services/product_service.py
#
# PURPOSE:
#   Business logic for products. All DB queries for products
#   live here. API routes call these functions — they never
#   query the DB directly.
#
# FUNCTIONS:
#   get_all_products()       — List products with optional filters
#   get_product_by_id()      — Fetch one product
#   create_product()         — Add a new product
#   search_products_by_name()— Simple keyword search (Phase 3)
#                              Semantic search comes in Phase 4
# ============================================================

import json
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database.models import Product
from app.schemas.product import ProductCreate


def get_all_products(
    db: Session,
    category: Optional[str] = None,
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[List[Product], int]:
    """
    Return a filtered list of products and the total count.

    Args:
        category  : Filter by category name (case-insensitive)
        brand     : Filter by brand name (case-insensitive)
        min_price : Minimum price filter
        max_price : Maximum price filter
        limit     : Max results to return (pagination)
        offset    : Number of results to skip (pagination)

    Returns:
        (list of Product ORM objects, total count before pagination)
    """
    query = db.query(Product)

    if category:
        query = query.filter(Product.category.ilike(f"%{category}%"))
    if brand:
        query = query.filter(Product.brand.ilike(f"%{brand}%"))
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    total = query.count()
    products = query.order_by(Product.id).offset(offset).limit(limit).all()
    return products, total


def get_product_by_id(db: Session, product_id: str) -> Optional[Product]:
    """
    Fetch a single product by its string product_id (e.g. 'PROD001').
    Returns None if not found.
    """
    return db.query(Product).filter(Product.product_id == product_id).first()


def create_product(db: Session, data: ProductCreate) -> Product:
    """
    Add a new product to the catalog.
    Converts specifications (dict) and tags (list) to JSON strings for storage.
    """
    product = Product(
        product_id=data.product_id,
        name=data.name,
        description=data.description,
        category=data.category,
        brand=data.brand,
        price=data.price,
        stock=data.stock,
        specifications=json.dumps(data.specifications or {}),
        tags=json.dumps(data.tags or []),
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def search_products_by_name(
    db: Session,
    query: str,
    limit: int = 20
) -> List[Product]:
    """
    Simple keyword search on product name, description, and category.
    This is a basic text match — semantic search with ChromaDB is added in Phase 4.

    Searches across: name, description, category, brand
    """
    pattern = f"%{query}%"
    results = (
        db.query(Product)
        .filter(
            or_(
                Product.name.ilike(pattern),
                Product.description.ilike(pattern),
                Product.category.ilike(pattern),
                Product.brand.ilike(pattern),
            )
        )
        .limit(limit)
        .all()
    )
    return results


def get_products_by_category(db: Session, category: str) -> List[Product]:
    """
    Return all products in a specific category.
    Used by the recommendation engine (Phase 8) to find similar products.
    """
    return (
        db.query(Product)
        .filter(Product.category.ilike(f"%{category}%"))
        .all()
    )


def get_products_by_ids(db: Session, product_ids: List[str]) -> List[Product]:
    """
    Fetch multiple products by their product_id list.
    Used by the recommendation engine to hydrate product details
    after ChromaDB returns matching product_ids.
    """
    return (
        db.query(Product)
        .filter(Product.product_id.in_(product_ids))
        .all()
    )
