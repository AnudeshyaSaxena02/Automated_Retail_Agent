# ============================================================
# app/schemas/product.py
#
# Pydantic models for the Product API.
# These define what data is accepted in requests and returned
# in responses. They are separate from the ORM models.
#
# FLOW:
#   HTTP Request → ProductCreate (validates input)
#   DB Row       → ProductResponse (serializes output)
# ============================================================

import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class ProductCreate(BaseModel):
    """Schema for adding a new product. Used in POST /products."""

    product_id: str = Field(..., example="PROD021", description="Unique product identifier")
    name: str = Field(..., example="Dell XPS 15")
    description: Optional[str] = Field(None, example="High-performance laptop for professionals")
    category: str = Field(..., example="Laptops")
    brand: Optional[str] = Field(None, example="Dell")
    price: float = Field(..., gt=0, example=89999.0, description="Price in INR, must be > 0")
    stock: int = Field(default=100, ge=0, example=50)
    specifications: Optional[Dict[str, Any]] = Field(default={}, example={"RAM": "32GB", "CPU": "i9"})
    tags: Optional[List[str]] = Field(default=[], example=["laptop", "premium", "coding"])


class ProductResponse(BaseModel):
    """Schema for a single product returned in API responses."""

    id: int
    product_id: str
    name: str
    description: Optional[str]
    category: str
    brand: Optional[str]
    price: float
    stock: int
    specifications: Dict[str, Any] = {}
    tags: List[str] = []
    created_at: datetime

    @field_validator("specifications", mode="before")
    @classmethod
    def parse_specs(cls, v):
        """Convert JSON string from DB to dict for the response."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return {}
        return v or {}

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v):
        """Convert JSON string from DB to list for the response."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return []
        return v or []

    model_config = {"from_attributes": True}  # Allows reading from SQLAlchemy ORM objects


class ProductListResponse(BaseModel):
    """Schema for the paginated product list endpoint."""
    total: int
    products: List[ProductResponse]
