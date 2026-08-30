# Phase 12: API & Integration Layer

## Overview

Phase 12 exposes the RAG system (Phases 1-11) as a production-ready REST API with seamless integration between:
- **Member 1** (Recommendation Engine) → sends recommendations with ML scores
- **Member 2** (Data/RAG/LLM) → this layer, explains recommendations and answers questions  
- **Member 3** (UI/Frontend) → receives explanations, searches, and answers

## Architecture

```
┌─────────────────────┐
│   Member 1          │
│ Recommendation      │─────────┐
│ Engine              │         │
└─────────────────────┘         │
                                │
                        POST /recommendations/explain
                                │
                                ▼
┌─────────────────────────────────────────────────────────┐
│  Phase 12: API Server (FastAPI)                         │
│                                                         │
│  • /recommendations/explain  → Explain recommendations │
│  • /search                   → Search foods            │
│  • /ask                      → Answer questions        │
│  • /ask-specific             → Specific food questions │
│  • /health                   → Health check            │
└─────────────────────────────────────────────────────────┘
         │                    │
         │                    │
    Leverages:            Integrates with:
    • Phase 6: Retriever  • Phase 6: HybridRetriever
    • Phase 8b: RAG       • Phase 8b: RAGPipeline
    • Phase 10: Q&A       • Phase 10: FoodInformationLayer
    • Phase 11: Eval      • Phase 9: Validation
         │                    │
         └────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
┌─────────────────────┐  ┌──────────────────┐
│   Member 3          │  │  Other Systems   │
│   UI/Frontend       │  │  (monitoring,    │
│                     │  │   logging, etc)  │
└─────────────────────┘  └──────────────────┘
```

## Components

### `api_server.py` (Main API Server)
FastAPI application with all endpoints, error handling, and logging.

**Key Features:**
- Lifespan management (startup/shutdown)
- Request validation with Pydantic models
- Comprehensive error handling with fallbacks
- Structured logging for debugging
- OpenAPI documentation (Swagger UI)

**Endpoints:**

| Endpoint | Method | Purpose | From | To |
|----------|--------|---------|------|-----|
| `/recommendations/explain` | POST | Explain recommendation with ML score | Member 1 | Member 3 |
| `/search` | GET | Search foods by query + filters | Member 3 | Member 3 |
| `/ask` | POST | Answer general food question | Member 3 | Member 3 |
| `/ask-specific` | POST | Answer about specific food | Member 3 | Member 3 |
| `/health` | GET | System health check | Any | Any |

### `api_client.py` (Integration Client)
Python client library for Member 1 and Member 3 integration.

**Classes:**
- `Member2APIClient` - Main client with methods for all endpoints

**Usage:**
```python
from api_client import Member2APIClient

client = Member2APIClient()

# Member 1 integration
explanation = client.explain_recommendation(
    food_id="curry_123",
    ml_score=0.87,
    user_taste_summary="You like spicy curries"
)

# Member 3 integration
results = client.search_foods("spicy vegetarian", top_k=5)
answer = client.ask_question("What's high-protein?")
```

## Request/Response Models

### 1. Recommendation Request (Member 1 → Member 2)

**Request:**
```json
{
  "food_id": "butter_chicken_123",
  "ml_score": 0.87,
  "user_taste_summary": "You enjoy creamy, mildly spicy Indian curries",
  "confidence_class": "high",
  "filters": {}
}
```

**Response:**
```json
{
  "food_id": "butter_chicken_123",
  "explanation": "This creamy butter chicken curry combines tender chicken in a rich tomato-based sauce with aromatic spices...",
  "reasoning": "Matched user taste: You enjoy creamy, mildly spicy Indian curries",
  "retrieved_document": "Knowledge base content (first 500 chars)...",
  "ml_score": 0.87,
  "user_taste_match": "You enjoy creamy, mildly spicy Indian curries",
  "grounded": true,
  "limitation_flagged": false,
  "error": null
}
```

### 2. Search Request (Member 3 → Member 2)

**Request:**
```
GET /search?query=spicy+vegetarian&veg_status=vegetarian&category=Indian&price_max=500&top_k=5
```

**Response:**
```json
{
  "query": "spicy vegetarian",
  "results": [
    {
      "food_id": "paneer_tikka_001",
      "name": "Spiced Paneer Tikka",
      "similarity": 0.92,
      "metadata": {"category": "Indian", "price": 350, "veg_status": "vegetarian"}
    },
    ...
  ],
  "total": 5,
  "above_threshold": true,
  "error": null
}
```

### 3. Question Request (Member 3 → Member 2)

**Request:**
```json
{
  "query": "What's a good high-protein vegetarian option?",
  "filters": {"veg_status": "vegetarian"},
  "top_k": 3
}
```

**Response:**
```json
{
  "query": "What's a good high-protein vegetarian option?",
  "answer": "Based on our menu, here are excellent high-protein vegetarian options...",
  "sources": [
    {
      "food_id": "paneer_butter_001",
      "similarity": 0.88,
      "document": "Knowledge base text..."
    },
    ...
  ],
  "grounded": true,
  "error": null
}
```

## Error Handling & Fallbacks

### Graceful Degradation

The API is designed to **never fail silently**. Every error includes:

1. **HTTP Status Code** - Indicates severity
2. **Error Message** - Explains what went wrong
3. **Response Body** - Returns best-effort response when possible

### Error Scenarios

| Scenario | Status | Response | Fallback |
|----------|--------|----------|----------|
| Food not found | 404 | Clear error message | "No information available" |
| Invalid ML score | 400 | Validation error | Reject request |
| No search results | 200 | Empty results array | Friendly "no matches" message |
| LLM timeout | 500 | Error with partial answer | "I don't have information..." |
| Component init fails | 500 | Server won't start, clear error | None (fails fast) |

### Validation

Request validation happens at multiple levels:

1. **Pydantic Models** - Validate JSON structure and types
2. **Value Ranges** - Ensure ml_score ∈ [0, 1], top_k ∈ [1, 20]
3. **Content Checks** - Verify food_id exists, query not empty
4. **Post-Processing** - Validate LLM didn't hallucinate scores

## Setup & Deployment

### Local Development

```bash
# 1. Install dependencies
pip install fastapi uvicorn pydantic python-dotenv

# 2. Ensure Phase 1-11 components exist
# Check: rag_pipeline.py, retrieval.py, food_info_layer.py, etc.

# 3. Start API server
python api_server.py

# 4. In another terminal, test integration
python api_client.py

# 5. Open interactive docs
# Browser: http://localhost:8000/docs
```

### Production Deployment

```bash
# Using Gunicorn + Uvicorn (recommended)
pip install gunicorn

gunicorn api_server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### Environment Variables (Optional)

Create `.env` file:
```
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
KNOWLEDGE_BASE_PATH=food_knowledge_base.csv
CHROMA_DIR=./chroma_db
```

## Integration Guide

### For Member 1 (Recommendation Engine)

1. **Install client:**
   ```python
   from api_client import Member2APIClient
   ```

2. **After ranking foods, explain top recommendation:**
   ```python
   client = Member2APIClient()
   
   # Your ML model picked this food
   food_id = "best_recommendation_123"
   ml_score = 0.87  # Model confidence
   reason = "Matches your taste for spicy curries"
   
   # Get explanation for Member 3 UI
   explanation = client.explain_recommendation(
       food_id=food_id,
       ml_score=ml_score,
       user_taste_summary=reason
   )
   
   # Send to Member 3:
   ui_text = explanation["explanation"]
   ```

3. **Handle errors:**
   ```python
   try:
       response = client.explain_recommendation(...)
   except ValueError as e:
       # Invalid food_id or score
       ui_text = "Sorry, we couldn't explain this recommendation"
   except requests.RequestException as e:
       # API down
       ui_text = "Service temporarily unavailable"
   ```

### For Member 3 (UI/Frontend)

1. **Search for foods:**
   ```python
   client = Member2APIClient()
   
   results = client.search_foods(
       query="spicy vegetarian",
       veg_status="vegetarian",
       top_k=5
   )
   
   for food in results["results"]:
       display_food_card(
           name=food["name"],
           match_score=f"{food['similarity']:.0%}",
           food_id=food["food_id"]
       )
   ```

2. **Answer user questions:**
   ```python
   answer_obj = client.ask_question(
       query=user_input,
       top_k=3
   )
   
   display_answer(answer_obj["answer"])
   display_sources(answer_obj["sources"])
   ```

3. **Get specific food details:**
   ```python
   detail = client.ask_specific_food(
       food_id="selected_food_123",
       query="Is this vegetarian?"
   )
   
   show_answer(detail["answer"])
   ```

## API Documentation

When server is running:

- **Interactive Docs**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc (ReDoc)
- **OpenAPI Spec**: http://localhost:8000/openapi.json

All endpoints include:
- Request/response schemas
- Example values
- Parameter descriptions
- Error codes

## Logging & Monitoring

### Log Levels

```
INFO  - Normal operation, API requests
WARNING - Validation issues, edge cases
ERROR - Exceptions, component failures
```

### Key Log Messages

```
✓ Explanation generated for food_id
✓ Search returned N results
✓ Generated answer with N sources
✗ Food not found: food_id
✗ Search validation error: reason
✗ Unhandled exception: details
```

### Monitoring Queries

```python
# Check API health
response = client.health_check()
if response["status"] != "healthy":
    alert_ops_team()

# Monitor response times
import time
start = time.time()
result = client.search_foods("query")
latency_ms = (time.time() - start) * 1000
```

## Performance Considerations

| Operation | Typical Latency | Bottleneck |
|-----------|-----------------|-----------|
| Search | 100-200ms | Embedding encoding + Chroma query |
| Recommendation explanation | 500-1000ms | LLM API call (OpenRouter) |
| Question answering | 800-1500ms | Retrieval + LLM |
| Health check | <10ms | Memory only |

### Optimization Tips

1. **Batch similar requests** - Combine multiple searches when possible
2. **Cache responses** - For frequently asked questions
3. **Increase workers** - Gunicorn can handle more concurrent requests
4. **Monitor LLM latency** - Slowest component; consider streaming

## Troubleshooting

### "Connection refused" when starting server

```bash
# Check if port 8000 is in use
lsof -i :8000
# Kill existing process
kill -9 <PID>
```

### "Module not found" error

```bash
# Ensure all Phase 1-11 files exist in same directory
ls *.py | grep -E "rag_pipeline|retrieval|food_info"

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"
```

### "Food ID not found" errors

```bash
# Verify knowledge base is built
ls -lh food_knowledge_base.csv

# Check Chroma database
ls -lh chroma_db/
```

### API slow / timeouts

```python
# Test component individually
from rag_pipeline import RAGPipeline
rag = RAGPipeline()

import time
start = time.time()
result = rag.answer_food_question("test query")
print(f"Latency: {time.time() - start:.2f}s")
```

## Security Considerations

### Production Checklist

- [ ] Add authentication (API keys, OAuth)
- [ ] Enable CORS for Member 3 frontend
- [ ] Rate limit requests to prevent abuse
- [ ] Use HTTPS/TLS for encryption
- [ ] Add request/response logging
- [ ] Set up monitoring & alerting
- [ ] Backup knowledge base regularly

### Example CORS Setup

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://member3-ui.example.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Next Steps

Phase 12 completes the Member 2 system. Next:

1. **Member 1 Integration** - Integrate this API with recommendation engine
2. **Member 3 Integration** - Build UI that consumes these endpoints
3. **Monitoring** - Add dashboards for API health and performance
4. **Optimization** - Cache, rate limiting, load testing
5. **Phase 13+** - End-to-end testing and system validation

---

**Phase 12 Status**: ✓ API & Integration Layer Complete
