"""
Phase 3 — Food Semantic Representation

Builds one standardized sentence per food item from structured metadata.
This sentence is the input to Phase 4 (embeddings) — its consistency and
clarity directly determines retrieval quality later.

Design choice: template-based, not LLM-generated. A fixed template keeps
every row's sentence in the same shape (same field order, same phrasing),
which helps the embedding model learn a stable pattern across 5,795 items.
An LLM-written sentence per item would vary in style row to row and add
noise to the embedding space for no real benefit here, since all the
information is already structured.
"""

import pandas as pd

INPUT_PATH = "menu_dataset_enriched_FINAL.csv"
OUTPUT_PATH = "menu_dataset_phase3_semantic.csv"

VEG_LABELS = {
    "vegetarian": "vegetarian",
    "non_vegetarian": "non-vegetarian",
    "uncertain": "vegetarian status unclear",
}


def build_semantic_text(row) -> str:
    name = row["name"]
    category = row["category"] if pd.notna(row["category"]) else "general"
    food_type = row["food_type"]
    veg_label = VEG_LABELS.get(row["veg_status"], "vegetarian status unclear")
    dietary = row["dietary_tags"]
    spice = row["spice_level"] if pd.notna(row["spice_level"]) else "unspecified"
    meal = row["meal_type"]
    restaurant = row["restaurant"]
    cuisine = row.get("cuisine")
    protein = row.get("protein")
    flavor = row.get("flavor")
    base = row.get("base")

    parts = [f"{name} — {category} category"]

    # New Taste DNA attributes — only included when confidently known, since
    # "unknown"/"none" convey no information and would just add noise to
    # every sentence (60% of rows have flavor: unknown, for example).
    if isinstance(cuisine, str) and cuisine.lower() not in ("unknown", "none"):
        parts.append(f"{cuisine} cuisine")

    parts.append(f"{food_type} dish")

    if isinstance(protein, str) and protein.lower() not in ("unknown", "none", "vegetarian"):
        parts.append(f"{protein} protein")

    if isinstance(base, str) and base.lower() not in ("unknown", "none"):
        parts.append(f"{base} base")

    parts.append(veg_label)

    if isinstance(dietary, str) and dietary != "none" and dietary != veg_label:
        parts.append(dietary)

    if isinstance(flavor, str) and flavor.lower() not in ("unknown", "none", "neutral"):
        parts.append(f"{flavor} flavor")

    parts.append(f"{spice} spice level")
    parts.append(f"{meal} meal")

    return ", ".join(parts) + f", served at {restaurant}."


def main():
    df = pd.read_csv(INPUT_PATH, encoding="utf-8")
    df["semantic_text"] = df.apply(build_semantic_text, axis=1)

    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")

    print(f"Built semantic_text for {len(df)} rows.")
    print("\nSample outputs:")
    for text in df["semantic_text"].sample(6, random_state=1):
        print(" -", text)

    lengths = df["semantic_text"].str.split().str.len()
    print(f"\nWord count — min: {lengths.min()}, mean: {lengths.mean():.1f}, max: {lengths.max()}")
    print(f"\nSaved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
