"""
seed.py — Populates the database with sample products, customers,
orders, memory, and budget history for demo purposes.

Run with: python -m app.database.seed
"""

import json
from datetime import datetime, timedelta
from app.database.connection import init_db, SessionLocal
from app.database.models import (
    Customer, Product, Order, CustomerMemory,
    BudgetHistory, ProductReview
)


# ── Helper ────────────────────────────────────────────────
def jl(lst): return json.dumps(lst)
def jd(dct): return json.dumps(dct)

def week_of_month(dt: datetime) -> int:
    return (dt.day - 1) // 7 + 1


# ── Products ──────────────────────────────────────────────
PRODUCTS = [
    # Laptops
    dict(product_id="PROD001", name="Lenovo IdeaPad Slim 5",
         description="Intel i5 13th Gen, 16GB RAM, 512GB SSD, 15.6\" FHD. Ideal for AI, ML, and coding workloads.",
         category="Laptops", brand="Lenovo", price=58999,
         specifications=jd({"CPU": "Intel i5-13420H", "RAM": "16GB", "Storage": "512GB SSD", "Display": "15.6 FHD"}),
         tags=jl(["laptop", "AI", "machine learning", "coding", "students", "lenovo"])),

    dict(product_id="PROD002", name="ASUS VivoBook 15",
         description="AMD Ryzen 5, 8GB RAM, 512GB SSD. Lightweight everyday laptop for students and professionals.",
         category="Laptops", brand="ASUS", price=45999,
         specifications=jd({"CPU": "AMD Ryzen 5 5600H", "RAM": "8GB", "Storage": "512GB SSD"}),
         tags=jl(["laptop", "budget", "students", "office", "asus"])),

    dict(product_id="PROD003", name="HP Pavilion x360",
         description="2-in-1 convertible laptop, Intel i5, touch display. Great for creative work and presentations.",
         category="Laptops", brand="HP", price=62999,
         specifications=jd({"CPU": "Intel i5-1235U", "RAM": "16GB", "Type": "2-in-1 Touch"}),
         tags=jl(["laptop", "2-in-1", "creative", "touch", "premium", "hp"])),

    dict(product_id="PROD004", name="Acer Aspire 5",
         description="AMD Ryzen 5, 8GB RAM. Best budget laptop with solid performance for everyday computing.",
         category="Laptops", brand="Acer", price=38999,
         specifications=jd({"CPU": "AMD Ryzen 5 5500U", "RAM": "8GB", "Storage": "256GB SSD"}),
         tags=jl(["laptop", "budget", "value", "acer", "students"])),

    # Mobiles
    dict(product_id="PROD005", name="Samsung Galaxy M54 5G",
         description="6.7\" Super AMOLED, 8GB RAM, 5000mAh battery, 5G ready. Best mid-range Android phone.",
         category="Mobiles", brand="Samsung", price=28999,
         specifications=jd({"Display": "6.7 AMOLED", "RAM": "8GB", "Battery": "5000mAh", "Network": "5G"}),
         tags=jl(["smartphone", "samsung", "5G", "android", "mid-range"])),

    dict(product_id="PROD006", name="OnePlus Nord CE 3 5G",
         description="Snapdragon 782G, 8GB RAM, 67W fast charging. Smooth performance for power users.",
         category="Mobiles", brand="OnePlus", price=24999,
         specifications=jd({"Processor": "Snapdragon 782G", "RAM": "8GB", "Charging": "67W"}),
         tags=jl(["smartphone", "oneplus", "5G", "fast-charging", "performance"])),

    dict(product_id="PROD007", name="Realme 12 Pro 5G",
         description="64MP periscope camera, Snapdragon 6 Gen 1. Excellent camera phone under ₹25,000.",
         category="Mobiles", brand="Realme", price=19999,
         specifications=jd({"Camera": "64MP Periscope", "RAM": "8GB", "Processor": "Snapdragon 6 Gen 1"}),
         tags=jl(["smartphone", "camera", "budget", "realme", "5G"])),

    # Accessories
    dict(product_id="PROD008", name="Logitech MX Master 3S",
         description="Wireless ergonomic mouse, 8K DPI, silent clicks. The best productivity mouse available.",
         category="Accessories", brand="Logitech", price=8999,
         specifications=jd({"DPI": "8000", "Connection": "Bluetooth + USB", "Battery": "70 days"}),
         tags=jl(["mouse", "wireless", "productivity", "logitech", "ergonomic"])),

    dict(product_id="PROD009", name="Sony WH-1000XM5",
         description="Industry-leading noise cancellation, 30hr battery, Hi-Res Audio. Premium over-ear headphones.",
         category="Accessories", brand="Sony", price=29990,
         specifications=jd({"ANC": "Industry Leading", "Battery": "30 hours", "Driver": "30mm"}),
         tags=jl(["headphones", "noise-cancelling", "premium", "sony", "wireless"])),

    dict(product_id="PROD010", name="Keychron K2 Pro Mechanical Keyboard",
         description="Compact 75% layout, hot-swappable switches, RGB backlight. Perfect for coders.",
         category="Accessories", brand="Keychron", price=6999,
         specifications=jd({"Layout": "75%", "Switches": "Hot-swappable", "Backlight": "RGB"}),
         tags=jl(["keyboard", "mechanical", "gaming", "coding", "keychron"])),

    dict(product_id="PROD011", name="Anker PowerCore 20000",
         description="20,000mAh power bank, 22.5W fast charge, dual USB-A + USB-C. Never run out of battery.",
         category="Accessories", brand="Anker", price=2999,
         specifications=jd({"Capacity": "20000mAh", "Output": "22.5W", "Ports": "USB-A x2, USB-C x1"}),
         tags=jl(["power-bank", "portable", "accessories", "anker", "travel"])),

    # Wearables
    dict(product_id="PROD012", name="Samsung Galaxy Watch 6",
         description="Advanced health tracking, BioActive sensor, sleep coaching. Premium Android smartwatch.",
         category="Wearables", brand="Samsung", price=24999,
         specifications=jd({"Display": "1.4 AMOLED", "Sensors": "BioActive", "Battery": "40 hours"}),
         tags=jl(["smartwatch", "fitness", "samsung", "wearable", "health"])),

    dict(product_id="PROD013", name="Noise ColorFit Ultra 2",
         description="1.96\" AMOLED display, BT calling, 100+ sports modes. Best budget smartwatch in India.",
         category="Wearables", brand="Noise", price=3499,
         specifications=jd({"Display": "1.96 AMOLED", "Battery": "7 days", "Calling": "Bluetooth"}),
         tags=jl(["smartwatch", "budget", "fitness", "noise", "wearable"])),

    # Fitness
    dict(product_id="PROD014", name="Boldfit Yoga Mat 6mm",
         description="Anti-slip TPE yoga mat, 6mm thick, eco-friendly. Ideal for yoga, stretching, and workouts.",
         category="Fitness", brand="Boldfit", price=999,
         specifications=jd({"Thickness": "6mm", "Material": "TPE", "Size": "183x61cm"}),
         tags=jl(["yoga", "fitness", "mat", "sports", "workout", "budget"])),

    dict(product_id="PROD015", name="Adidas Ultraboost 22 Running Shoes",
         description="Responsive BOOST midsole, Primeknit upper, high energy return. Best running shoes for daily training.",
         category="Fitness", brand="Adidas", price=12999,
         specifications=jd({"Midsole": "BOOST", "Upper": "Primeknit", "Drop": "10mm"}),
         tags=jl(["shoes", "running", "sports", "adidas", "fitness", "premium"])),

    # Daily & Snacks
    dict(product_id="PROD016", name="Cadbury Celebrations Gift Pack",
         description="Assorted premium chocolates gift box, 286g. Perfect for festive gifting.",
         category="Snacks", brand="Cadbury", price=599,
         specifications=jd({"Weight": "286g", "Variants": "Dairy Milk, Bournville, 5 Star"}),
         tags=jl(["snacks", "chocolate", "gift", "festive", "cadbury", "budget"])),

    dict(product_id="PROD017", name="Pilgrim Vitamin C Face Wash",
         description="Brightening face wash with 2% Alpha Arbutin, suitable for all skin types.",
         category="Personal Care", brand="Pilgrim", price=699,
         specifications=jd({"Key Ingredient": "Vitamin C, Alpha Arbutin", "Volume": "100ml"}),
         tags=jl(["skincare", "personal-care", "face-wash", "daily", "budget"])),

    # Stationery
    dict(product_id="PROD018", name="Classmate Premium Notebook Set (5 Pack)",
         description="A4 ruled notebooks, 172 pages each, hard cover. Essential for students.",
         category="Stationery", brand="Classmate", price=299,
         specifications=jd({"Pages": "172 per book", "Size": "A4", "Cover": "Hard"}),
         tags=jl(["notebook", "stationery", "study", "students", "budget"])),

    dict(product_id="PROD019", name="Parker Vector Fountain Pen",
         description="Stainless steel nib, cartridge ink system. Smooth writing experience for professionals.",
         category="Stationery", brand="Parker", price=1499,
         specifications=jd({"Nib": "Stainless Steel", "Ink": "Cartridge", "Body": "Resin"}),
         tags=jl(["pen", "stationery", "fountain-pen", "premium", "gift", "parker"])),

    # Camera
    dict(product_id="PROD020", name="GoPro HERO12 Black",
         description="5.3K60 video, HyperSmooth 6.0 stabilization, waterproof to 10m. Best action camera.",
         category="Cameras", brand="GoPro", price=32999,
         specifications=jd({"Video": "5.3K60", "Stabilization": "HyperSmooth 6.0", "Waterproof": "10m"}),
         tags=jl(["camera", "action", "sports", "vlog", "outdoor", "gopro"])),
]

# ── Sample Reviews ────────────────────────────────────────
REVIEWS = [
    dict(product_id="PROD001", rating=5, reviewer_name="Arjun M.",
         review_text="Excellent laptop for machine learning. Runs PyTorch smoothly. Great build quality from Lenovo. Battery lasts all day."),
    dict(product_id="PROD001", rating=4, reviewer_name="Sneha K.",
         review_text="Perfect for college students doing data science. Fast SSD, adequate RAM. Highly recommend for ML beginners."),
    dict(product_id="PROD002", rating=4, reviewer_name="Rohit T.",
         review_text="Good value for money. Handles MS Office and browsing well. ASUS build quality is reliable."),
    dict(product_id="PROD005", rating=5, reviewer_name="Divya P.",
         review_text="Brilliant AMOLED display and 5G connectivity. Samsung mid-range is getting better each year."),
    dict(product_id="PROD009", rating=5, reviewer_name="Karan S.",
         review_text="Best noise cancelling I have experienced. Completely blocks out office noise. Worth every rupee."),
    dict(product_id="PROD012", rating=4, reviewer_name="Meera R.",
         review_text="Accurate health tracking and good sleep monitoring. Battery lasts about 2 days with AOD on."),
]


# ── Customers ─────────────────────────────────────────────
CUSTOMERS = [
    dict(customer_id="CUST001", name="Rahul Sharma", email="rahul@example.com"),
    dict(customer_id="CUST002", name="Priya Patel",  email="priya@example.com"),
    dict(customer_id="CUST003", name="Amit Kumar",   email="amit@example.com"),
]


# ── Order history per customer ────────────────────────────
# Format: (product_id, price_paid, days_ago)
ORDERS = {
    "CUST001": [
        ("PROD001", 58999, 62),  # Month start (day 1 of 2 months ago)
        ("PROD008", 8999,  52),  # Week 2
        ("PROD010", 6999,  30),  # Last month start
        ("PROD009", 29990,  3),  # This month start
    ],
    "CUST002": [
        ("PROD005", 28999, 55),
        ("PROD012", 24999, 45),
        ("PROD014", 999,   40),
        ("PROD015", 12999,  5),
    ],
    "CUST003": [
        ("PROD011", 2999,  50),
        ("PROD013", 3499,  35),
        ("PROD018", 299,   20),
        ("PROD011", 2999,   6),
    ],
}


# ── Memory config per customer ────────────────────────────
MEMORY = {
    "CUST001": dict(
        purchased_categories=jl(["Laptops", "Accessories"]),
        preferred_brands=jl(["Lenovo", "Logitech", "Keychron", "Sony"]),
        favorite_products=jl(["PROD001", "PROD009"]),
        total_purchases=4, total_spend=104987.0,
        avg_budget_start=44994.5, budget_count_start=2,
        avg_budget_mid=7999.0,    budget_count_mid=2,
        avg_budget_end=0.0,       budget_count_end=0,
        monthly_pattern=jd({"week1": ["Laptops", "Accessories"], "week2": ["Accessories"]}),
        category_interests=jl(["Laptops", "Accessories", "Audio", "Peripherals"]),
        visit_count=6,
    ),
    "CUST002": dict(
        purchased_categories=jl(["Mobiles", "Wearables", "Fitness"]),
        preferred_brands=jl(["Samsung", "Adidas", "Boldfit"]),
        favorite_products=jl(["PROD005", "PROD012"]),
        total_purchases=4, total_spend=67996.0,
        avg_budget_start=26999.0, budget_count_start=2,
        avg_budget_mid=6999.0,    budget_count_mid=2,
        avg_budget_end=0.0,       budget_count_end=0,
        monthly_pattern=jd({"week1": ["Mobiles", "Wearables"], "week2": ["Fitness"]}),
        category_interests=jl(["Mobiles", "Wearables", "Fitness", "Health", "Sports"]),
        visit_count=4,
    ),
    "CUST003": dict(
        purchased_categories=jl(["Accessories", "Wearables", "Stationery"]),
        preferred_brands=jl(["Anker", "Noise", "Classmate"]),
        favorite_products=jl(["PROD011", "PROD013"]),
        total_purchases=4, total_spend=9746.0,
        avg_budget_start=3124.0, budget_count_start=2,
        avg_budget_mid=1874.0,   budget_count_mid=2,
        avg_budget_end=0.0,      budget_count_end=0,
        monthly_pattern=jd({"week1": ["Accessories"], "week3": ["Stationery"]}),
        category_interests=jl(["Accessories", "Wearables", "Stationery", "Budget Gadgets"]),
        visit_count=5,
    ),
}


# ── Seed Function ─────────────────────────────────────────
def seed():
    init_db()
    db = SessionLocal()

    # Check if already seeded
    if db.query(Customer).count() > 0:
        print("[SEED] Database already has data. Skipping seed.")
        db.close()
        return

    print("[SEED] Seeding database...")

    # 1. Products
    product_objs = {}
    for p in PRODUCTS:
        obj = Product(**p)
        db.add(obj)
        product_objs[p["product_id"]] = obj
    db.commit()
    print(f"   [SEED] {len(PRODUCTS)} products inserted")

    # 2. Reviews
    for r in REVIEWS:
        db.add(ProductReview(**r))
    db.commit()
    print(f"   [SEED] {len(REVIEWS)} product reviews inserted")

    # 3. Customers + Orders + Memory + BudgetHistory
    now = datetime.utcnow()

    for c in CUSTOMERS:
        cid = c["customer_id"]
        customer = Customer(**c)
        db.add(customer)
        db.flush()  # flush so FK references work

        # Orders
        for (pid, price, days_ago) in ORDERS[cid]:
            purchase_dt = now - timedelta(days=days_ago)
            db.add(Order(
                customer_id=cid, product_id=pid,
                quantity=1, price_paid=price,
                purchased_at=purchase_dt,
            ))
            db.add(BudgetHistory(
                customer_id=cid, amount=price,
                day_of_month=purchase_dt.day,
                week_of_month=week_of_month(purchase_dt),
                month=purchase_dt.month,
                year=purchase_dt.year,
                purchased_at=purchase_dt,
            ))

        # Memory
        mem_data = MEMORY[cid]
        db.add(CustomerMemory(
            customer_id=cid,
            last_visit=now - timedelta(days=1),
            updated_at=now,
            **mem_data,
        ))

    db.commit()
    print(f"   [SEED] {len(CUSTOMERS)} customers with orders, memory, and budget history inserted")
    db.close()
    print("\n[SEED] Seed complete! Database is ready.")


if __name__ == "__main__":
    seed()
