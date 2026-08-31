from pathlib import Path

from training.feature_matrix import (
    FEATURE_COLUMNS,
)
from recommendation.feature_builder import (
    build_recommendation_features,
)
from recommendation.scorer import score_food
from taste_dna.loader import load_taste_dna


BASE_DIR = Path(__file__).parent.parent

FOODS_PATH = (
    BASE_DIR
    / "data"
    / "synthetic"
    / "foods.csv"
)

TASTE_DNA_PATH = (
    BASE_DIR
    / "data"
    / "synthetic"
    / "user_preferences.csv"
)


def load_foods():
    import csv

    with open(
        FOODS_PATH,
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        return list(csv.DictReader(file))


def main():

    user_id = "U001"

    foods = load_foods()

    dna = load_taste_dna(
        TASTE_DNA_PATH,
        user_id,
    )

    print()
    print("Prediction Debug")
    print("================")
    print()

    for food in foods:

        feature_dict = build_recommendation_features(
            food=food,
            taste_dna=dna.as_dict(),
        )

        feature_vector = [
            feature_dict[feature]
            for feature in FEATURE_COLUMNS
        ]

        score = score_food(
            feature_vector
        )

        print(
            f"{food['food_id']} "
            f"{food['name']:<20} "
            f"score={score:.6f}"
        )

        print(
            "  taste_match="
            f"{feature_dict['taste_match_score']:.4f}"
        )

        print(
            "  history="
            f"{feature_dict['previous_interactions']:.1f}"
        )

        print()

        if food["food_id"] == "F029":
            print("F029 feature vector:")

            for feature, value in zip(
                FEATURE_COLUMNS,
                feature_vector,
            ):
                print(
                    f"  {feature:<40} {value:.6f}"
                )

            print()

    print("Done.")


if __name__ == "__main__":
    main()