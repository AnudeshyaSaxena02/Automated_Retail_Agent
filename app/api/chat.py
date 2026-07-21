# ============================================================
# IDAM — Intelligent Automated Retail Store Backend
# app/api/chat.py
#
# PURPOSE:
#   FastAPI router for the Phase 9 AI Shopping Assistant.
#   Intentionally thin — HTTP concerns only.
#   All business logic lives in chat_service.py.
#
# ENDPOINT:
#   POST /chat/{customer_id}
#     — Single-turn conversational AI endpoint.
#       Detects intent, routes to the appropriate services,
#       and returns a grounded LLM response.
# ============================================================

import logging

from fastapi import APIRouter, Body, Depends, Path
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import handle_chat

logger = logging.getLogger(__name__)

router = APIRouter()


# ── POST /chat/{customer_id} ──────────────────────────────────

@router.post(
    "/{customer_id}",
    response_model=ChatResponse,
    summary="AI Shopping Assistant — conversational product chat",
    description=(
        "The single-turn AI Shopping Assistant endpoint. "
        "Send a natural-language message and receive a personalised, "
        "grounded LLM response.\n\n"
        "**How it works internally:**\n"
        "1. **Intent Detection** — classifies your message into one of 8 intents\n"
        "2. **Memory Loading** — loads customer purchase history and budget profile\n"
        "3. **Service Routing** — calls the correct pipeline based on intent:\n"
        "   - `product_search` → ChromaDB semantic search\n"
        "   - `product_details` → hybrid product lookup (exact → fuzzy → semantic)\n"
        "   - `recommendation` → Phase 8 recommendation engine (5-factor scoring)\n"
        "   - `product_comparison` → hybrid lookup × 2 products\n"
        "   - `customer_history` → customer memory + order history\n"
        "   - `order_history` → purchase history summary\n"
        "   - `budget_query` → budget-filtered recommendations\n"
        "   - `general_chat` → LLM-only response\n"
        "4. **LLM Response** — Groq (primary) with automatic Gemini fallback\n\n"
        "**Single-turn design:** Each call is independent. Customer memory "
        "(purchases, budget, interests) is always loaded fresh from the database, "
        "giving the LLM full context without persisting conversation history.\n\n"
        "**Budget formats supported:** `₹60,000`, `60k`, `60K`, `Rs. 60000`, "
        "`under 60k`, `below ₹60,000`, etc."
    ),
    responses={
        200: {
            "description": "AI response generated successfully",
            "model": ChatResponse,
        },
        401: {
            "description": "LLM API key invalid",
            "content": {
                "application/json": {
                    "example": {"detail": "LLM authentication failed."}
                }
            },
        },
        502: {
            "description": "LLM provider unavailable",
            "content": {
                "application/json": {
                    "example": {"detail": "Could not reach the LLM provider."}
                }
            },
        },
        504: {
            "description": "LLM request timed out",
        },
    },
)
def chat_with_assistant(
    customer_id: str = Path(
        ...,
        description="Customer's unique identifier (e.g. 'CUST001')",
        example="CUST001",
    ),
    request: ChatRequest = Body(..., description="Chat message body"),
    db: Session = Depends(get_db),
):
    """
    Send a natural-language message to the AI Shopping Assistant.

    **Example messages and what they trigger:**

    | Message | Detected Intent | Pipeline |
    |---|---|---|
    | `"I need a laptop for AI under ₹60,000"` | `budget_query` | Recommendation engine |
    | `"What have I purchased recently?"` | `order_history` | Order history |
    | `"Compare Lenovo IdeaPad Slim 5 with HP Pavilion"` | `product_comparison` | Hybrid product lookup |
    | `"Recommend accessories for my setup"` | `recommendation` | Recommendation engine |
    | `"I have ₹10,000"` | `budget_query` | Budget-filtered recommendations |
    | `"Tell me about the Sony WH-1000XM5"` | `product_details` | Hybrid product lookup |
    | `"Show me the best laptops"` | `product_search` | Semantic search |
    | `"What do you sell?"` | `general_chat` | LLM only |

    **Response fields:**
    - `intent` — Detected intent label (for transparency)
    - `provider` — LLM that served the response (`groq` or `gemini`)
    - `response` — The LLM's conversational answer
    - `products` — Product list (empty for history/general intents)
    - `metadata` — Budget detected, intent confidence, total products
    """
    logger.info(
        f"[Chat API] POST /chat/{customer_id} | "
        f"Message: '{request.message[:60]}'"
        + ("..." if len(request.message) > 60 else "")
    )

    return handle_chat(
        db          = db,
        customer_id = customer_id,
        message     = request.message,
    )
