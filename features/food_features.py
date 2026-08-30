import csv
from pathlib import Path
from typing import Dict, List

# pyrefly: ignore [missing-import]
import numpy as np
from sklearn.preprocessing import OneHotEncoder


REQUIRED_COLUMNS = [
    "food_id",
    "name",
    "cuisine",
    "protein",
    "flavor",
    "spice_level",
    "base",
    "meal_type",
]

CATEGORICAL_COLUMNS = [
    "cuisine",
    "protein",
    "flavor",
    "spice_level",
    "base",
    "meal_type",
]


def load_foods(csv_path: str | Path) -> List[Dict[str, str]]:
    """Load and validate the food dataset."""

    csv_path = Path(csv_path)

    if not csv_path.exists():
        raise FileNotFoundError(
            f"Food dataset not found: {csv_path}"
        )

    with open(csv_path, "r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            raise ValueError("Food CSV has no header.")

        missing_columns = [
            column
            for column in REQUIRED_COLUMNS
            if column not in reader.fieldnames
        ]

        if missing_columns:
            raise ValueError(
                f"Missing required columns: {missing_columns}"
            )

        foods = list(reader)

    if not foods:
        raise ValueError("Food dataset is empty.")

    food_ids = [food["food_id"].strip() for food in foods]

    if any(not food_id for food_id in food_ids):
        raise ValueError("Food dataset contains an empty food_id.")

    if len(food_ids) != len(set(food_ids)):
        raise ValueError("Food dataset contains duplicate food_id values.")

    return foods


class FoodFeatureEncoder:
    """
    Converts categorical food attributes into numerical features.

    The encoder is fitted once on training data and then reused
    for inference so the feature representation stays consistent.
    """

    def __init__(self):
        self.encoder = OneHotEncoder(
            handle_unknown="ignore",
            sparse_output=False,
        )

        self.is_fitted = False

    def fit(self, foods: List[Dict[str, str]]):
        """Learn the possible categorical values from food data."""

        if not foods:
            raise ValueError("Cannot fit encoder on empty food data.")

        values = [
            [food[column] for column in CATEGORICAL_COLUMNS]
            for food in foods
        ]

        self.encoder.fit(values)
        self.is_fitted = True

        return self

    def transform(self, foods: List[Dict[str, str]]) -> np.ndarray:
        """Convert food records into numerical feature vectors."""

        if not self.is_fitted:
            raise RuntimeError(
                "Encoder must be fitted before transform()."
            )

        if not foods:
            return np.empty(
                (0, len(self.get_feature_names())),
                dtype=float,
            )

        values = [
            [food[column] for column in CATEGORICAL_COLUMNS]
            for food in foods
        ]

        return self.encoder.transform(values)

    def fit_transform(self, foods: List[Dict[str, str]]) -> np.ndarray:
        """Fit the encoder and transform the same food data."""

        self.fit(foods)
        return self.transform(foods)

    def get_feature_names(self) -> List[str]:
        """Return the generated numerical feature names."""

        if not self.is_fitted:
            raise RuntimeError(
                "Encoder must be fitted before getting feature names."
            )

        return list(
            self.encoder.get_feature_names_out(
                CATEGORICAL_COLUMNS
            )
        )