"""
Phase 6 — Hybrid Retrieval

A clean retrieval interface wrapping the Chroma vector store from Phase 5.
This is what Member 1 (ranking/prediction) and the RAG/explanation service
call — neither of them should need to know Chroma exists underneath.

RUN THIS LOCALLY, in the same folder as chroma_db/ (built by
build_vector_store.py).

Setup:
    pip install chromadb sentence-transformers

Usage:
    from retrieval import HybridRetriever

    retriever = HybridRetriever()
    results = retriever.retrieve(
        query_text="spicy chicken curry",
        filters={"veg_status": "non_vegetarian", "price_max": 800},
        top_k=5,
    )
    for r in results:
        print(r["similarity"], r["name"], r["metadata"])
"""

import chromadb
from typing import Optional
from sentence_transformers import SentenceTransformer

CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "foods"
MODEL_NAME = "all-MiniLM-L6-v2"   # must match generate_embeddings.py / build_vector_store.py

# Filter keys that map directly to an equality check on stored metadata
EXACT_MATCH_FIELDS = [
    "veg_status", "food_type", "meal_type", "dietary_tags",
    "spice_level", "restaurant", "category",
    "cuisine", "protein", "flavor", "base",
]


class HybridRetriever:
    def __init__(self, chroma_dir: str = CHROMA_DIR, collection_name: str = COLLECTION_NAME,
                 model_name: str = MODEL_NAME):
        self.client = chromadb.PersistentClient(path=chroma_dir)
        self.collection = self.client.get_collection(name=collection_name)
        self.model = SentenceTransformer(model_name)

    def _build_where(self, filters: Optional[dict]) -> Optional[dict]:
        """Turns a simple flat filter dict into Chroma's where-clause syntax,
        combining multiple conditions with $and only when there's more than
        one — Chroma errors if you wrap a single condition in $and."""
        if not filters:
            return None

        conditions = []
        for field in EXACT_MATCH_FIELDS:
            if field in filters and filters[field] is not None:
                conditions.append({field: filters[field]})

        if "price_min" in filters and filters["price_min"] is not None:
            conditions.append({"price": {"$gte": filters["price_min"]}})
        if "price_max" in filters and filters["price_max"] is not None:
            conditions.append({"price": {"$lte": filters["price_max"]}})

        if not conditions:
            return None
        if len(conditions) == 1:
            return conditions[0]
        return {"$and": conditions}

    def retrieve(self, query_text: str, filters: Optional[dict] = None, top_k: int = 10) -> list:
        """
        filters (all optional):
            veg_status, food_type, meal_type, dietary_tags, spice_level,
            restaurant, category  -> exact match
            price_min, price_max  -> numeric range
        """
        query_embedding = self.model.encode([query_text], normalize_embeddings=True).tolist()
        where = self._build_where(filters)

        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
            where=where,
        )

        output = []
        ids = results["ids"][0]
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        dists = results["distances"][0]

        for food_id, doc, meta, dist in zip(ids, docs, metas, dists):
            # semantic_text always starts "{name} — {category} category, ..."
            # per Phase 3's template, so this split reliably recovers the name
            # without needing a redundant "name" field in metadata.
            name = doc.split(" — ")[0] if " — " in doc else doc
            output.append({
                "food_id": food_id,
                "name": name,
                "semantic_text": doc,
                "metadata": meta,
                "similarity": round(1 - dist, 4),  # cosine distance -> similarity, higher = more relevant
            })
        return output


if __name__ == "__main__":
    # Quick manual smoke test when run directly
    retriever = HybridRetriever()

    print("=== Query 1: pure semantic, no filters ===")
    for r in retriever.retrieve("cheesy pizza", top_k=5):
        print(f"  sim={r['similarity']:.3f}  {r['semantic_text']}")

    print("\n=== Query 2: semantic + single filter ===")
    for r in retriever.retrieve("spicy curry", filters={"protein": "beef"}, top_k=5):
        print(f"  sim={r['similarity']:.3f}  {r['semantic_text']}")

    print("\n=== Query 3: semantic + multiple filters (exact + price range) ===")
    for r in retriever.retrieve(
        "fanta",
        filters={"Cuisine": "cafe", "flavor": "sweet"},
        top_k=5,
    ):
        print(f"  sim={r['similarity']:.3f}  {r['semantic_text']}")
