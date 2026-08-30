import csv
from pathlib import Path

from training.dataset_builder import build_training_dataset
from taste_dna.synthetic_loader import load_synthetic_taste_dna


BASE_DIR = Path(__file__).parent.parent

FOODS_PATH = (
    BASE_DIR
    / "data"
    / "synthetic"
    / "foods.csv"
)

INTERACTIONS_PATH = (
    BASE_DIR
    / "data"
    / "synthetic"
    / "interactions.csv"
)

PREFERENCES_PATH = (
    BASE_DIR
    / "data"
    / "synthetic"
    / "user_preferences.csv"
)

OUTPUT_PATH = (
    BASE_DIR
    / "data"
    / "synthetic"
    / "training_dataset.csv"
)


def export_training_dataset():
    """
    Build and save the complete ML training dataset.
    """

    taste_dna_by_user = load_synthetic_taste_dna(
        PREFERENCES_PATH
    )

    rows = build_training_dataset(
        FOODS_PATH,
        INTERACTIONS_PATH,
        taste_dna_by_user=taste_dna_by_user,
    )

    if not rows:
        raise ValueError(
            "Training dataset is empty."
        )

    fieldnames = list(rows[0].keys())

    with open(
        OUTPUT_PATH,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)

    print(
        f"Training dataset exported to: {OUTPUT_PATH}"
    )

    print(f"Rows: {len(rows)}")
    print(f"Columns: {len(fieldnames)}")


if __name__ == "__main__":
    export_training_dataset()