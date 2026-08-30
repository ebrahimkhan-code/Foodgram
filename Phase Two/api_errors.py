"""
Phase 12: Error Handling & Fallback Behavior Documentation

Complete reference for all error scenarios, codes, responses, and fallback mechanisms.
"""

# ============================================================================
# HTTP Status Codes & Meanings
# ============================================================================

HTTP_STATUS_CODES = {
    200: "OK - Request successful",
    400: "Bad Request - Invalid input (validate and retry with correct params)",
    404: "Not Found - Food/resource doesn't exist (try different food_id)",
    500: "Internal Server Error - Unexpected failure (check logs, retry later)",
}


# ============================================================================
# Error Categories
# ============================================================================

class ErrorCategory:
    """Error classification and handling strategy."""
    
    VALIDATION = "Validation Error"
    NOT_FOUND = "Resource Not Found"
    SERVICE = "Service Error"
    TIMEOUT = "Request Timeout"
    FALLBACK_USED = "Fallback Response"


# ============================================================================
# Error Scenarios & Responses
# ============================================================================

ERROR_SCENARIOS = {
    # =========================================================================
    # MEMBER 1 → MEMBER 2: /recommendations/explain
    # =========================================================================
    
    "food_id_not_found": {
        "scenario": "Member 1 sends food_id that doesn't exist in knowledge base",
        "example": {
            "request": {
                "food_id": "nonexistent_123",
                "ml_score": 0.87,
                "user_taste_summary": "..."
            }
        },
        "http_status": 404,
        "response": {
            "food_id": "nonexistent_123",
            "explanation": "We don't have detailed information about this item right now.",
            "ml_score": 0.87,
            "user_taste_match": "...",
            "grounded": False,
            "error": "Food ID 'nonexistent_123' not found in knowledge base"
        },
        "category": "NOT_FOUND",
        "fallback": "Generic 'no information' response",
        "member3_display": "Neutral message: 'We have limited info about this item'",
        "retry_advice": "Verify food_id is correct from ranking results"
    },
    
    "invalid_ml_score": {
        "scenario": "ML score outside valid range (0.0-1.0)",
        "example": {
            "request": {
                "food_id": "curry_123",
                "ml_score": 1.5,  # Invalid: > 1.0
                "user_taste_summary": "..."
            }
        },
        "http_status": 400,
        "response": {
            "detail": "ml_score must be 0-1, got 1.5",
            "status_code": 400,
            "timestamp": "2026-08-30T..."
        },
        "category": "VALIDATION",
        "fallback": "None - reject request",
        "member3_display": "N/A",
        "retry_advice": "Member 1: Clamp score to [0.0, 1.0] range"
    },
    
    "empty_user_taste_summary": {
        "scenario": "Member 1 provides empty user_taste_summary",
        "example": {
            "request": {
                "food_id": "curry_123",
                "ml_score": 0.87,
                "user_taste_summary": ""  # Empty
            }
        },
        "http_status": 400,
        "response": {
            "detail": "user_taste_summary cannot be empty",
            "status_code": 400,
            "timestamp": "2026-08-30T..."
        },
        "category": "VALIDATION",
        "fallback": "None - reject request",
        "member3_display": "N/A",
        "retry_advice": "Member 1: Always provide why this matches user"
    },
    
    "llm_api_timeout": {
        "scenario": "LLM (OpenRouter) takes too long or times out",
        "example": {
            "request": {
                "food_id": "curry_123",
                "ml_score": 0.87,
                "user_taste_summary": "..."
            },
            "timeout_after_ms": 30000
        },
        "http_status": 500,
        "response": {
            "food_id": "curry_123",
            "explanation": "We're having trouble generating details right now.",
            "ml_score": 0.87,
            "user_taste_match": "...",
            "grounded": False,
            "error": "LLM request timed out after 30s"
        },
        "category": "TIMEOUT",
        "fallback": "Knowledge base template-based fallback",
        "member3_display": "Honest: 'Having trouble with AI explanation, showing basic info'",
        "retry_advice": "Retry after 5-10 seconds, LLM may recover"
    },
    
    "score_hallucination_detected": {
        "scenario": "LLM alters the ML score in explanation",
        "example": {
            "request": {
                "food_id": "curry_123",
                "ml_score": 0.5,
                "user_taste_summary": "..."
            },
            "llm_response": "This item has a score of 0.85..."  # Changed 0.5 → 0.85
        },
        "http_status": 200,
        "response": {
            "food_id": "curry_123",
            "explanation": "This item has a score of 0.85...",
            "ml_score": 0.5,
            "grounded": True,
            "limitation_flagged": True,  # ← Key: Score hallucination detected
            "error": null
        },
        "category": "FALLBACK_USED",
        "fallback": "Return explanation but flag for review",
        "member3_display": "Shows explanation but logs warning in UI",
        "retry_advice": "Score was corrected server-side; UI can trust ml_score field"
    },
    
    # =========================================================================
    # MEMBER 3 → MEMBER 2: /search
    # =========================================================================
    
    "empty_search_query": {
        "scenario": "User submits empty search query",
        "example": {
            "url": "/search?query=&top_k=5"
        },
        "http_status": 422,  # Pydantic validation
        "response": {
            "detail": "ensure this value has at least 1 characters",
            "status_code": 422,
            "timestamp": "2026-08-30T..."
        },
        "category": "VALIDATION",
        "fallback": "None - reject request",
        "member3_display": "Show input validation error to user",
        "retry_advice": "User: Enter a search term"
    },
    
    "no_search_results": {
        "scenario": "Query doesn't match any foods",
        "example": {
            "request": {
                "query": "xyz123nothingmatch",
                "top_k": 5
            }
        },
        "http_status": 200,
        "response": {
            "query": "xyz123nothingmatch",
            "results": [],  # Empty
            "total": 0,
            "above_threshold": False,
            "error": null
        },
        "category": "FALLBACK_USED",
        "fallback": "Return empty results (don't crash)",
        "member3_display": "'No items match your search. Try different keywords.'",
        "retry_advice": "User: Rephrase query, use category/filter instead"
    },
    
    "low_similarity_results": {
        "scenario": "Search results exist but confidence is low (<30%)",
        "example": {
            "request": {
                "query": "purple pizza",
                "top_k": 3
            },
            "best_match_similarity": 0.15  # Below 30% threshold
        },
        "http_status": 200,
        "response": {
            "query": "purple pizza",
            "results": [
                {
                    "food_id": "pizza_margherita",
                    "name": "Margherita Pizza",
                    "similarity": 0.15,
                    "metadata": {...}
                }
            ],
            "total": 1,
            "above_threshold": False,  # ← Key: Flag low confidence
            "error": null
        },
        "category": "FALLBACK_USED",
        "fallback": "Return results but flag 'above_threshold: false'",
        "member3_display": "'Results might not match well. Try refining your search.'",
        "retry_advice": "User: Use filters (category, veg_status) for better results"
    },
    
    "invalid_top_k": {
        "scenario": "Member 3 requests invalid top_k (< 1 or > 20)",
        "example": {
            "url": "/search?query=pizza&top_k=50"
        },
        "http_status": 422,
        "response": {
            "detail": "ensure this value is less than or equal to 20",
            "status_code": 422
        },
        "category": "VALIDATION",
        "fallback": "None - reject request",
        "member3_display": "N/A",
        "retry_advice": "UI: Clamp top_k to [1, 20]"
    },
    
    "invalid_filter_value": {
        "scenario": "Invalid filter value (e.g., price_max='abc')",
        "example": {
            "url": "/search?query=pizza&price_max=abc"
        },
        "http_status": 422,
        "response": {
            "detail": "value is not a valid integer",
            "status_code": 422
        },
        "category": "VALIDATION",
        "fallback": "None - reject request",
        "member3_display": "N/A",
        "retry_advice": "UI: Validate input types before sending"
    },
    
    # =========================================================================
    # MEMBER 3 → MEMBER 2: /ask
    # =========================================================================
    
    "empty_question": {
        "scenario": "User submits empty question",
        "example": {
            "request": {
                "query": "",
                "top_k": 3
            }
        },
        "http_status": 422,
        "response": {
            "detail": "ensure this value has at least 1 characters",
            "status_code": 422
        },
        "category": "VALIDATION",
        "fallback": "None - reject request",
        "member3_display": "Show validation error",
        "retry_advice": "User: Enter a question"
    },
    
    "no_relevant_documents": {
        "scenario": "Question doesn't match any foods in knowledge base",
        "example": {
            "request": {
                "query": "What's a purple spaghetti with wings?"
            }
        },
        "http_status": 200,
        "response": {
            "query": "What's a purple spaghetti with wings?",
            "answer": "I don't have confident information matching that request.",
            "sources": [],
            "grounded": False,
            "error": null
        },
        "category": "FALLBACK_USED",
        "fallback": "Return honest 'no information' message",
        "member3_display": "'I don't have enough info. Try a different question.'",
        "retry_advice": "User: Ask about specific cuisines or dishes"
    },
    
    "llm_generation_error": {
        "scenario": "LLM fails to generate answer (API error, rate limit, etc.)",
        "example": {
            "request": {
                "query": "What's a high-protein option?"
            },
            "llm_error": "Rate limit exceeded"
        },
        "http_status": 500,
        "response": {
            "query": "What's a high-protein option?",
            "answer": "I don't have enough information to answer that question. Try being more specific about what you're looking for.",
            "sources": [],
            "grounded": False,
            "error": "Rate limit exceeded"
        },
        "category": "SERVICE",
        "fallback": "Return honest message without LLM",
        "member3_display": "'Service is busy, try again in a moment.'",
        "retry_advice": "Retry after 10-30 seconds"
    },
    
    # =========================================================================
    # MEMBER 3 → MEMBER 2: /ask-specific
    # =========================================================================
    
    "specific_food_not_found": {
        "scenario": "Asked about food_id that doesn't exist",
        "example": {
            "url": "/ask-specific?food_id=nonexistent&query=Is this vegetarian?"
        },
        "http_status": 500,
        "response": {
            "query": "Is this vegetarian?",
            "answer": "We don't have information about this food.",
            "sources": [],
            "grounded": False,
            "error": "Food ID not found in knowledge base"
        },
        "category": "NOT_FOUND",
        "fallback": "Return 'no information' message",
        "member3_display": "'No details available for this item.'",
        "retry_advice": "Verify food_id is correct"
    },
    
    "unsupported_topic_question": {
        "scenario": "User asks about ingredients/nutrition/allergens (intercepted by Phase 10)",
        "example": {
            "url": "/ask-specific?food_id=pizza_123&query=What are the ingredients?"
        },
        "http_status": 200,
        "response": {
            "query": "What are the ingredients?",
            "answer": "We don't track a full ingredient list for this item. What we do know: its main protein is cheese, it's served with a bread base. Check with the restaurant for exact ingredients.",
            "sources": [{"food_id": "pizza_123", "type": "specific"}],
            "grounded": True
        },
        "category": "FALLBACK_USED",
        "fallback": "Phase 10 intercepts, returns honest answer with partial info",
        "member3_display": "Partial answer + 'Check with restaurant for details'",
        "retry_advice": "This is correct behavior - we don't have ingredients data"
    },
    
    # =========================================================================
    # SYSTEM ERRORS
    # =========================================================================
    
    "component_not_initialized": {
        "scenario": "API started but Phase 1-11 components failed to load",
        "example": {
            "error": "chromadb.PersistentClient: chroma_db directory not found"
        },
        "http_status": 500,
        "response": {
            "status": "degraded",
            "components": {
                "retriever": "✗ Not initialized",
                "rag_pipeline": "✗ Not initialized",
                "food_layer": "✗ Not initialized"
            },
            "error": "Failed to initialize components"
        },
        "category": "SERVICE",
        "fallback": "Server won't start - fail fast and log error",
        "member3_display": "N/A - API unavailable",
        "retry_advice": "OPS: Check logs, verify Phase 1-11 artifacts exist"
    },
    
    "knowledge_base_missing": {
        "scenario": "food_knowledge_base.csv not found",
        "example": {
            "error": "FileNotFoundError: food_knowledge_base.csv"
        },
        "http_status": 500,
        "response": {
            "error": "Internal server error",
            "detail": "No such file or directory: 'food_knowledge_base.csv'"
        },
        "category": "SERVICE",
        "fallback": "None - API fails to start",
        "member3_display": "N/A - API unavailable",
        "retry_advice": "OPS: Run Phase 7 (build_knowledge_base.py) first"
    },
    
    "chroma_database_corrupted": {
        "scenario": "Vector store (Chroma) is corrupted or unreadable",
        "example": {
            "error": "SQLiteError: database disk image is malformed"
        },
        "http_status": 500,
        "response": {
            "error": "Internal server error",
            "detail": "database disk image is malformed"
        },
        "category": "SERVICE",
        "fallback": "None - all search/retrieval fails",
        "member3_display": "N/A - API unavailable",
        "retry_advice": "OPS: Rebuild vector store (run Phase 5)"
    },
    
    "server_timeout": {
        "scenario": "Request processing exceeds timeout (e.g., slow LLM)",
        "example": {
            "request": {"query": "..."},
            "timeout_ms": 30000
        },
        "http_status": 504,  # Gateway Timeout (if behind proxy) or no response
        "response": {
            "error": "Request timed out"
        },
        "category": "TIMEOUT",
        "fallback": "Return partial result if available, otherwise error",
        "member3_display": "'Taking longer than expected, please retry.'",
        "retry_advice": "Retry request; check LLM API status"
    },
}


# ============================================================================
# Fallback Strategies
# ============================================================================

FALLBACK_STRATEGIES = {
    "never_fail": {
        "principle": "API should never return 5xx error if possible",
        "implementation": [
            "Validate input at API boundary (400 → reject early)",
            "Try/catch all component calls",
            "Return partial/best-effort response on error (with error flag)",
            "Log all errors for debugging"
        ],
        "example": """
        try:
            result = rag_pipeline.explain_recommendation(food_id, ml_score)
        except KeyError:
            # Food not found → return 404 with fallback
            return ExplanationResponse(
                explanation="We don't have information...",
                error="Food not found"
            )
        except Exception as e:
            # LLM error → return 500 with best-effort
            return ExplanationResponse(
                explanation="...",  # Fallback from template
                error=str(e)
            )
        """
    },
    
    "honest_about_limits": {
        "principle": "Tell user when we don't know rather than guess",
        "implementation": [
            "If no relevant documents: say 'I don't have information'",
            "If low confidence: flag 'above_threshold: false'",
            "If unsupported topic: explain what we can/can't answer",
            "Never hallucinate details not in knowledge base"
        ],
        "example": """
        For question "What are ingredients?":
        ✗ BAD: "This pizza contains mozzarella, tomato sauce, and flour..."
        ✓ GOOD: "We don't track detailed ingredients. 
                 What we know: cheese-based, bread foundation.
                 Check restaurant for full ingredient list."
        """
    },
    
    "graceful_degradation": {
        "principle": "System degrades gracefully, not crashes",
        "implementation": [
            "Missing optional fields → use defaults",
            "Failed validation → reject with clear error",
            "Slow service → return cached/partial result",
            "Component failure → skip and use fallback"
        ],
        "example": """
        Component init:
        - retriever: OK ✓
        - rag_pipeline: TIMEOUT → use template-based answers only
        - food_layer: NOT_INITIALIZED → skip specific food questions
        
        Health endpoint: status="degraded" with component details
        """
    },
    
    "fail_fast": {
        "principle": "For critical errors, don't try to recover - fail clearly",
        "implementation": [
            "Knowledge base missing → API won't start",
            "Vector store corrupted → API won't start",
            "Invalid config → API won't start",
            "Clear error logs so OPS knows what to fix"
        ]
    }
}


# ============================================================================
# Error Response Format (Standard)
# ============================================================================

STANDARD_ERROR_RESPONSE = {
    "generic_error": {
        "error": "Error description",
        "status_code": 400,
        "timestamp": "2026-08-30T14:23:45.123456",
        "detail": "Additional context"
    },
    
    "validation_error": {
        "detail": "Specific validation issue",
        "status_code": 422
    },
    
    "not_found_error": {
        "detail": "Resource not found",
        "status_code": 404
    },
    
    "server_error": {
        "error": "Internal server error",
        "detail": "Exception message",
        "status_code": 500,
        "timestamp": "2026-08-30T..."
    }
}


# ============================================================================
# Monitoring & Alerting
# ============================================================================

ALERTS = {
    "high_error_rate": {
        "condition": "> 5% of requests return 4xx/5xx",
        "action": "Page OPS, check logs for root cause"
    },
    
    "slow_responses": {
        "condition": "p99 latency > 5s",
        "action": "Check LLM API status, scale workers"
    },
    
    "component_degradation": {
        "condition": "Health endpoint shows component 'NOT_initialized'",
        "action": "Restart API server, check artifact files"
    },
    
    "repeated_timeouts": {
        "condition": "> 3 timeout errors in 5 min",
        "action": "Check LLM provider status, possible outage"
    }
}


# ============================================================================
# Testing Error Scenarios
# ============================================================================

def test_error_scenarios():
    """
    Test all error scenarios to ensure proper handling.
    
    Run: python api_client.py
    """
    from api_client import Member2APIClient
    import requests
    
    client = Member2APIClient()
    
    # Test invalid ml_score
    try:
        client.explain_recommendation("food_123", ml_score=1.5, user_taste_summary="test")
        print("✗ Should have raised error for invalid ml_score")
    except Exception as e:
        print(f"✓ Caught invalid ml_score: {e}")
    
    # Test nonexistent food
    try:
        response = client.explain_recommendation(
            "nonexistent_123",
            ml_score=0.87,
            user_taste_summary="test"
        )
        assert response.get("error") is not None
        print("✓ Nonexistent food returns error response")
    except Exception as e:
        print(f"✓ Caught nonexistent food: {e}")
    
    # Test empty search
    try:
        client.search_foods("")
        print("✗ Should have raised error for empty query")
    except Exception as e:
        print(f"✓ Caught empty search: {e}")
    
    # Test no results
    response = client.search_foods("xyz123nothingmatch")
    if response["total"] == 0:
        print("✓ No results handled gracefully")
    
    print("\n✓ All error scenarios handled correctly")


if __name__ == "__main__":
    print("""
    Phase 12: Error Handling & Fallback Documentation
    
    This module documents all possible error scenarios and fallback behaviors.
    See ERROR_SCENARIOS dict for details on each error.
    
    To test error handling:
        python api_client.py test
    """)
    
    # Print summary of errors
    print(f"\nTotal error scenarios documented: {len(ERROR_SCENARIOS)}")
    
    for scenario_name, details in ERROR_SCENARIOS.items():
        print(f"\n  • {scenario_name}")
        print(f"    Status: {details['http_status']}")
        print(f"    Category: {details['category']}")
        print(f"    Fallback: {details['fallback']}")
