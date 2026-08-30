"""
Phase 8a — Embed the knowledge base for semantic RAG search

Separate from Phase 4/5's embeddings: those embedded the short semantic_text
for RECOMMENDATION similarity. This embeds the longer, richer
knowledge_document from Phase 7, for OPEN-ENDED FOOD QUESTIONS — a different
retrieval need, so it gets its own vectors and its own Chroma collection.

RUN THIS LOCALLY (needs Hugging Face Hub access to download the model).

Setup:
    pip install sentence-transformers chromadb pandas numpy
    python build_knowledge_embeddings.py
"""

import numpy as np
import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer

INPUT_PATH = "food_knowledge_base.csv"
CHROMA_DIR = "./chroma_db"                  # same dir as Phase 5 — different collection inside it
COLLECTION_NAME = "food_knowledge"          # distinct from Phase 5's "foods" collection
MODEL_NAME = "all-MiniLM-L6-v2"             # same model as Phase 4, for consistency

METADATA_FIELDS = [
    "restaurant", "category", "food_type", "meal_type",
    "dietary_tags", "spice_level", "veg_status", "price",
    "cuisine", "protein", "flavor", "base",
]
BATCH_SIZE = 500


def build_metadata(row) -> dict:
    meta = {}
    for field in METADATA_FIELDS:
        val = row[field]
        if pd.notna(val):
            meta[field] = val.item() if hasattr(val, "item") else val
    return meta


def main():
    df = pd.read_csv(INPUT_PATH, encoding="utf-8")
    print(f"Loaded {len(df)} knowledge documents.")

    model = SentenceTransformer(MODEL_NAME)
    print("Encoding knowledge documents...")
    embeddings = model.encode(
        df["knowledge_document"].tolist(),
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    print(f"Indexing into Chroma collection '{COLLECTION_NAME}'...")
    for start in range(0, len(df), BATCH_SIZE):
        end = start + BATCH_SIZE
        batch = df.iloc[start:end]
        collection.upsert(
            ids=batch["food_id"].tolist(),
            embeddings=embeddings[start:end].tolist(),
            documents=batch["knowledge_document"].tolist(),
            metadatas=[build_metadata(row) for _, row in batch.iterrows()],
        )
        print(f"  {min(end, len(df))}/{len(df)}")

    print(f"Done. Collection now has {collection.count()} items.")


if __name__ == "__main__":
    main()
