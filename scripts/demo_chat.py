#!/usr/bin/env python
"""
scripts/demo_chat.py
=====================
Runs a curated set of demo queries covering all 8 intents through
the IDAM AI Shopping Assistant and pretty-prints the results.

Useful for:
  - Live demos / presentations
  - Smoke-testing the full chat pipeline
  - Verifying intent routing works end-to-end

Usage:
    python scripts/demo_chat.py
    python scripts/demo_chat.py --base-url http://localhost:8001
    python scripts/demo_chat.py --customer CUST002
"""

import sys
import json
import argparse
import textwrap

try:
    import requests
except ImportError:
    print("[demo_chat] ERROR: 'requests' is not installed.")
    print("  Run: pip install requests")
    sys.exit(1)


# ── ANSI colours (graceful fallback on Windows without VT mode) ──
try:
    import ctypes
    ctypes.windll.kernel32.SetConsoleMode(
        ctypes.windll.kernel32.GetStdHandle(-11), 7
    )
except Exception:
    pass

RESET  = "\033[0m"
BOLD   = "\033[1m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
DIM    = "\033[2m"


# ── Demo scenarios — one per intent ──────────────────────────────
DEMO_QUERIES = [
    {
        "intent_label": "budget_query",
        "customer_id":  "CUST001",
        "message":      "I need a laptop for AI development under ₹60,000",
        "note":         "Should detect budget ₹60,000 and return budget-filtered recommendations",
    },
    {
        "intent_label": "recommendation",
        "customer_id":  "CUST001",
        "message":      "Recommend some accessories for my setup",
        "note":         "Should use CUST001 memory (Lenovo/Sony/Logitech preferences)",
    },
    {
        "intent_label": "product_search",
        "customer_id":  "CUST002",
        "message":      "Show me the best wireless headphones",
        "note":         "Semantic search — should return headphone products",
    },
    {
        "intent_label": "product_details",
        "customer_id":  "CUST001",
        "message":      "Tell me about the Sony WH-1000XM5",
        "note":         "Hybrid lookup — exact or fuzzy match in DB",
    },
    {
        "intent_label": "product_comparison",
        "customer_id":  "CUST001",
        "message":      "Compare Lenovo IdeaPad Slim 5 with HP Pavilion x360",
        "note":         "Should look up both products and compare specs",
    },
    {
        "intent_label": "order_history",
        "customer_id":  "CUST001",
        "message":      "What have I purchased recently?",
        "note":         "Should return CUST001 order history",
    },
    {
        "intent_label": "customer_history",
        "customer_id":  "CUST002",
        "message":      "Tell me about my shopping profile and preferences",
        "note":         "Should load CUST002 memory and summarise interests",
    },
    {
        "intent_label": "general_chat",
        "customer_id":  "CUST003",
        "message":      "What kinds of products do you sell?",
        "note":         "LLM-only response — no service call",
    },
]


def print_separator(char="─", width=70):
    print(DIM + char * width + RESET)


def print_demo_result(idx: int, scenario: dict, result: dict, elapsed: float):
    print_separator()
    print(
        f"{BOLD}{CYAN}[{idx}] {scenario['intent_label'].upper()}{RESET}  "
        f"{DIM}({scenario['customer_id']}){RESET}"
    )
    print(f"  {BOLD}Query  :{RESET} {scenario['message']}")
    print(f"  {DIM}Note   : {scenario['note']}{RESET}")
    print()

    detected = result.get("intent", "?")
    provider = result.get("provider", "?")
    products = result.get("products", [])
    response = result.get("response", "")
    metadata = result.get("metadata", {})

    match_colour = GREEN if detected == scenario["intent_label"] else YELLOW
    print(f"  {BOLD}Detected Intent :{RESET} {match_colour}{detected}{RESET}")
    print(f"  {BOLD}LLM Provider    :{RESET} {provider}")
    print(f"  {BOLD}Products        :{RESET} {len(products)}")
    print(f"  {BOLD}Elapsed         :{RESET} {elapsed:.2f}s")

    if metadata.get("budget_detected"):
        print(f"  {BOLD}Budget Detected :{RESET} ₹{metadata['budget_detected']:,.0f}")

    print()
    print(f"  {BOLD}Response:{RESET}")
    wrapped = textwrap.fill(response, width=66, initial_indent="    ", subsequent_indent="    ")
    print(wrapped)

    if products:
        print()
        print(f"  {BOLD}Top products:{RESET}")
        for p in products[:3]:
            score = p.get("final_score") or p.get("similarity_score")
            score_str = f"  score={score:.2f}" if score is not None else ""
            print(f"    • {p['name']}  ₹{p['price']:,.0f}{score_str}")


def run_demo(base_url: str, customer_override: str = None, timeout: int = 30):
    base_url = base_url.rstrip("/")

    print(f"\n{BOLD}{'=' * 70}{RESET}")
    print(f"{BOLD}  IDAM AI Shopping Assistant — Demo Chat Runner{RESET}")
    print(f"{BOLD}{'=' * 70}{RESET}")
    print(f"  Server  : {base_url}")
    print(f"  Queries : {len(DEMO_QUERIES)} (one per intent)")
    print(f"{BOLD}{'=' * 70}{RESET}\n")

    # Verify server is up
    try:
        r = requests.get(f"{base_url}/health", timeout=5)
        r.raise_for_status()
    except requests.exceptions.ConnectionError:
        print(f"{RED}✗ Cannot reach {base_url}{RESET}")
        print("  Start the server: uvicorn main:app --reload")
        sys.exit(1)
    except Exception as exc:
        print(f"{RED}✗ Server health check failed: {exc}{RESET}")
        sys.exit(1)

    import time
    results_summary = []

    for idx, scenario in enumerate(DEMO_QUERIES, start=1):
        cid = customer_override or scenario["customer_id"]
        payload = {"message": scenario["message"]}

        try:
            t0 = time.time()
            r = requests.post(
                f"{base_url}/chat/{cid}",
                json=payload,
                timeout=timeout,
            )
            elapsed = time.time() - t0

            if r.status_code == 200:
                result = r.json()
                print_demo_result(idx, scenario, result, elapsed)
                results_summary.append({
                    "idx": idx,
                    "expected": scenario["intent_label"],
                    "detected": result.get("intent"),
                    "ok": True,
                    "elapsed": elapsed,
                })
            else:
                print_separator()
                print(f"{RED}[{idx}] {scenario['intent_label']} — HTTP {r.status_code}{RESET}")
                try:
                    print(f"  {r.json()}")
                except Exception:
                    print(f"  {r.text[:200]}")
                results_summary.append({
                    "idx": idx,
                    "expected": scenario["intent_label"],
                    "detected": None,
                    "ok": False,
                    "elapsed": time.time() - t0,
                })

        except requests.exceptions.Timeout:
            print(f"{RED}[{idx}] {scenario['intent_label']} — TIMEOUT after {timeout}s{RESET}")
            results_summary.append({"idx": idx, "ok": False, "elapsed": timeout})
        except Exception as exc:
            print(f"{RED}[{idx}] {scenario['intent_label']} — ERROR: {exc}{RESET}")
            results_summary.append({"idx": idx, "ok": False, "elapsed": 0})

    # ── Final summary ─────────────────────────────────────────
    print_separator("═")
    total = len(results_summary)
    passed = sum(1 for r in results_summary if r["ok"])
    correct_intents = sum(
        1 for r in results_summary
        if r.get("detected") and r.get("expected") and r["detected"] == r["expected"]
    )
    avg_time = sum(r["elapsed"] for r in results_summary) / total if total else 0

    print(f"\n{BOLD}  Demo Summary{RESET}")
    print(f"  Queries run     : {total}")
    print(f"  Successful (2xx): {passed}/{total}")
    print(f"  Correct intents : {correct_intents}/{total}")
    print(f"  Avg response    : {avg_time:.2f}s")

    if passed == total:
        print(f"\n  {GREEN}{BOLD}✓ All demo queries completed successfully.{RESET}\n")
    else:
        print(f"\n  {YELLOW}⚠  {total - passed} query(ies) failed. See details above.{RESET}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IDAM demo chat runner")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL of the running IDAM server (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--customer",
        default=None,
        help="Override customer ID for all queries (default: per-scenario)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Request timeout in seconds (default: 30)",
    )
    args = parser.parse_args()
    run_demo(base_url=args.base_url, customer_override=args.customer, timeout=args.timeout)
