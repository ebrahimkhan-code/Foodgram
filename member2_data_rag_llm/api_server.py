"""
Phase 12 — API & Integration Server

Exposes the RAG system (Phases 1-11) as REST API endpoints.

Architecture:
  1. Member 1 (Recommendation Engine) → POST /recommendations/explain
     Sends: food_id, ml_score, user_taste_summary
     Receives: explanation, reasoning, context for UI

  2. Member 3 (UI/Frontend) → GET /search, POST /ask
     Sends: query, filters
     Receives: results, explanations, metadata

  3. Phase 2 (RAG Pipeline) → Internal calls
     Uses: HybridRetriever, RAGPipeline, FoodInformationLayer

Error Handling:
  - Graceful fallbacks for missing data
  - Detailed error responses with actionable messages
  - Request validation with clear error codes
  - Logging for debugging

Setup:
    pip install fastapi uvicorn pydantic python-dotenv

Run:
    python api_server.py
    # or
    uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
"""

import os

# Load environment variables from a local .env (OPENROUTER_API_KEY, ports, etc.)
# BEFORE importing the Phase 1-11 components — rag_pipeline reads
# os.environ["OPENROUTER_API_KEY"] at import/construct time, so the .env must be
# loaded first or the LLM client raises "Set OPENROUTER_API_KEY ...".
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv optional; env vars can still be set by the shell

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
import json
import logging
from datetime import datetime

# Import Phase 1-11 components
from retrieval import HybridRetriever
from rag_pipeline import RAGPipeline
from food_info_layer import FoodInformationLayer
from explanation_service import validate_explanation


# ============================================================================
# Setup
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global component instances
retriever = None
rag_pipeline = None
food_layer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize components on startup, cleanup on shutdown."""
    global retriever, rag_pipeline, food_layer
    
    logger.info("🚀 Initializing Phase 12 API Server...")
    try:
        retriever = HybridRetriever()
        rag_pipeline = RAGPipeline()
        food_layer = FoodInformationLayer()
        logger.info("✓ All components initialized successfully")
    except Exception as e:
        logger.error(f"✗ Failed to initialize components: {e}")
        raise
    
    yield
    
    logger.info("🛑 Shutting down API Server")


app = FastAPI(
    title="Food Recommendation RAG API",
    description="Member 2 (Data/RAG/LLM) integration layer for food recommendations",
    version="1.0.0",
    lifespan=lifespan
)

# Allow the Node backend (and, if ever needed, the frontend) to call this
# service directly during development. The Node backend proxies these
# endpoints, so cross-origin isn't strictly required there, but leaving CORS
# open in dev avoids surprises if Member 3 calls /search or /ask from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Request/Response Models
# ============================================================================

class RecommendationRequest(BaseModel):
    """Request from Member 1: recommendation with ML score and user context."""
    food_id: str = Field(..., description="Food ID recommended by Member 1")
    ml_score: float = Field(..., ge=0.0, le=1.0, description="ML model confidence score (0-1)")
    user_taste_summary: str = Field(..., description="User taste/preference summary from Member 1")
    confidence_class: Optional[str] = Field(None, description="Confidence level: high/medium/low")
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional metadata filters")


class ExplanationResponse(BaseModel):
    """Response to Member 3: explanation and context for UI."""
    food_id: str
    explanation: str
    reasoning: Optional[str] = None
    retrieved_document: Optional[str] = None
    ml_score: float
    user_taste_match: str
    grounded: bool = True
    limitation_flagged: bool = False
    error: Optional[str] = None


class SearchRequest(BaseModel):
    """Request for food search/retrieval."""
    query: str = Field(..., description="Search query or question")
    filters: Optional[Dict[str, Any]] = Field(None, description="Metadata filters")
    top_k: int = Field(3, ge=1, le=20, description="Number of results")


class SearchResult(BaseModel):
    """Individual search result."""
    food_id: str
    name: str
    similarity: float
    metadata: Dict[str, Any]


class SearchResponse(BaseModel):
    """Response with search results."""
    query: str
    results: List[SearchResult]
    total: int
    above_threshold: bool = True
    error: Optional[str] = None


class QuestionRequest(BaseModel):
    """Request to ask a food question."""
    query: str = Field(..., description="Food question or request")
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional metadata filters")
    top_k: int = Field(3, ge=1, le=20, description="Number of sources")


class QuestionResponse(BaseModel):
    """Response with answer and sources."""
    query: str
    answer: str
    sources: List[Dict[str, Any]]
    grounded: bool = True
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    components: Dict[str, str]


# ============================================================================
# Health Check & Diagnostics
# ============================================================================

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Check API and component health.
    
    Returns:
        HealthResponse with component status
    """
    components = {
        "retriever": "✓ Ready" if retriever else "✗ Not initialized",
        "rag_pipeline": "✓ Ready" if rag_pipeline else "✗ Not initialized",
        "food_layer": "✓ Ready" if food_layer else "✗ Not initialized",
    }
    
    all_ready = all("✓" in v for v in components.values())
    
    return HealthResponse(
        status="healthy" if all_ready else "degraded",
        timestamp=datetime.now().isoformat(),
        components=components
    )


@app.get("/", tags=["System"])
async def root():
    """API root with basic info."""
    return {
        "name": "Food Recommendation RAG API (Phase 12)",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "recommendations": "/recommendations/explain",
            "search": "/search",
            "ask": "/ask",
        }
    }


# ============================================================================
# Member 1 → Member 2 Endpoint
# Receive recommendation, return explanation
# ============================================================================

@app.post("/recommendations/explain", response_model=ExplanationResponse, tags=["Recommendations"])
async def explain_recommendation(request: RecommendationRequest):
    """
    Member 1 → Member 2: Explain a food recommendation.
    
    Receives:
        - food_id: Recommended food from ML model
        - ml_score: Model confidence (0-1)
        - user_taste_summary: Why this matches user (from Member 1)
        - confidence_class: Optional confidence level
    
    Returns:
        - explanation: Natural language explanation for Member 3 UI
        - retrieved_document: Source knowledge document (for traceability)
        - grounded: Whether explanation is grounded in data
        - error: If something went wrong
    
    Error Handling:
        - Food not found → fallback message + error flag
        - LLM error → returns best-effort explanation
        - Invalid score → validation warning
    """
    try:
        logger.info(f"Explanation request: food_id={request.food_id}, score={request.ml_score}")
        
        # Validate ml_score is reasonable
        if request.ml_score < 0.0 or request.ml_score > 1.0:
            raise ValueError(f"ml_score must be 0-1, got {request.ml_score}")
        
        # Get explanation from RAG pipeline
        result = rag_pipeline.explain_recommendation(
            food_id=request.food_id,
            ml_score=request.ml_score,
            confidence_class=request.confidence_class
        )
        
        explanation = result.get("explanation", "")
        document = result.get("retrieved_document", "")
        
        # Validate explanation doesn't hallucinate the score
        hallucinated_score = validate_explanation(explanation, request.ml_score)
        
        # Build response
        response = ExplanationResponse(
            food_id=request.food_id,
            explanation=explanation,
            reasoning=f"Matched user taste: {request.user_taste_summary}",
            retrieved_document=document[:500] if document else None,  # Truncate for API response
            ml_score=request.ml_score,
            user_taste_match=request.user_taste_summary,
            grounded=True,
            limitation_flagged=hallucinated_score  # Flag if LLM altered score
        )
        
        logger.info(f"✓ Explanation generated for {request.food_id}")
        return response
    
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except KeyError as e:
        logger.error(f"Food not found: {request.food_id}")
        raise HTTPException(
            status_code=404,
            detail=f"Food ID '{request.food_id}' not found in knowledge base"
        )
    
    except Exception as e:
        logger.error(f"Error explaining recommendation: {e}", exc_info=True)
        # Return best-effort response with error flag
        return ExplanationResponse(
            food_id=request.food_id,
            explanation="We don't have detailed information about this item right now.",
            ml_score=request.ml_score,
            user_taste_match=request.user_taste_summary,
            grounded=False,
            error=str(e)
        )


# ============================================================================
# Member 3 → Member 2 Endpoints
# Search and retrieve foods, answer questions
# ============================================================================

@app.get("/search", response_model=SearchResponse, tags=["Search"])
async def search_foods(
    query: str = Query(..., description="Search query"),
    veg_status: Optional[str] = Query(None, description="vegetarian/non_vegetarian"),
    food_type: Optional[str] = Query(None, description="Type of food"),
    category: Optional[str] = Query(None, description="Food category"),
    price_min: Optional[int] = Query(None, description="Minimum price"),
    price_max: Optional[int] = Query(None, description="Maximum price"),
    top_k: int = Query(3, ge=1, le=20, description="Number of results")
):
    """
    Search for foods by query and optional filters.
    
    Query Examples:
        - "spicy vegetarian curry"
        - "low-calorie breakfast"
        - "protein-rich chicken"
    
    Filters (all optional):
        - veg_status: vegetarian, non_vegetarian
        - food_type: snack, main_course, dessert, etc.
        - category: Indian, Chinese, Italian, etc.
        - price_min, price_max: Price range
    
    Returns:
        - results: List of matching foods with similarity scores
        - total: Number of results
        - above_threshold: Whether best match is confident
    
    Error Handling:
        - Invalid query → HTTP 400
        - No results → returns empty results with suggestion
        - Filter error → ignores invalid filters, logs warning
    """
    try:
        logger.info(f"Search request: query='{query}', top_k={top_k}")
        
        # Build filters dict
        filters = {}
        if veg_status:
            filters["veg_status"] = veg_status
        if food_type:
            filters["food_type"] = food_type
        if category:
            filters["category"] = category
        if price_min is not None:
            filters["price_min"] = price_min
        if price_max is not None:
            filters["price_max"] = price_max
        
        # Query retriever
        results = retriever.retrieve(
            query_text=query,
            filters=filters if filters else None,
            top_k=top_k
        )
        
        # Format results
        formatted_results = [
            SearchResult(
                food_id=r["food_id"],
                name=r["name"],
                similarity=r["similarity"],
                metadata=r.get("metadata", {})
            )
            for r in results
        ]
        
        above_threshold = bool(results) and results[0].get("similarity", 0.0) >= 0.30
        
        logger.info(f"✓ Search returned {len(formatted_results)} results")
        
        return SearchResponse(
            query=query,
            results=formatted_results,
            total=len(formatted_results),
            above_threshold=above_threshold
        )
    
    except ValueError as e:
        logger.warning(f"Search validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        return SearchResponse(
            query=query,
            results=[],
            total=0,
            error=str(e)
        )


@app.post("/ask", response_model=QuestionResponse, tags=["Questions"])
async def answer_food_question(request: QuestionRequest):
    """
    Answer a food question using RAG.
    
    Examples:
        - "What's a good high-protein option?"
        - "Find me vegetarian Indian food"
        - "Show me spicy snacks"
    
    The system:
        1. Searches food knowledge base
        2. Retrieves top-k most relevant items
        3. Uses LLM to generate grounded answer
        4. Returns answer + sources for traceability
    
    Error Handling:
        - No relevant results → honest "no information" response
        - Low confidence → response with confidence flag
        - LLM error → fallback response with error message
    """
    try:
        logger.info(f"Question request: '{request.query}'")
        
        # Build filters
        filters = request.filters if request.filters else None
        
        # Get answer from RAG pipeline
        result = rag_pipeline.answer_food_question(
            query_text=request.query,
            filters=filters,
            top_k=request.top_k
        )
        
        answer = result.get("answer", "")
        sources = result.get("sources", [])
        food_ids = result.get("retrieved_food_ids", [])
        
        logger.info(f"✓ Generated answer with {len(sources)} sources")
        
        return QuestionResponse(
            query=request.query,
            answer=answer,
            sources=sources,
            grounded=bool(sources)  # Grounded if we have sources
        )
    
    except Exception as e:
        logger.error(f"Question answering error: {e}", exc_info=True)
        return QuestionResponse(
            query=request.query,
            answer="I don't have enough information to answer that question. Try being more specific about what you're looking for.",
            sources=[],
            grounded=False,
            error=str(e)
        )


# ============================================================================
# Advanced Endpoints
# ============================================================================

@app.post("/ask-specific", response_model=QuestionResponse, tags=["Questions"])
async def ask_specific_food_question(
    food_id: str = Query(..., description="Food ID to ask about"),
    query: str = Query(..., description="Question about the food")
):
    """
    Ask a specific question about a known food.
    
    Used when Member 3 wants detailed info about a specific food_id.
    
    Examples:
        - food_id="x1a2b3", query="Is this vegetarian?"
        - food_id="y4c5d6", query="Tell me more about this dish"
    
    Returns:
        - answer: Grounded in food's knowledge document
        - grounded: Always true if food exists
        - error: If food not found
    """
    try:
        logger.info(f"Specific food question: food_id={food_id}, query='{query}'")
        
        # Use food_layer for specific food queries
        result = food_layer.ask(query_text=query, food_id=food_id)
        
        answer = result.get("answer", "")
        grounded = result.get("grounded", False)
        limitation_flagged = result.get("limitation_flagged", False)
        
        logger.info(f"✓ Answered specific food question for {food_id}")
        
        return QuestionResponse(
            query=query,
            answer=answer,
            sources=[{"food_id": food_id, "type": "specific"}],
            grounded=grounded
        )
    
    except Exception as e:
        logger.error(f"Specific food question error: {e}", exc_info=True)
        return QuestionResponse(
            query=query,
            answer="We don't have information about this food.",
            sources=[],
            grounded=False,
            error=str(e)
        )


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with consistent format."""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail}")
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "timestamp": datetime.now().isoformat()
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return {
        "error": "Internal server error",
        "detail": str(exc),
        "status_code": 500,
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    # Host/port are configurable via env. Default port is 8001 so this service
    # does NOT collide with Member 1's Flask recommender, which runs on 8000.
    host = os.environ.get("MEMBER2_HOST", "127.0.0.1")
    port = int(os.environ.get("MEMBER2_PORT", "8001"))

    print(f"""
    ╔════════════════════════════════════════════════════════════════╗
    ║        Phase 12: API & Integration Server                      ║
    ║        Food Recommendation RAG - REST API                      ║
    ╚════════════════════════════════════════════════════════════════╝

    Starting server on http://{host}:{port}

    📍 API Docs: http://{host}:{port}/docs
    📍 Alternative Docs: http://{host}:{port}/redoc
    📍 Health Check: http://{host}:{port}/health

    Endpoints:
      POST /recommendations/explain  (Member 1 → Member 2)
      GET  /search                   (Member 3 → Member 2)
      POST /ask                      (Member 3 → Member 2)
      POST /ask-specific             (Advanced queries)
    """)

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
