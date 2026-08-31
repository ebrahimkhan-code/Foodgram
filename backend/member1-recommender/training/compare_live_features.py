from datetime import datetime
from pathlib import Path

# pyrefly: ignore [missing-import]
import numpy as np

from recommendation.history import (
    load_interactions,
    build_user_history,
)
from recommendation.feature_builder import (
    build_recommendation_features,
)
from taste_dna.loader import load_taste_dna
from training.feature_matrix import (
    FEATURE_COLUMNS,
    load_feature_matrices,
)


BASE_DIR = Path(__file__).parent.parent

TRAIN_PATH = (
    BASE_DIR
    / "data"
    / "synthetic"
    / "train.csv"
)

VALIDATION_PATH = (
    BASE_DIR
    / "data"
    / "synthetic"
    / "validation.csv"
)

TEST_PATH = (
    BASE_DIR
    / "data"
    / "synthetic"
    / "test.csv"
)

INTERACTIONS_PATH = (
    BASE_DIR
    / "data"
    / "synthetic"
    / "interactions.csv"
)

TASTE_DNA_PATH = (
    BASE_DIR
    / "data"
    / "synthetic"
    / "user_preferences.csv"
)


def main():

    (
        X_train,
        _,
        _,
        _,
        _,
        _,
    ) = load_feature_matrices(
        TRAIN_PATH,
        VALIDATION_PATH,
        TEST_PATH,
    )

    interactions = load_interactions(
        INTERACTIONS_PATH
    )

    dna = load_taste_dna(
        TASTE_DNA_PATH,
        "U001",
    )

    latest_timestamp = max(
        datetime.fromisoformat(
           interaction["timestamp"]
    )
    for interaction in interactions
)

    history = build_user_history(
        interactions,
        "U001",
        timestamp=latest_timestamp,
    )

    food = {
        "food_id": "DEBUG",
        "name": "Debug Food",
        "cuisine": "Pakistani",
        "protein": "Chicken",
        "flavor": "Savory",
        "spice_level": "High",
        "base": "Rice",
        "meal_type": "Dinner",
    }

    live_features = build_recommendation_features(
        food=food,
        taste_dna=dna.as_dict(),
        history=history,
        timestamp=latest_timestamp,
     )

    print()
    print("Training vs Live Feature Distribution")
    print("======================================")
    print()

    for index, feature in enumerate(
        FEATURE_COLUMNS
    ):

        training_values = X_train[:, index]
        live_value = live_features[feature]

        mean = np.mean(training_values)
        std = np.std(training_values)

        if std > 0:
            z_score = (
                live_value - mean
            ) / std
        else:
            z_score = 0.0

        print(
            f"{feature:<40} "
            f"live={live_value:>10.3f} "
            f"train_mean={mean:>10.3f} "
            f"train_max={np.max(training_values):>10.3f} "
            f"z={z_score:>8.2f}"
        )


if __name__ == "__main__":
    main()