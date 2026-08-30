"""
Phase 8b — RAG Pipeline

Two entry points:
  1. explain_recommendation(food_id, ml_score, confidence_class)
     -> direct lookup by food_id (no search needed), LLM phrases the
        explanation. Used when Member 1 has already picked a specific food.

  2. answer_food_question(query_text, filters=None, top_k=3)
     -> semantic search over the Phase 8a knowledge embeddings, LLM answers
        USING ONLY the retrieved documents. Used for open-ended questions.

Both return the generated text PLUS retrieval metadata (which food_ids/
documents were used) — needed per the roadmap for debugging and for Phase 11
(RAG evaluation) later.

Hard rule enforced in the prompts, not left to hope: the LLM must not alter
the ML score it's given, and must not state ingredients/nutrition facts that
aren't in the retrieved document.

RUN THIS LOCALLY.

Setup:
    pip install chromadb sentence-transformers openai pandas
    export OPENROUTER_API_KEY="your_key_here"
    python rag_pipeline.py     # runs a couple of demo calls at the bottom
"""

import os
import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer
from openai import OpenAI

KNOWLEDGE_BASE_PATH = "food_knowledge_base.csv"
CHROMA_DIR = "./chroma_db"
KNOWLEDGE_COLLECTION = "food_knowledge"
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
LLM_MODEL_NAME = "meta-llama/llama-3.3-70b-instruct"  # check openrouter.ai/models?fmt=free — free models rotate

EXACT_MATCH_FIELDS = [
    "veg_status", "food_type", "meal_type", "dietary_tags",
    "spice_level", "restaurant", "category",
    "cuisine", "protein", "flavor", "base",
]


class RAGPipeline:
    def __init__(self):
        # Fast lookup path: food_id -> knowledge_document, no embedding needed
        kb = pd.read_csv(KNOWLEDGE_BASE_PATH, encoding="utf-8")
        self.knowledge_by_id = kb.set_index("food_id")["knowledge_document"].to_dict()

        # Semantic search path
        self.embed_model = SentenceTransformer(EMBED_MODEL_NAME)
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        self.collection = client.get_collection(name=KNOWLEDGE_COLLECTION)

        # LLM
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("Set OPENROUTER_API_KEY environment variable first.")
        self.llm = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

    def _build_where(self, filters):
        if not filters:
            return None
        conditions = [{k: v} for k, v in filters.items() if k in EXACT_MATCH_FIELDS and v is not None]
        if not conditions:
            return None
        return conditions[0] if len(conditions) == 1 else {"$and": conditions}

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        response = self.llm.chat.completions.create(
            model=LLM_MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,  # a little natural variation is fine here — this isn't structured extraction
            max_tokens=200,
        )
        return response.choices[0].message.content.strip()

    # ---- Mode 1: explanation for a specific recommended food ----
    def explain_recommendation(self, food_id: str, ml_score: float, confidence_class: str = None) -> dict:
        document = self.knowledge_by_id.get(food_id)
        if document is None:
            return {
                "food_id": food_id,
                "explanation": "No information available for this food.",
                "retrieved_document": None,
                "ml_score": ml_score,
            }

        system_prompt = (
            "You explain food recommendations to users in 1-2 friendly sentences. "
            "Use ONLY the facts given below — never invent ingredients, nutrition claims, "
            "or details not present in the provided information. "
            "Never state or imply a different match score than the one given to you."
        )
        user_prompt = (
            f"Food information: {document}\n"
            f"Match score (0-1, given by the recommendation model, do not alter or restate as a different number): {ml_score}\n"
            f"Confidence: {confidence_class or 'not specified'}\n\n"
            "Write a short, natural explanation of why this might suit the user."
        )
        explanation = self._call_llm(system_prompt, user_prompt)

        return {
            "food_id": food_id,
            "explanation": explanation,
            "retrieved_document": document,   # returned for debugging/traceability
            "ml_score": ml_score,
        }

    # ---- Mode 2: open-ended food question, semantic search + grounded answer ----
    def answer_food_question(self, query_text: str, filters: dict = None, top_k: int = 3) -> dict:
        query_embedding = self.embed_model.encode([query_text], normalize_embeddings=True).tolist()
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
            where=self._build_where(filters),
        )

        ids = results["ids"][0]
        docs = results["documents"][0]
        dists = results["distances"][0]

        if not docs:
            return {
                "query": query_text,
                "answer": "I don't have information matching that request.",
                "retrieved_food_ids": [],
                "sources": [],
            }

        context = "\n".join(f"- {doc}" for doc in docs)
        system_prompt = (
            "You answer food questions using ONLY the context provided below. "
            "If the context doesn't fully answer the question, say so honestly instead "
            "of guessing or inventing details. Never state ingredients or nutrition facts "
            "that aren't in the context."
        )
        user_prompt = f"Context:\n{context}\n\nQuestion: {query_text}"
        answer = self._call_llm(system_prompt, user_prompt)

        return {
            "query": query_text,
            "answer": answer,
            "retrieved_food_ids": ids,
            "sources": [{"food_id": i, "similarity": round(1 - d, 4), "document": doc}
                        for i, doc, d in zip(ids, docs, dists)],
        }


if __name__ == "__main__":
    rag = RAGPipeline()

    print("=== Mode 1: explain a specific recommendation ===")
    # Swap in a real food_id from your dataset to test this properly
    sample_food_id = next(iter(rag.knowledge_by_id))
    result = rag.explain_recommendation(sample_food_id, ml_score=0.87, confidence_class="high")
    print(result["explanation"])
    print(f"(grounded in: {result['retrieved_document'][:80]}...)")

    print("\n=== Mode 2: open-ended question with a filter ===")
    result = rag.answer_food_question(
        "What's a good breakfast option option?",
        filters={"meal_type": "breakfast"},
        top_k=3,
    )
    print(result["answer"])
    print("Sources used:", [s["food_id"] for s in result["sources"]])
