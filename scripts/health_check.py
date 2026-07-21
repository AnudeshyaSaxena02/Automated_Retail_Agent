#!/usr/bin/env python
"""
scripts/health_check.py
========================
Validates the entire IDAM stack by hitting core endpoints.

Checks:
  1. GET /          — root alive
  2. GET /health    — DB connection
  3. GET /products  — product catalog accessible
  4. POST /chat/CUST001 — end-to-end AI chat pipeline

Usage:
    python scripts/health_check.py
    python scripts/health_check.py --base-url http://localhost:8001
"""

import sys
import json
import argparse

try:
    import requests
except ImportError:
    print("[health_check] ERROR: 'requests' is not installed.")
    print("  Run: pip install requests")
    sys.exit(1)


def check(label: str, response) -> bool:
    status = response.status_code
    ok = 200 <= status < 300
    symbol = "✓" if ok else "✗"
    print(f"  {symbol} [{status}] {label}")
    if not ok:
        try:
            print(f"      Detail: {response.json()}")
        except Exception:
            print(f"      Body: {response.text[:200]}")
    return ok


def run_health_check(base_url: str):
    base_url = base_url.rstrip("/")
    print(f"\n[health_check] Target: {base_url}\n")

    passed = 0
    total = 4

    # ── 1. Root ───────────────────────────────────────────────
    try:
        r = requests.get(f"{base_url}/", timeout=5)
        if check("GET /  (root alive)", r):
            passed += 1
    except requests.exceptions.ConnectionError:
        print(f"  ✗ Could not connect to {base_url}")
        print("    Is the server running? Start with: uvicorn main:app --reload")
        sys.exit(1)

    # ── 2. Health ─────────────────────────────────────────────
    r = requests.get(f"{base_url}/health", timeout=5)
    if check("GET /health  (DB connection)", r):
        passed += 1

    # ── 3. Product catalog ────────────────────────────────────
    r = requests.get(f"{base_url}/products", timeout=5)
    if check("GET /products  (catalog accessible)", r):
        data = r.json()
        count = len(data) if isinstance(data, list) else data.get("total", "?")
        print(f"      Products in catalog: {count}")
        passed += 1

    # ── 4. End-to-end chat ────────────────────────────────────
    payload = {"message": "Recommend a good laptop for coding under ₹60,000"}
    r = requests.post(
        f"{base_url}/chat/CUST001",
        json=payload,
        timeout=30,
    )
    if check("POST /chat/CUST001  (end-to-end AI pipeline)", r):
        data = r.json()
        print(f"      Intent detected : {data.get('intent')}")
        print(f"      LLM provider    : {data.get('provider')}")
        print(f"      Products in resp: {len(data.get('products', []))}")
        print(f"      Response snippet: {data.get('response', '')[:100]}...")
        passed += 1

    # ── Summary ───────────────────────────────────────────────
    print(f"\n[health_check] Result: {passed}/{total} checks passed.")
    if passed == total:
        print("[health_check] ✓ All systems operational.\n")
        sys.exit(0)
    else:
        print("[health_check] ✗ Some checks failed. See details above.\n")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IDAM stack health check")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL of the running IDAM server (default: http://localhost:8000)",
    )
    args = parser.parse_args()
    run_health_check(args.base_url)
