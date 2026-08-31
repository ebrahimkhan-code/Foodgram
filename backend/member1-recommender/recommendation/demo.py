import csv
import sys
from pathlib import Path
from datetime import datetime

from recommendation.history import (
    load_interactions,
    build_user_history,
)
from recommendation.pipeline import recommend_foods
from taste_dna.loader import load_taste_dna


BASE_DIR = Path(__file__).parent.parent

# ---------------------------------------------------------
# REAL FOOD CATALOG
# ---------------------------------------------------------

FOODS_PATH = (
    BASE_DIR
    / "data"
    / "menu_dataset_enriched_claude_FINAL.csv"
)

# ---------------------------------------------------------
# SYNTHETIC USER DATA
# ---------------------------------------------------------

TASTE_DNA_PATH = (
    BASE_DIR
    / "data"
    / "synthetic"
    / "user_preferences.csv"
)

INTERACTIONS_PATH = (
    BASE_DIR
    / "data"
    / "synthetic"
    / "interactions.csv"
)


REQUIRED_FOOD_COLUMNS = [
    "food_id",
    "name",
    "cuisine",
    "protein",
    "flavor",
    "spice_level",
    "base",
    "meal_type",
]


def load_foods():
    """Load and validate the real food catalog."""

    if not FOODS_PATH.exists():
        raise FileNotFoundError(
            f"Food dataset not found: {FOODS_PATH}"
        )

    with open(
        FOODS_PATH,
        "r",
        encoding="utf-8",
        newline="",
    ) as file:

        foods = list(
            csv.DictReader(file)
        )

    if not foods:
        raise ValueError(
            "Food dataset is empty."
        )

    missing = [
        column
        for column in REQUIRED_FOOD_COLUMNS
        if column not in foods[0]
    ]

    if missing:
        raise ValueError(
            f"Food dataset missing required columns: {missing}"
        )

    return foods


def main():

    # -----------------------------------------------------
    # User
    # -----------------------------------------------------

    user_id = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "U001"
    )

    # -----------------------------------------------------
    # Load food catalog
    # -----------------------------------------------------

    foods = load_foods()

    print(
        f"Loaded {len(foods)} foods from:"
    )

    print(
        f"  {FOODS_PATH}"
    )

    # -----------------------------------------------------
    # Load Taste DNA
    # -----------------------------------------------------

    taste_dna = load_taste_dna(
        TASTE_DNA_PATH,
        user_id,
    )

    # -----------------------------------------------------
    # Load interactions
    # -----------------------------------------------------

    interactions = load_interactions(
        INTERACTIONS_PATH,
    )

    if not interactions:
        raise ValueError(
            "No interactions found."
        )

    # -----------------------------------------------------
    # Latest interaction timestamp
    # -----------------------------------------------------

    latest_timestamp = max(
        datetime.fromisoformat(
            interaction["timestamp"]
        )
        for interaction in interactions
    )

    # -----------------------------------------------------
    # Build user history
    # -----------------------------------------------------

    history = build_user_history(
        interactions,
        user_id,
        timestamp=latest_timestamp,
    )

    # -----------------------------------------------------
    # Generate recommendations
    # -----------------------------------------------------

    results = recommend_foods(
        foods=foods,
        taste_dna=taste_dna.as_dict(),
        history=history,
        timestamp=latest_timestamp,
        top_k=10,
    )

    # -----------------------------------------------------
    # Output
    # -----------------------------------------------------

    print()
    print("Food Recommendations")
    print("====================")
    print()

    print(
        f"User: {user_id}"
    )

    print()

    # -----------------------------------------------------
    # User history
    # -----------------------------------------------------

    print("User History")
    print("------------")

    print(
        f"Likes:        "
        f"{history['previous_likes']:.0f}"
    )

    print(
        f"Dislikes:     "
        f"{history['previous_dislikes']:.0f}"
    )

    print(
        f"Saves:        "
        f"{history['previous_saves']:.0f}"
    )

    print(
        f"Skips:        "
        f"{history['previous_skips']:.0f}"
    )

    print(
        f"Interactions: "
        f"{history['previous_interactions']:.0f}"
    )

    print()

    # -----------------------------------------------------
    # Recommendations
    # -----------------------------------------------------

    print("Top Recommendations")
    print("-------------------")

    for index, result in enumerate(
        results,
        start=1,
    ):

        food = result["food"]
        score = result["score"]

        name = food.get(
            "name",
            "Unknown Food",
        )

        cuisine = food.get(
            "cuisine",
            "unknown",
        )

        protein = food.get(
            "protein",
            "unknown",
        )

        print(
            f"{index:2}. "
            f"{name:<35} "
            f"{cuisine:<18} "
            f"{protein:<12} "
            f"score={score:.4f}"
        )


if __name__ == "__main__":
    main()