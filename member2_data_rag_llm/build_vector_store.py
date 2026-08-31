"""
Phase 5 — Vector Store (ChromaDB)

Wraps the Phase 4 embeddings in a persistent, filterable vector database.
This gives Member 1 a single function to call: "find foods semantically
similar to X, optionally restricted to vegetarian / a spice level / a price
range" — that's the hybrid retrieval interface named in the roadmap (Phase 6).

RUN THIS LOCALLY, after Phase 4 has produced:
    food_embeddings.npy
    food_id_order.csv
in the same folder, alongside menu_dataset_phase3_semantic.csv.

Setup:
    pip install chromadb sentence-transformers pandas numpy
    python build_vector_store.py

Design choice: we pass our OWN precomputed embeddings (from Phase 4) into
Chroma instead of letting Chroma pick its own default embedding model.
Reasons:
  1. Consistency — the vectors stored are exactly the ones we already
     validated in Phase 4's sanity check, not a second, different model.
  2. No redundant download — Chroma's default embedding function would
     pull its own model; we already have one cached from Phase 4.
  3. Control — if you ever swap embedding models, there's one place
     (generate_embeddings.py) that changes, not a hidden default inside
     Chroma's config.

The tradeoff: because Chroma doesn't know how to embed NEW text on its own
here, this script also loads the same sentence-transformer model once, just
to embed incoming search queries at query time (fast — one sentence per
query, not the whole dataset).
"""

import numpy as np
import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer

DATA_PATH = "menu_dataset_phase3_semantic.csv"
EMBEDDINGS_PATH = "food_embeddings.npy"
ID_ORDER_PATH = "food_id_order.csv"
CHROMA_DIR = "./chroma_db"          # persists to disk here
COLLECTION_NAME = "foods"
MODEL_NAME = "all-MiniLM-L6-v2"     # must match generate_embeddings.py

# Metadata fields Member 1/3 can filter on later (e.g. where={"veg_status": "vegetarian"})
METADATA_FIELDS = [
    "restaurant", "category", "food_type", "meal_type",
    "dietary_tags", "spice_level", "veg_status", "price",
    "cuisine", "protein", "flavor", "base",
    # Not used for filtering, but kept for traceability/debugging in the RAG
    # layer (Phase 7 requirement) — lets the explanation step show its work
    # without re-parsing semantic_text or going back to the original CSV.
    "name", "description", "source",
]

BATCH_SIZE = 500  # Chroma has an internal max batch size; chunking is safe regardless of dataset size


def build_metadata(row) -> dict:
    """Only include non-null fields — Chroma rejects NaN as a metadata value,
    and a food missing a field (e.g. no price) shouldn't block indexing it."""
    meta = {}
    for field in METADATA_FIELDS:
        val = row[field]
        if pd.notna(val):
            # Chroma metadata values must be str/int/float/bool
            meta[field] = val.item() if hasattr(val, "item") else val
    return meta


def main():
    df = pd.read_csv(DATA_PATH, encoding="utf-8")
    embeddings = np.load(EMBEDDINGS_PATH)
    id_order = pd.read_csv(ID_ORDER_PATH)["food_id"].tolist()

    # Re-order df to exactly match the embeddings' row order (they were saved
    # independently — this alignment step is what keeps vector[i] matched to
    # the correct food_id[i]).
    df = df.set_index("food_id").loc[id_order].reset_index()
    assert len(df) == len(embeddings), "Row count mismatch between CSV and embeddings — check inputs"

    client = chromadb.PersistentClient(path=CHROMA_DIR)
    # get_or_create so re-running this script is safe/idempotent
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},  # match Phase 4's normalized-cosine setup
    )

    print(f"Indexing {len(df)} foods into Chroma at '{CHROMA_DIR}'...")
    for start in range(0, len(df), BATCH_SIZE):
        end = start + BATCH_SIZE
        batch = df.iloc[start:end]
        collection.upsert(
            ids=batch["food_id"].tolist(),
            embeddings=embeddings[start:end].tolist(),
            documents=batch["semantic_text"].tolist(),
            metadatas=[build_metadata(row) for _, row in batch.iterrows()],
        )
        print(f"  {min(end, len(df))}/{len(df)}")

    print(f"Done. Collection now has {collection.count()} items.")

    # ---- Demo: hybrid retrieval (semantic + metadata filter) ----
    print("\n--- Demo query ---")
    model = SentenceTransformer(MODEL_NAME)
    query = "spicy chicken curry"
    query_embedding = model.encode([query], normalize_embeddings=True).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=5,
        where={"veg_status": "non_vegetarian"},  # example metadata filter
    )
    print(f"Query: '{query}' (filtered to non_vegetarian)")
    for doc, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
        print(f"  dist={dist:.3f}  {doc}")


if __name__ == "__main__":
    main()
