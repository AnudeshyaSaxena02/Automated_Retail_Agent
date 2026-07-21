# IDAM — Intelligent Automated Retail Store Backend

An AI-powered retail backend built with **FastAPI**, **SQLite**, **ChromaDB**, and **Groq / Gemini LLMs**.

IDAM delivers a conversational AI shopping assistant with customer memory, dynamic budget learning, and a multi-factor personalised recommendation engine — all via a clean REST API.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [Demo Personas](#demo-personas)
- [Utility Scripts](#utility-scripts)
- [Development Notes](#development-notes)

---

## Quick Start

### Prerequisites

- Python 3.10+
- A free [Groq API key](https://console.groq.com) (primary LLM — instant, no credit card)
- Optionally, a free [Gemini API key](https://aistudio.google.com) (automatic fallback)

### 1. Clone and install

```bash
git clone <repo-url>
cd idam
pip install -r requirements.txt
```

### 2. Configure environment

```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

Open `.env` and set your API keys:

```env
GROQ_API_KEY=gsk_your_key_here
GEMINI_API_KEY=your_gemini_key_here   # Optional — used as fallback
```

### 3. Seed the database

```bash
python -m app.database.seed
```

### 4. Start the server

```bash
uvicorn main:app --reload
```

The server starts at **http://localhost:8000**  
Interactive API docs: **http://localhost:8000/docs**

### 5. Test the chat endpoint

```bash
curl -X POST http://localhost:8000/chat/CUST001 \
  -H "Content-Type: application/json" \
  -d '{"message": "I need a laptop for AI under ₹60,000"}'
```

---

## Architecture Overview

```
User message
     │
     ▼
POST /chat/{customer_id}          ← app/api/chat.py (thin HTTP layer)
     │
     ▼
handle_chat()                     ← app/services/chat_service.py
     │
     ├─ 1. Validate customer      ← SQLite via customer_service
     ├─ 2. Detect intent          ← app/ai/intent/intent_detector.py  (rule-based, no LLM)
     ├─ 3. Load customer memory   ← app/ai/memory/memory_engine.py
     ├─ 4. Route to pipeline      ← app/ai/intent/router.py
     │       ├─ product_search    → search_service → ChromaDB semantic search
     │       ├─ product_details   → hybrid lookup (exact → fuzzy → semantic)
     │       ├─ recommendation    → recommendation_engine (5-factor scoring)
     │       ├─ product_comparison→ hybrid lookup × 2 products
     │       ├─ customer_history  → memory_engine + order history
     │       ├─ order_history     → order history
     │       ├─ budget_query      → recommendation_engine (budget-filtered)
     │       └─ general_chat      → LLM only
     ├─ 5. Build prompt           ← app/ai/prompts/prompt_builder.py
     └─ 6. Call LLM               ← app/ai/llm/llm_client.py
               ├─ Groq (primary)
               └─ Gemini (automatic fallback)
```

### Key Design Decisions

| Decision | Rationale |
|---|---|
| Rule-based intent detection | Deterministic, zero latency, no LLM cost |
| Stateless single-turn chat | Customer memory loaded fresh per request — no session state |
| Groq + Gemini with fallback | Free tier, high availability, automatic provider switching |
| SQLite + ChromaDB | Zero infrastructure — runs locally with no external services |
| Memory grows, never shrinks | Customer interests accumulate over time for better personalisation |

---

## Project Structure

```
idam/
├── main.py                         # FastAPI app entry point, lifespan, router registration
├── requirements.txt
├── .env.example                    # Environment variable template
│
├── app/
│   ├── api/                        # HTTP route handlers (thin layer — no business logic)
│   │   ├── chat.py                 # POST /chat/{customer_id}  ← Phase 9
│   │   ├── recommendations.py      # POST /recommendations     ← Phase 8
│   │   ├── search.py               # POST /search              ← Phase 5
│   │   ├── llm.py                  # POST /llm/query           ← Phase 6
│   │   ├── orders.py               # POST /orders              ← Phase 4
│   │   ├── products.py             # GET/POST /products        ← Phase 3
│   │   └── customers.py            # GET/POST /customers       ← Phase 3
│   │
│   ├── services/                   # Business logic layer
│   │   ├── chat_service.py         # Chat orchestration pipeline
│   │   ├── recommendation_service.py
│   │   ├── search_service.py
│   │   ├── customer_service.py
│   │   ├── order_service.py        # Also updates customer memory on purchase
│   │   ├── product_service.py
│   │   └── llm_service.py
│   │
│   ├── ai/                         # AI/ML modules
│   │   ├── intent/
│   │   │   ├── intent_detector.py  # Rule-based 8-intent classifier
│   │   │   └── router.py           # Dispatches intents to service pipelines
│   │   ├── memory/
│   │   │   └── memory_engine.py    # Customer memory read/write + budget projection
│   │   ├── recommendation/
│   │   │   ├── recommendation_engine.py
│   │   │   ├── candidate_generator.py
│   │   │   ├── scoring.py          # 5-factor weighted scoring
│   │   │   ├── filters.py
│   │   │   └── customer_profile_builder.py
│   │   ├── rag/
│   │   │   └── rag_context_builder.py
│   │   ├── prompts/
│   │   │   └── prompt_builder.py   # All LLM prompt templates
│   │   ├── embeddings/             # Sentence-transformer embedding pipeline
│   │   ├── vectordb/               # ChromaDB client + product indexing
│   │   └── llm/
│   │       ├── llm_client.py       # complete_with_fallback() — main entry point
│   │       ├── groq_client.py
│   │       ├── gemini_client.py
│   │       └── exceptions.py
│   │
│   ├── database/
│   │   ├── models.py               # 6 SQLAlchemy ORM tables
│   │   ├── connection.py           # SQLite engine + session factory
│   │   └── seed.py                 # Demo data (5 customers, 25 products)
│   │
│   ├── schemas/                    # Pydantic request/response models
│   │   ├── chat.py                 # ChatRequest, ChatResponse, ChatProductItem
│   │   ├── recommendation.py
│   │   ├── search.py
│   │   └── ...
│   │
│   └── config/
│       └── settings.py             # Pydantic BaseSettings — all config from .env
│
├── data/
│   ├── idam.db                     # SQLite database (auto-created)
│   └── chroma_db/                  # ChromaDB vector store (auto-created)
│
└── scripts/
    ├── reset_and_seed.py           # Drop + re-seed + re-index (demo reset)
    ├── health_check.py             # Validate full stack (4 checks)
    └── demo_chat.py                # Run all 8 intent scenarios end-to-end
```

---

## Environment Variables

All variables have sensible defaults. Only API keys are required.

| Variable | Default | Description |
|---|---|---|
| `APP_NAME` | `IDAM Retail Store Backend` | Application display name |
| `APP_VERSION` | `1.0.0` | API version |
| `DEBUG` | `True` | Enable debug logging |
| `DATABASE_URL` | `sqlite:///./data/idam.db` | SQLite database path |
| `LLM_PROVIDER` | `groq` | Primary LLM: `groq` or `gemini` |
| `LLM_TIMEOUT` | `30` | LLM request timeout in seconds |
| `GROQ_API_KEY` | — | **Required.** [Get free key](https://console.groq.com) |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Groq model to use |
| `GEMINI_API_KEY` | — | Optional fallback. [Get free key](https://aistudio.google.com) |
| `GEMINI_MODEL` | `gemini-1.5-flash` | Gemini model to use |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | HuggingFace sentence-transformer model |
| `CHROMA_DB_PATH` | `./data/chroma_db` | ChromaDB persistence directory |
| `SIMILARITY_THRESHOLD` | `0.3` | Minimum cosine similarity for search results (0.0–1.0) |
| `RAG_TOP_K` | `5` | Products retrieved per RAG query |
| `RECOMMENDATION_TOP_K` | `10` | Products returned by recommendation engine |
| `RECOMMENDATION_RECENCY_DAYS` | `30` | Days to exclude recently purchased products |

---

## API Reference

### Health

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Root — confirms server is running |
| `GET` | `/health` | Health check — confirms DB connection |

### Products

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/products` | List all products (with optional filters) |
| `GET` | `/products/{product_id}` | Get a single product |
| `POST` | `/products` | Create a new product |

### Customers

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/customers` | List all customers |
| `GET` | `/customers/{customer_id}` | Get customer + memory profile |
| `POST` | `/customers` | Create a new customer |

### Orders

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/orders` | Record a purchase (triggers memory update) |
| `GET` | `/orders/{customer_id}` | Get order history for a customer |

### Semantic Search

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/search` | Semantic product search via ChromaDB |
| `POST` | `/search/index` | Re-index all products into ChromaDB |

### LLM

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/llm/query` | Direct LLM query (Phase 6, no RAG) |
| `POST` | `/llm/rag` | RAG-enriched LLM query with product context |

### Recommendations

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/recommendations` | Get personalised recommendations for a customer |

### AI Chat Assistant ← Phase 9

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/chat/{customer_id}` | **Main endpoint.** Single-turn AI Shopping Assistant |

#### `POST /chat/{customer_id}` — Request

```json
{
  "message": "I need a laptop for AI development under ₹60,000"
}
```

#### `POST /chat/{customer_id}` — Response

```json
{
  "customer_id": "CUST001",
  "intent":      "budget_query",
  "provider":    "groq",
  "response":    "Based on your ₹60,000 budget and preference for Lenovo...",
  "products": [
    {
      "product_id":  "PROD001",
      "name":        "Lenovo IdeaPad Slim 5",
      "category":    "Laptops",
      "brand":       "Lenovo",
      "price":       58999.0,
      "stock":       100,
      "final_score": 0.87,
      "reason":      "Matches preferred brand (Lenovo) and budget."
    }
  ],
  "metadata": {
    "budget_detected":   60000.0,
    "intent_confidence": 1.0,
    "total_products":    5
  }
}
```

#### Detected Intents

| Intent | Example Trigger |
|---|---|
| `budget_query` | `"I have ₹60,000"`, `"under ₹60k"` |
| `recommendation` | `"Recommend something for me"` |
| `product_search` | `"Show me the best laptops"` |
| `product_details` | `"Tell me about Sony WH-1000XM5"` |
| `product_comparison` | `"Compare Lenovo IdeaPad vs HP Pavilion"` |
| `order_history` | `"What have I purchased recently?"` |
| `customer_history` | `"Tell me my shopping profile"` |
| `general_chat` | `"What do you sell?"` |

---

## Demo Personas

The seed data includes 5 customers with distinct shopping profiles:

| Customer ID | Name | Profile |
|---|---|---|
| `CUST001` | Rahul Sharma | Tech-heavy: Laptops, Accessories, Audio (Lenovo, Sony) |
| `CUST002` | Priya Patel | Mobile & Fitness (Samsung, Adidas) |
| `CUST003` | Amit Kumar | Budget gadgets & Stationery (Anker, Noise) |
| `CUST004` | Neha Singh | Gaming & Home-Office (Razer, SteelSeries, BenQ) |
| `CUST005` | Vikram Reddy | Premium Audio & Wearables (Sony, JBL, Samsung) |

---

## Utility Scripts

### Reset and re-seed

Drops all data and starts fresh — useful before a demo:

```bash
python scripts/reset_and_seed.py        # with confirmation prompt
python scripts/reset_and_seed.py --yes  # skip confirmation
```

### Health check

Validates the full stack (root, DB, catalog, chat pipeline):

```bash
python scripts/health_check.py
python scripts/health_check.py --base-url http://localhost:8001
```

### Demo chat runner

Runs all 8 intent scenarios through the live API:

```bash
python scripts/demo_chat.py
python scripts/demo_chat.py --customer CUST004
python scripts/demo_chat.py --base-url http://localhost:8001 --timeout 60
```

---

## Development Notes

### Adding a new product

1. Add to `PRODUCTS` list in `app/database/seed.py`
2. Run `python scripts/reset_and_seed.py --yes` to rebuild
3. Or POST directly to `/products` and then POST to `/search/index`

### Adding a new intent

1. Add enum value to `ChatIntent` in `app/ai/intent/intent_detector.py`
2. Add trigger keywords to `detect_intent()`
3. Add a handler in `app/ai/intent/router.py`
4. Add a prompt instruction in `_CHAT_INTENT_INSTRUCTIONS` in `app/ai/prompts/prompt_builder.py`

### Changing the LLM model

Update `GROQ_MODEL` or `GEMINI_MODEL` in `.env`. No code changes needed.

### Re-indexing ChromaDB

If you add products without restarting the server:

```bash
curl -X POST http://localhost:8000/search/index
```
