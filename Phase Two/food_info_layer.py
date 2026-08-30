"""
Phase 10 — Food Information Layer

Handles two question types:
  1. About a SPECIFIC food (food_id given) — "why was this recommended",
     "what's in this dish"
  2. OPEN-ENDED food questions (no food_id) — "what's a good spicy vegetarian
     dish" — via semantic search

The core requirement from the roadmap: never invent information that isn't
in the data. Two mechanisms enforce this, not just a prompt instruction:

  1. TOPIC PRE-CHECK — questions about ingredients/nutrition/allergens are
     intercepted BEFORE the LLM is called. Your dataset dropped a full
     `ingredients` field, so an LLM asked "what's in this dish" would be
     tempted to guess plausible ingredients from the dish name — exactly the
     kind of unsupported claim the roadmap forbids. Instead, this layer
     answers with whatever partial info actually exists (protein, base,
     dietary_tags) plus an honest "we don't track full ingredient lists"
     disclaimer.

  2. SIMILARITY THRESHOLD — for open-ended search, if the best retrieved
     match isn't actually relevant (low cosine similarity), the system says
     so rather than forcing an answer out of weak context.

RUN THIS LOCALLY.

Usage:
    from food_info_layer import FoodInformationLayer

    layer = FoodInformationLayer()
    layer.ask("what's in this?", food_id="x8l5__beef-gyro")
    layer.ask("what's a good spicy vegetarian option?")
"""

import re
from typing import Optional
from rag_pipeline import RAGPipeline

KNOWLEDGE_BASE_PATH = "food_knowledge_base.csv"
SIMILARITY_THRESHOLD = 0.30   # below this, treat retrieval as "not actually relevant"

UNSUPPORTED_TOPICS = {
    "ingredients": ["ingredient", "what's in", "whats in", "what is in",
                    "made of", "made with", "contains what", "does it contain",
                    "does this contain", "recipe"],
    "nutrition": ["calorie", "nutrition", "protein content", "carbs", "carbohydrate", "fat content", "sodium"],
    "allergen": ["allergen", "allergy", "allergic"],
}

# Pulls known facts back out of the Phase 7 knowledge_document template —
# works because we control that template's exact wording.
PROTEIN_RE = re.compile(r"Its main protein is (\w+)\.")
BASE_RE = re.compile(r"served with a (\w+) base")
DIETARY_RE = re.compile(r"It is tagged (\w+)\.")


class FoodInformationLayer:
    def __init__(self):
        self.rag = RAGPipeline()
        import pandas as pd
        kb = pd.read_csv(KNOWLEDGE_BASE_PATH, encoding="utf-8")
        self.knowledge_by_id = kb.set_index("food_id")["knowledge_document"].to_dict()

    def _detect_unsupported_topic(self, query_text: str) -> Optional[str]:
        q = query_text.lower()
        for topic, keywords in UNSUPPORTED_TOPICS.items():
            if any(kw in q for kw in keywords):
                return topic
        return None

    def _partial_answer(self, document: str, topic: str) -> str:
        protein = PROTEIN_RE.search(document)
        base = BASE_RE.search(document)
        dietary = DIETARY_RE.search(document)

        known_bits = []
        if protein:
            known_bits.append(f"its main protein is {protein.group(1)}")
        if base:
            known_bits.append(f"it's served with a {base.group(1)} base")
        if dietary:
            known_bits.append(f"it's tagged {dietary.group(1)}")

        known_str = f" What we do know: {', '.join(known_bits)}." if known_bits else ""

        if topic == "ingredients":
            return f"We don't track a full ingredient list for this item.{known_str} Check with the restaurant for exact ingredients."
        if topic == "nutrition":
            return f"We don't track detailed nutrition/calorie information for this item.{known_str} Check with the restaurant for nutrition facts."
        if topic == "allergen":
            return f"We don't track a full allergen list — only general dietary tags.{known_str} If you have a specific allergy, please confirm directly with the restaurant."
        return f"That information isn't available in our data.{known_str}"

    def ask(self, query_text: str, food_id: Optional[str] = None,
             filters: Optional[dict] = None, top_k: int = 3) -> dict:

        topic = self._detect_unsupported_topic(query_text)

        # ---- Path 1: question about a SPECIFIC food ----
        if food_id:
            document = self.knowledge_by_id.get(food_id)
            if document is None:
                return {"query": query_text, "food_id": food_id,
                        "answer": "We don't have information for this food.",
                        "grounded": False, "limitation_flagged": True}

            if topic:
                return {"query": query_text, "food_id": food_id,
                        "answer": self._partial_answer(document, topic),
                        "grounded": True, "limitation_flagged": True}

            system_prompt = (
                "Answer the user's question using ONLY the food information given below. "
                "If the information doesn't fully answer the question, say so honestly "
                "instead of guessing. Never invent ingredients, nutrition facts, or "
                "allergen information not explicitly stated."
            )
            user_prompt = f"Food information: {document}\n\nQuestion: {query_text}"
            answer = self.rag._call_llm(system_prompt, user_prompt)
            return {"query": query_text, "food_id": food_id, "answer": answer,
                    "grounded": True, "limitation_flagged": False}

        # ---- Path 2: OPEN-ENDED question, semantic search ----
        query_embedding = self.rag.embed_model.encode([query_text], normalize_embeddings=True).tolist()
        results = self.rag.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
            where=self.rag._build_where(filters),
        )
        ids = results["ids"][0]
        docs = results["documents"][0]
        dists = results["distances"][0]

        if not docs or (1 - dists[0]) < SIMILARITY_THRESHOLD:
            return {"query": query_text, "food_id": None,
                    "answer": "I don't have confident information matching that request.",
                    "grounded": False, "limitation_flagged": True,
                    "retrieved_food_ids": ids, "best_similarity": round(1 - dists[0], 4) if dists else None}

        if topic:
            # Best-effort across the retrieved set, still no LLM guessing
            combined = " ".join(self._partial_answer(doc, topic) for doc in docs[:1])
            return {"query": query_text, "food_id": None, "answer": combined,
                    "grounded": True, "limitation_flagged": True,
                    "retrieved_food_ids": ids}

        context = "\n".join(f"- {doc}" for doc in docs)
        system_prompt = (
            "Answer using ONLY the context below. If the context doesn't fully answer the "
            "question, say so honestly. Never invent ingredients, nutrition, or allergen facts."
        )
        user_prompt = f"Context:\n{context}\n\nQuestion: {query_text}"
        answer = self.rag._call_llm(system_prompt, user_prompt)

        return {"query": query_text, "food_id": None, "answer": answer,
                "grounded": True, "limitation_flagged": False,
                "retrieved_food_ids": ids,
                "best_similarity": round(1 - dists[0], 4)}


if __name__ == "__main__":
    layer = FoodInformationLayer()
    sample_food_id = next(iter(layer.knowledge_by_id))

    print("=== Ingredient question about a specific food (should NOT call LLM) ===")
    print(layer.ask("what's in this dish?", food_id=sample_food_id))

    print("\n=== Normal question about a specific food (grounded LLM call) ===")
    print(layer.ask("is this spicy?", food_id=sample_food_id))

    print("\n=== Open-ended question ===")
    print(layer.ask("what's a good spicy vegetarian option?"))

    print("\n=== Open-ended nutrition question (should NOT call LLM) ===")
    print(layer.ask("how many calories does a spicy dish have?"))
