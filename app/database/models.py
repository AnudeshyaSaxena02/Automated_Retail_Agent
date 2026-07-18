# ============================================================
# IDAM — Intelligent Automated Retail Store Backend
# app/database/models.py
#
# PURPOSE:
#   Defines all 6 database tables as SQLAlchemy ORM classes.
#   Each class = one table in the SQLite database.
#
# TABLES:
#   1. Customer        — Who is shopping
#   2. Product         — What is available to buy
#   3. Order           — What was purchased (one row per item)
#   4. CustomerMemory  — Evolving AI memory per customer (1:1 with Customer)
#   5. BudgetHistory   — Raw spend data per purchase (for budget learning)
#   6. ProductReview   — Reviews used by RAG pipeline
#
# HOW IT CONNECTS:
#   connection.py imports Base from here to run create_all()
#   Services import specific models to query the database
# ============================================================

import json
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime,
    Text, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship

# Base is the parent class all models inherit from.
# SQLAlchemy uses it to track all tables for create_all().
Base = declarative_base()


# ============================================================
# HELPER FUNCTIONS
# These make it easier to store Python lists/dicts as JSON
# in SQLite TEXT columns and read them back automatically.
# ============================================================

def list_to_json(data: list) -> str:
    """Convert a Python list to a JSON string for storage."""
    return json.dumps(data) if data else "[]"


def json_to_list(data: str) -> list:
    """Convert a stored JSON string back to a Python list."""
    if not data:
        return []
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return []


def dict_to_json(data: dict) -> str:
    """Convert a Python dict to a JSON string for storage."""
    return json.dumps(data) if data else "{}"


def json_to_dict(data: str) -> dict:
    """Convert a stored JSON string back to a Python dict."""
    if not data:
        return {}
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return {}


# ============================================================
# TABLE 1: Customer
#
# Stores basic customer identity.
# No authentication — Customer ID is the identifier.
#
# Relationships:
#   - Has many Orders
#   - Has one CustomerMemory
#   - Has many BudgetHistory entries
# ============================================================

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Unique identifier used in API requests — e.g., "CUST001"
    customer_id = Column(String(50), unique=True, nullable=False, index=True)

    name = Column(String(100), nullable=False)
    email = Column(String(150), nullable=True)

    # Timestamp when the customer was created
    created_at = Column(DateTime, default=datetime.utcnow)

    # ----------------------------
    # ORM Relationships
    # These let us do: customer.orders, customer.memory, etc.
    # ----------------------------
    orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan")
    memory = relationship("CustomerMemory", back_populates="customer", uselist=False, cascade="all, delete-orphan")
    budget_history = relationship("BudgetHistory", back_populates="customer", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Customer id={self.customer_id} name={self.name}>"


# ============================================================
# TABLE 2: Product
#
# The product catalog.
# Each product has a structured set of fields plus a flexible
# JSON 'specifications' column for category-specific attributes.
#
# Used for:
#   - Displaying products via REST API
#   - Semantic search (description + tags indexed in ChromaDB)
#   - RAG pipeline (description + specifications fed to LLM)
# ============================================================

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Unique identifier — e.g., "PROD001"
    product_id = Column(String(50), unique=True, nullable=False, index=True)

    name = Column(String(200), nullable=False)

    # Used for semantic search and RAG — describe the product fully
    description = Column(Text, nullable=True)

    category = Column(String(100), nullable=False, index=True)  # "Laptops", "Mobiles", etc.
    brand = Column(String(100), nullable=True)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=100)

    # JSON string: {"RAM": "16GB", "Storage": "512GB SSD", "Display": "15.6 inch"}
    # Flexible — different products have different specs
    specifications = Column(Text, nullable=True, default="{}")

    # JSON list: ["laptop", "AI", "machine learning", "students", "coding"]
    # Used for tag-based filtering and recommendation scoring
    tags = Column(Text, nullable=True, default="[]")

    created_at = Column(DateTime, default=datetime.utcnow)

    # ORM relationships
    order_items = relationship("Order", back_populates="product")
    reviews = relationship("ProductReview", back_populates="product", cascade="all, delete-orphan")

    # ----------------------------
    # Helper properties to access JSON fields as Python objects
    # Usage: product.specs_dict  →  {"RAM": "16GB", ...}
    # ----------------------------
    @property
    def specs_dict(self) -> dict:
        return json_to_dict(self.specifications)

    @property
    def tags_list(self) -> list:
        return json_to_list(self.tags)

    def __repr__(self):
        return f"<Product id={self.product_id} name={self.name} price={self.price}>"


# ============================================================
# TABLE 3: Order
#
# Records every completed purchase.
# One row = one product purchased by one customer.
#
# KEY FIELDS:
#   price_paid    — Actual price at time of purchase (builds budget history)
#   purchased_at  — Timestamp used for:
#                    - Time-of-month budget pattern detection
#                    - Monthly shopping pattern analysis
# ============================================================

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys — link to Customer and Product by their string IDs
    customer_id = Column(String(50), ForeignKey("customers.customer_id"), nullable=False, index=True)
    product_id = Column(String(50), ForeignKey("products.product_id"), nullable=False)

    quantity = Column(Integer, default=1)

    # Price at time of purchase — product price may change later
    price_paid = Column(Float, nullable=False)

    # When the purchase happened — critical for time-of-month analysis
    purchased_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # ORM relationships
    customer = relationship("Customer", back_populates="orders")
    product = relationship("Product", back_populates="order_items")

    def __repr__(self):
        return f"<Order customer={self.customer_id} product={self.product_id} paid={self.price_paid}>"


# ============================================================
# TABLE 4: CustomerMemory
#
# The most important table for the AI assistant.
# One row per customer. Updated automatically after every purchase.
#
# DESIGN DECISIONS:
#   - JSON columns grow over time (interests NEVER shrink — by design)
#   - Three separate budget averages (start/mid/end of month)
#   - monthly_pattern tracks which categories are bought each week
#
# HOW IT UPDATES:
#   When a customer makes a purchase, order_service.py:
#   1. Saves the order
#   2. Saves a BudgetHistory row
#   3. Loads this CustomerMemory row
#   4. Updates all relevant fields
#   5. Saves the updated row
# ============================================================

class CustomerMemory(Base):
    __tablename__ = "customer_memory"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # One memory row per customer
    customer_id = Column(
        String(50),
        ForeignKey("customers.customer_id"),
        unique=True,
        nullable=False,
        index=True
    )

    # ----------------------------
    # Purchase History Summary
    # ----------------------------
    # JSON list: ["Laptops", "Mobiles", "Accessories"]
    purchased_categories = Column(Text, default="[]")

    # JSON list: ["Lenovo", "Samsung", "Sony"]
    preferred_brands = Column(Text, default="[]")

    # JSON list of product_ids the customer has bought
    favorite_products = Column(Text, default="[]")

    total_purchases = Column(Integer, default=0)
    total_spend = Column(Float, default=0.0)

    # ----------------------------
    # Dynamic Budget Learning
    # Three separate averages split by time-of-month.
    #
    # avg_budget_start = average spend when shopping on days 1–10
    # avg_budget_mid   = average spend when shopping on days 11–20
    # avg_budget_end   = average spend when shopping on days 21–31
    #
    # These are running averages updated after each purchase.
    # The memory engine uses today's date to pick the right average.
    # ----------------------------
    avg_budget_start = Column(Float, default=0.0)   # Days 1–10
    avg_budget_mid = Column(Float, default=0.0)     # Days 11–20
    avg_budget_end = Column(Float, default=0.0)     # Days 21–31

    # Count of purchases per period (needed to compute running averages)
    budget_count_start = Column(Integer, default=0)
    budget_count_mid = Column(Integer, default=0)
    budget_count_end = Column(Integer, default=0)

    # ----------------------------
    # Monthly Shopping Pattern
    # Tracks which categories are typically bought each week of the month.
    # JSON dict: {"week1": ["Electronics", "Gadgets"], "week3": ["Snacks"]}
    # ----------------------------
    monthly_pattern = Column(Text, default="{}")

    # ----------------------------
    # Expanding Interest Categories
    # This list ONLY grows — new categories are appended, old ones never removed.
    # This is how the system "discovers" new customer interests over time.
    # JSON list: ["Laptops", "Accessories", "Smartwatches", "Fitness"]
    # ----------------------------
    category_interests = Column(Text, default="[]")

    # ----------------------------
    # Visit Tracking
    # ----------------------------
    visit_count = Column(Integer, default=0)
    last_visit = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ORM relationship
    customer = relationship("Customer", back_populates="memory")

    # ----------------------------
    # Helper properties — get JSON columns as Python objects
    # ----------------------------
    @property
    def purchased_categories_list(self) -> list:
        return json_to_list(self.purchased_categories)

    @property
    def preferred_brands_list(self) -> list:
        return json_to_list(self.preferred_brands)

    @property
    def favorite_products_list(self) -> list:
        return json_to_list(self.favorite_products)

    @property
    def monthly_pattern_dict(self) -> dict:
        return json_to_dict(self.monthly_pattern)

    @property
    def category_interests_list(self) -> list:
        return json_to_list(self.category_interests)

    def __repr__(self):
        return f"<CustomerMemory customer={self.customer_id} purchases={self.total_purchases}>"


# ============================================================
# TABLE 5: BudgetHistory
#
# Raw spend data — one row per purchase.
# Used to compute accurate budget averages in CustomerMemory.
#
# WHY SEPARATE TABLE?
#   CustomerMemory stores running averages (summaries).
#   BudgetHistory stores raw data — useful for:
#   - Recalculating averages from scratch if needed
#   - Detecting seasonal spending trends
#   - Generating analytics/reports
# ============================================================

class BudgetHistory(Base):
    __tablename__ = "budget_history"

    id = Column(Integer, primary_key=True, autoincrement=True)

    customer_id = Column(
        String(50),
        ForeignKey("customers.customer_id"),
        nullable=False,
        index=True
    )

    # How much was spent in this transaction
    amount = Column(Float, nullable=False)

    # Time-of-month metadata — computed from purchased_at
    day_of_month = Column(Integer, nullable=False)    # 1–31
    week_of_month = Column(Integer, nullable=False)   # 1–5
    month = Column(Integer, nullable=False)           # 1–12
    year = Column(Integer, nullable=False)

    # The actual purchase timestamp (linked to the order)
    purchased_at = Column(DateTime, nullable=False)

    # ORM relationship
    customer = relationship("Customer", back_populates="budget_history")

    def __repr__(self):
        return f"<BudgetHistory customer={self.customer_id} amount={self.amount} day={self.day_of_month}>"


# ============================================================
# TABLE 6: ProductReview
#
# Stores customer reviews for products.
# Used ONLY by the RAG pipeline to provide rich product context
# to the LLM when answering product-related questions.
#
# NOT used for customer memory — that comes from Order history.
# ============================================================

class ProductReview(Base):
    __tablename__ = "product_reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)

    product_id = Column(
        String(50),
        ForeignKey("products.product_id"),
        nullable=False,
        index=True
    )

    # The review text — this gets embedded and stored in ChromaDB (Phase 4)
    review_text = Column(Text, nullable=False)

    rating = Column(Integer, nullable=True)  # 1–5 stars

    # Optional: who wrote the review (not linked to Customer table for simplicity)
    reviewer_name = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # ORM relationship
    product = relationship("Product", back_populates="reviews")

    def __repr__(self):
        return f"<ProductReview product={self.product_id} rating={self.rating}>"
