# ============================================================
# app/ai/recommendation — Personalization Package (Phase 8)
#
# Modules:
#   customer_profile_builder.py  — converts CustomerMemory ORM
#     into a structured profile dict (budget, brands, interests)
#   candidate_generator.py       — generates candidate product pool
#     via ChromaDB semantic search + SQLite interest-based retrieval
#   filters.py                   — removes out-of-stock and recently
#     purchased products from the candidate pool
#   scoring.py                   — 5-factor weighted scoring engine
#     (interest, semantic, budget, frequency, popularity)
#   recommendation_engine.py     — pipeline coordinator; composes
#     the above modules into a single run() function
# ============================================================
