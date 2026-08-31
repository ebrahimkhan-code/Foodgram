import csv
from pathlib import Path


BASE_DIR = Path(__file__).parent.parent

DATASET_PATH = (
    BASE_DIR
    / "data"
    / "synthetic"
    / "training_dataset.csv"
)


REQUIRED_COLUMNS = [
    "interaction_id",
    "user_id",
    "food_id",
    "cuisine",
    "protein",
    "flavor",
    "spice_level",
    "base",
    "meal_type",
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
    "target",
]


def load_dataset():

    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_PATH}"
        )

    with open(
        DATASET_PATH,
        "r",
        encoding="utf-8",
        newline="",
    ) as file:

        reader = csv.DictReader(file)
        rows = list(reader)

    return reader.fieldnames, rows


def validate_columns(columns):

    missing = [
        column
        for column in REQUIRED_COLUMNS
        if column not in columns
    ]

    if missing:
        raise AssertionError(
            f"Missing columns: {missing}"
        )


def validate_targets(rows):

    targets = {
        int(row["target"])
        for row in rows
    }

    assert targets == {0, 1}, (
        f"Expected both target classes, got {targets}"
    )


def validate_missing_values(rows):

    for row_number, row in enumerate(rows, start=2):

        for column in REQUIRED_COLUMNS:

            value = row[column].strip()

            # These fields are categorical and must exist.
            if column in {
                "interaction_id",
                "user_id",
                "food_id",
                "cuisine",
                "protein",
                "flavor",
                "spice_level",
                "base",
                "meal_type",
            }:
                assert value != "", (
                    f"Missing {column} at CSV row "
                    f"{row_number}"
                )


def validate_unique_interactions(rows):

    ids = [
        row["interaction_id"]
        for row in rows
    ]

    assert len(ids) == len(set(ids)), (
        "Duplicate interaction IDs found."
    )


def validate_ranges(rows):

    for row in rows:

        hour = int(row["hour"])
        day = int(row["day_of_week"])

        assert 0 <= hour <= 23
        assert 0 <= day <= 6

        taste_score = float(
            row["taste_match_score"]
        )

        assert -1.0 <= taste_score <= 1.0

        previous_interactions = float(
            row["previous_interactions"]
        )

        assert previous_interactions >= 0


def print_summary(rows,columns):

    positive = sum(
        int(row["target"]) == 1
        for row in rows
    )

    negative = sum(
        int(row["target"]) == 0
        for row in rows
    )

    users = {
        row["user_id"]
        for row in rows
    }

    foods = {
        row["food_id"]
        for row in rows
    }

    print()
    print("Dataset validation successful.")
    print()
    print(f"Rows:             {len(rows)}")
    print(f"Columns:          {len(columns)}")
    print(f"Users:            {len(users)}")
    print(f"Foods:            {len(foods)}")
    print(f"Positive targets: {positive}")
    print(f"Negative targets: {negative}")

    positive_rate = positive / len(rows)

    print(
        f"Positive rate:    {positive_rate:.2%}"
    )


def main():

    columns, rows = load_dataset()

    validate_columns(columns)
    validate_targets(rows)
    validate_missing_values(rows)
    validate_unique_interactions(rows)
    validate_ranges(rows)

    print_summary(rows,columns)


if __name__ == "__main__":
    main()