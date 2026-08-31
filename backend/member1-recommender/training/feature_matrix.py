import csv
from pathlib import Path
from typing import List, Dict, Tuple

# pyrefly: ignore [missing-import]
import numpy as np


FEATURE_COLUMNS = [
    "cuisine_match",
    "protein_match",
    "flavor_match",
    "spice_level_match",
    "base_match",
    "meal_type_match",
    "taste_match_score",
    "previous_likes",
    "previous_dislikes",
    "previous_saves",
    "previous_skips",
    "previous_interactions",
    "days_since_previous_interaction",
    "hour",
    "day_of_week",
]

TARGET_COLUMN = "target"


def load_split(
    path: str | Path,
) -> List[Dict[str, str]]:

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Dataset split not found: {path}"
        )

    with open(
        path,
        "r",
        encoding="utf-8",
        newline="",
    ) as file:

        reader = csv.DictReader(file)

        return list(reader)


def rows_to_matrix(
    rows: List[Dict[str, str]],
) -> Tuple[np.ndarray, np.ndarray]:

    if not rows:
        raise ValueError(
            "Cannot create feature matrix from empty rows."
        )

    X = np.array(
        [
            [
                float(row[feature])
                for feature in FEATURE_COLUMNS
            ]
            for row in rows
        ],
        dtype=float,
    )

    y = np.array(
        [
            int(row[TARGET_COLUMN])
            for row in rows
        ],
        dtype=int,
    )

    return X, y


def load_feature_matrices(
    train_path: str | Path,
    validation_path: str | Path,
    test_path: str | Path,
):
    """
    Load train/validation/test CSV files and convert
    them into numerical feature matrices.
    """

    train_rows = load_split(train_path)
    validation_rows = load_split(validation_path)
    test_rows = load_split(test_path)

    X_train, y_train = rows_to_matrix(
        train_rows
    )

    X_validation, y_validation = rows_to_matrix(
        validation_rows
    )

    X_test, y_test = rows_to_matrix(
        test_rows
    )

    return (
        X_train,
        y_train,
        X_validation,
        y_validation,
        X_test,
        y_test,
    )