"""
Phase 4 — Embeddings

Converts each food's semantic_text into a 384-dim vector using a local
sentence-transformer model. Fully free, fully local — only needs internet
once to download the model (~80MB), then works fully offline.

RUN THIS LOCALLY. It won't run in a network-sandboxed environment that can't
reach huggingface.co to fetch the model weights.

Setup:
    pip install sentence-transformers pandas numpy
    python generate_embeddings.py

Output:
    food_embeddings.npy   — shape (n_rows, 384), float32 vectors
    food_id_order.csv     — food_id in the exact same row order as the .npy
                            file, so you can always map a vector back to a food
"""

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

INPUT_PATH = "menu_dataset_phase3_semantic.csv"
EMBEDDINGS_OUT = "food_embeddings.npy"
ID_ORDER_OUT = "food_id_order.csv"

MODEL_NAME = "all-MiniLM-L6-v2"


def main():
    df = pd.read_csv(INPUT_PATH, encoding="utf-8")
    print(f"Loaded {len(df)} rows.")

    print(f"Loading model '{MODEL_NAME}' (downloads once, then cached locally)...")
    model = SentenceTransformer(MODEL_NAME)

    texts = df["semantic_text"].tolist()
    print("Encoding... (a progress bar will show below)")
    embeddings = model.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,  # pre-normalize so cosine similarity == dot product later
    )

    print(f"\nEmbeddings shape: {embeddings.shape}")  # (n_rows, 384)

    np.save(EMBEDDINGS_OUT, embeddings.astype("float32"))
    df[["food_id"]].to_csv(ID_ORDER_OUT, index=False)

    print(f"Saved embeddings to {EMBEDDINGS_OUT}")
    print(f"Saved matching food_id order to {ID_ORDER_OUT}")

    # Quick sanity check: does semantic similarity actually work as expected?
    print("\n--- Sanity check: nearest neighbors for a sample dish ---")
    sample_idx = 0
    sample_text = texts[sample_idx]
    sims = embeddings @ embeddings[sample_idx]  # cosine sim, since already normalized
    top5 = np.argsort(-sims)[:6]  # includes itself at rank 0
    print(f"Query: {sample_text}")
    for i in top5[1:]:
        print(f"  sim={sims[i]:.3f}  {texts[i]}")


if __name__ == "__main__":
    main()
