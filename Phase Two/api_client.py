"""
Phase 12: API Integration Guide

How to integrate with Member 1 (Recommendation Engine) and Member 3 (UI).
"""

import requests
import json
from typing import Dict, Any, Optional


class Member2APIClient:
    """
    Client for integrating with Phase 12 API.
    Used by Member 1 and Member 3.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize API client.
        
        Args:
            base_url: API server URL (default: localhost:8000)
        """
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
    
    # =========================================================================
    # Member 1 Integration: Send recommendations, get explanations
    # =========================================================================
    
    def explain_recommendation(
        self,
        food_id: str,
        ml_score: float,
        user_taste_summary: str,
        confidence_class: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a recommendation from Member 1 to Member 2.
        
        Member 1 (Recommendation Engine):
            1. Runs ML model to rank foods
            2. Selects top recommendation
            3. Calls this function with:
               - food_id: The recommended food
               - ml_score: Model confidence (0-1)
               - user_taste_summary: Why this matches user (e.g., "You like spicy Indian food")
               - confidence_class: "high", "medium", or "low"
        
        Member 2 (This API):
            1. Receives recommendation
            2. Looks up food knowledge base
            3. Generates natural explanation
            4. Returns to Member 3 for UI display
        
        Args:
            food_id: Food ID from Member 1's ranking
            ml_score: ML model score (0.0-1.0)
            user_taste_summary: Why this recommendation matches user
            confidence_class: Optional confidence level
            filters: Optional metadata filters
        
        Returns:
            {
                "food_id": "x1a2b3c",
                "explanation": "Natural language explanation...",
                "reasoning": "Why this matches user...",
                "retrieved_document": "Knowledge base content (first 500 chars)...",
                "ml_score": 0.87,
                "user_taste_match": "You like spicy Indian food",
                "grounded": true,
                "limitation_flagged": false,
                "error": null
            }
        
        Raises:
            requests.RequestException: If API call fails
            ValueError: If response contains error
        
        Example:
            >>> client = Member2APIClient()
            >>> response = client.explain_recommendation(
            ...     food_id="curry_chicken_123",
            ...     ml_score=0.87,
            ...     user_taste_summary="You like spicy Indian curries",
            ...     confidence_class="high"
            ... )
            >>> print(response["explanation"])
            "This spicy chicken curry should appeal to your taste for..."
        """
        url = f"{self.base_url}/recommendations/explain"
        
        payload = {
            "food_id": food_id,
            "ml_score": ml_score,
            "user_taste_summary": user_taste_summary,
            "confidence_class": confidence_class,
            "filters": filters or {}
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        # Check for API-level errors
        if data.get("error"):
            raise ValueError(f"API error: {data['error']}")
        
        return data
    
    # =========================================================================
    # Member 3 Integration: Search and ask questions
    # =========================================================================
    
    def search_foods(
        self,
        query: str,
        veg_status: Optional[str] = None,
        food_type: Optional[str] = None,
        category: Optional[str] = None,
        price_min: Optional[int] = None,
        price_max: Optional[int] = None,
        top_k: int = 3
    ) -> Dict[str, Any]:
        """
        Search for foods using natural language query and filters.
        
        Member 3 (UI/Frontend):
            1. User enters search query (e.g., "spicy vegetarian curry")
            2. User applies filters (category, price range, veg_status)
            3. Calls this function
        
        Member 2 (This API):
            1. Encodes query using embeddings model
            2. Searches Chroma vector store
            3. Applies filters
            4. Returns top-k results with similarity scores
        
        Args:
            query: Search query (natural language)
            veg_status: "vegetarian" or "non_vegetarian"
            food_type: Type of food (snack, main_course, dessert, etc.)
            category: Cuisine category (Indian, Chinese, Italian, etc.)
            price_min: Minimum price in rupees
            price_max: Maximum price in rupees
            top_k: Number of results (1-20, default 3)
        
        Returns:
            {
                "query": "spicy vegetarian curry",
                "results": [
                    {
                        "food_id": "curry_veg_001",
                        "name": "Spiced Vegetable Curry",
                        "similarity": 0.89,
                        "metadata": {...}
                    },
                    ...
                ],
                "total": 3,
                "above_threshold": true,
                "error": null
            }
        
        Example:
            >>> client = Member2APIClient()
            >>> results = client.search_foods(
            ...     query="spicy vegetarian",
            ...     veg_status="vegetarian",
            ...     category="Indian",
            ...     price_max=500
            ... )
            >>> for result in results["results"]:
            ...     print(f"{result['name']} ({result['similarity']:.2%})")
        """
        url = f"{self.base_url}/search"
        
        params = {
            "query": query,
            "top_k": top_k
        }
        
        if veg_status:
            params["veg_status"] = veg_status
        if food_type:
            params["food_type"] = food_type
        if category:
            params["category"] = category
        if price_min is not None:
            params["price_min"] = price_min
        if price_max is not None:
            params["price_max"] = price_max
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def ask_question(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 3
    ) -> Dict[str, Any]:
        """
        Ask a general question about foods.
        
        Member 3 (UI/Frontend):
            1. User asks a question (e.g., "What's a good high-protein option?")
            2. Calls this function
        
        Member 2 (This API):
            1. Semantically searches knowledge base
            2. Retrieves top-k relevant foods
            3. Uses LLM to generate grounded answer
            4. Returns answer + sources for transparency
        
        Args:
            query: Food question/request (natural language)
            filters: Optional metadata filters (same as search)
            top_k: Number of source documents (1-20, default 3)
        
        Returns:
            {
                "query": "What's a good high-protein option?",
                "answer": "Based on our menu, here are high-protein options...",
                "sources": [
                    {
                        "food_id": "chicken_tikka_001",
                        "similarity": 0.85,
                        "document": "Knowledge base text..."
                    },
                    ...
                ],
                "grounded": true,
                "error": null
            }
        
        Example:
            >>> client = Member2APIClient()
            >>> answer = client.ask_question(
            ...     query="What's a good high-protein vegetarian option?"
            ... )
            >>> print(answer["answer"])
            >>> print(f"Sources: {len(answer['sources'])} items")
        """
        url = f"{self.base_url}/ask"
        
        payload = {
            "query": query,
            "filters": filters or {},
            "top_k": top_k
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def ask_specific_food(
        self,
        food_id: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Ask a specific question about a known food.
        
        Used when Member 3 wants to ask about a food_id already selected.
        
        Args:
            food_id: The specific food to ask about
            query: Question about the food
        
        Returns:
            Answer grounded in that specific food's knowledge document
        
        Example:
            >>> client = Member2APIClient()
            >>> answer = client.ask_specific_food(
            ...     food_id="curry_001",
            ...     query="Is this vegetarian?"
            ... )
        """
        url = f"{self.base_url}/ask-specific"
        
        params = {
            "food_id": food_id,
            "query": query
        }
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        return response.json()
    
    # =========================================================================
    # System Health
    # =========================================================================
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check API server and component health.
        
        Returns:
            {
                "status": "healthy" or "degraded",
                "timestamp": "2026-08-30T...",
                "components": {
                    "retriever": "✓ Ready",
                    "rag_pipeline": "✓ Ready",
                    "food_layer": "✓ Ready"
                }
            }
        """
        url = f"{self.base_url}/health"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()


# ============================================================================
# Usage Examples
# ============================================================================

def example_member1_integration():
    """
    Example: Member 1 (Recommendation Engine) sends recommendation to Member 2.
    """
    print("\n" + "="*70)
    print("EXAMPLE: Member 1 → Member 2 Integration")
    print("="*70)
    
    client = Member2APIClient()
    
    # Member 1 recommends a food with ML score
    response = client.explain_recommendation(
        food_id="butter_chicken_123",
        ml_score=0.87,
        user_taste_summary="You enjoy creamy, mildly spicy Indian curries with chicken",
        confidence_class="high"
    )
    
    print(f"\n📤 Member 1 Sends:")
    print(f"   Food ID: butter_chicken_123")
    print(f"   ML Score: 0.87 (87% confident)")
    print(f"   User Match: {response['user_taste_match']}")
    
    print(f"\n📥 Member 2 Returns:")
    print(f"   Explanation: {response['explanation'][:100]}...")
    print(f"   Grounded: {response['grounded']}")
    print(f"   Error Flag: {response['limitation_flagged']}")
    
    print(f"\n→ Member 3 (UI) displays this explanation to user")


def example_member3_search():
    """
    Example: Member 3 (UI) searches for foods.
    """
    print("\n" + "="*70)
    print("EXAMPLE: Member 3 → Member 2 Search")
    print("="*70)
    
    client = Member2APIClient()
    
    # Member 3 user searches with filters
    results = client.search_foods(
        query="spicy vegetarian",
        veg_status="vegetarian",
        category="Indian",
        price_max=500,
        top_k=5
    )
    
    print(f"\n🔍 Member 3 Searches:")
    print(f"   Query: {results['query']}")
    print(f"   Filters: vegetarian, Indian category, max ₹500")
    
    print(f"\n📊 Member 2 Returns {results['total']} results:")
    for i, result in enumerate(results['results'], 1):
        print(f"   {i}. {result['name']} ({result['similarity']:.0%} match)")
    
    print(f"\n→ Member 3 displays these results to user")


def example_member3_question():
    """
    Example: Member 3 user asks a question.
    """
    print("\n" + "="*70)
    print("EXAMPLE: Member 3 → Member 2 Question")
    print("="*70)
    
    client = Member2APIClient()
    
    # Member 3 user asks a question
    answer = client.ask_question(
        query="What's a good high-protein vegetarian option?",
        filters={"veg_status": "vegetarian"},
        top_k=3
    )
    
    print(f"\n❓ Member 3 User Asks:")
    print(f"   '{answer['query']}'")
    
    print(f"\n💬 Member 2 Answers:")
    print(f"   {answer['answer'][:150]}...")
    
    print(f"\n📚 Sources ({len(answer['sources'])} items):")
    for source in answer['sources']:
        print(f"   - {source['food_id']} ({source['similarity']:.0%} relevant)")
    
    print(f"\n→ Member 3 displays answer + sources for transparency")


def example_health_check():
    """
    Example: Check API health.
    """
    print("\n" + "="*70)
    print("EXAMPLE: Health Check")
    print("="*70)
    
    client = Member2APIClient()
    
    health = client.health_check()
    
    print(f"\nAPI Status: {health['status']}")
    print(f"Timestamp: {health['timestamp']}")
    print(f"\nComponents:")
    for component, status in health['components'].items():
        print(f"  {component}: {status}")


if __name__ == "__main__":
    """
    Run integration examples.
    
    Prerequisites:
        1. Start API server: python api_server.py
        2. Ensure Phase 1-11 components are ready
        3. Run this script in another terminal
    """
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║     Phase 12: API Integration - Client Examples                ║
    ║     Member 1 & Member 3 Integration Patterns                   ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        example_health_check()
        example_member1_integration()
        example_member3_search()
        example_member3_question()
        
        print("\n" + "="*70)
        print("✓ All integration examples completed successfully!")
        print("="*70)
    
    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        print("  Make sure API server is running: python api_server.py")
