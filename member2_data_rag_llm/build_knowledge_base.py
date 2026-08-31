"""
Phase 7 — Food Knowledge Base

Builds one rich, human-readable knowledge document per food item, meant to
ground LLM explanations (Phase 9) and food-info answers (Phase 10) in real
data rather than letting the LLM invent details.

Difference from Phase 3's semantic_text:
  - semantic_text: short, structured, built for SIMILARITY MATCHING
    (used by the recommendation retriever in Phase 6)
  - knowledge_document (this phase): longer, descriptive, built for
    GROUNDING AN EXPLANATION — this is what gets handed to the LLM as
    context when it explains "why we recommended this" or answers a
    question about a specific dish

This phase does NOT require an embedding model or any external API — it's
pure templating from columns you already have, so it runs directly here.

Output: food_knowledge_base.csv — one row per food, with:
  - food_id            (lookup key — Member 1 hands you this directly)
  - knowledge_document (the text to feed the LLM as context)
  - source             (provenance, kept for debugging/traceability)
  - full metadata columns alongside, for direct filtering/lookup without
    re-parsing the document text
"""

import re
import pandas as pd

INPUT_PATH = "menu_dataset_phase3_semantic.csv"
OUTPUT_PATH = "food_knowledge_base.csv"

# Matches the templated rule-based description from fill_rule_based.py —
# when a description matches this, it's redundant with what this script
# already states more richly, so it gets skipped rather than duplicated.
RULE_BASED_DESC_RE = re.compile(r"^.+ is a .+ item from .+, listed under the .+ menu\.$")


def article_for(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def format_price(price, flag) -> str:
    if pd.isna(price):
        return "price unavailable"
    if flag == "zero_price_review":
        return f"PKR {price:.0f} (flagged — may be a scrape error, verify before display)"
    return f"PKR {price:.0f}"


def format_rating(rating) -> str:
    if pd.isna(rating):
        return "no customer rating available yet"
    return f"a customer rating of {rating:.1f}/5"


def format_location(area, city) -> str:
    parts = [p for p in [area, city] if isinstance(p, str) and p.strip()]
    return ", ".join(parts) if parts else "location unspecified"


def build_knowledge_document(row) -> str:
    name = row["name"]
    restaurant = row["restaurant"]
    location = format_location(row.get("area"), row.get("city"))
    category = row["category"] if pd.notna(row["category"]) else "uncategorized"
    food_type = row["food_type"]
    veg = {
        "vegetarian": "vegetarian",
        "non_vegetarian": "non-vegetarian",
        "uncertain": "of unconfirmed vegetarian/non-vegetarian status",
    }.get(row["veg_status"], "of unconfirmed vegetarian/non-vegetarian status")
    dietary = row["dietary_tags"]
    spice = row["spice_level"] if pd.notna(row["spice_level"]) else "unspecified"
    spice_clause = "an unspecified spice level" if spice in ("unspecified", "none") else f"a {spice} spice level"
    meal = row["meal_type"]
    price_str = format_price(row["price"], row.get("price_flag"))
    rating_str = format_rating(row.get("rating"))
    raw_description = row["description"] if pd.notna(row["description"]) else ""

    cuisine = row.get("cuisine")
    protein = row.get("protein")
    base = row.get("base")
    flavor = row.get("flavor")

    cuisine_clause = f" It is {cuisine} cuisine." if isinstance(cuisine, str) and cuisine.lower() not in ("unknown", "none") else ""
    protein_clause = f" Its main protein is {protein}." if isinstance(protein, str) and protein.lower() not in ("unknown", "none", "vegetarian") else ""
    base_clause = f" It is served with a {base} base." if isinstance(base, str) and base.lower() not in ("unknown", "none") else ""
    flavor_clause = f" Its flavor profile is {flavor}." if isinstance(flavor, str) and flavor.lower() not in ("unknown", "none", "neutral") else ""

    # Skip the description if it's just the rule-based template — it would
    # otherwise duplicate the sentence this function already builds.
    extra_description = "" if RULE_BASED_DESC_RE.match(raw_description.strip()) else raw_description

    # Avoid "vegetarian ... tagged vegetarian" when dietary_tags says the
    # same thing veg_status already said.
    dietary_clause = ""
    if isinstance(dietary, str) and dietary not in ("none", "vegetarian", "non_vegetarian"):
        dietary_clause = f" It is tagged {dietary}."

    doc = (
        f"{name} is {article_for(food_type)} {food_type} dish available at {restaurant} in {location}. "
        f"It falls under the {category} category, is {veg}, and has {spice_clause}."
        f"{cuisine_clause}{protein_clause}{base_clause}{flavor_clause} "
        f"It is typically eaten as {'a ' + meal + ' item' if meal != 'anytime' else 'an anytime item'}."
        f"{dietary_clause} "
        f"It is priced at {price_str} and has {rating_str}."
    ).strip()

    if extra_description:
        doc += f" {extra_description}"

    return doc


def main():
    df = pd.read_csv(INPUT_PATH, encoding="utf-8")
    df["knowledge_document"] = df.apply(build_knowledge_document, axis=1)

    keep_cols = [
        "food_id", "knowledge_document", "name", "restaurant", "category",
        "food_type", "meal_type", "veg_status", "dietary_tags", "spice_level",
        "cuisine", "protein", "flavor", "base",
        "price", "price_flag", "rating", "area", "city", "source", "image_url",
    ]
    df = df[keep_cols]
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")

    print(f"Built knowledge documents for {len(df)} foods.")
    print("\nSample documents:")
    for doc in df["knowledge_document"].sample(4, random_state=2):
        print(" -", doc)
        print()

    lengths = df["knowledge_document"].str.split().str.len()
    print(f"Word count — min: {lengths.min()}, mean: {lengths.mean():.1f}, max: {lengths.max()}")
    print(f"\nSaved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
