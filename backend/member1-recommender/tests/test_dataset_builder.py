from training.dataset_builder import (
    build_training_dataset,
    calculate_taste_features,
    load_csv,
)

from pathlib import Path


DATA_DIR = (
    Path(__file__).parent.parent
    / "data"
    / "synthetic"
)

FOODS_PATH = DATA_DIR / "foods.csv"
INTERACTIONS_PATH = DATA_DIR / "interactions.csv"


def test_build_training_dataset():

    rows = build_training_dataset(
        FOODS_PATH,
        INTERACTIONS_PATH,
    )

    assert len(rows) > 0


def test_training_row_structure():

    rows = build_training_dataset(
        FOODS_PATH,
        INTERACTIONS_PATH,
    )

    row = rows[0]

    expected_columns = [
        "interaction_id",
        "user_id",
        "food_id",
        "cuisine",
        "protein",
        "flavor",
        "spice_level",
        "base",
        "meal_type",
        "hour",
        "day_of_week",
        "target",
    ]

    for column in expected_columns:
        assert column in row


def test_target_is_binary():

    rows = build_training_dataset(
        FOODS_PATH,
        INTERACTIONS_PATH,
    )

    targets = {
        row["target"]
        for row in rows
    }

    assert targets.issubset({0, 1})
    assert len(targets) == 2


def test_context_features():

    rows = build_training_dataset(
        FOODS_PATH,
        INTERACTIONS_PATH,
    )

    for row in rows:
        assert 0 <= row["hour"] <= 23
        assert 0 <= row["day_of_week"] <= 6

def test_taste_features_are_added():

    foods = load_csv(FOODS_PATH)

    food = foods[0]

    dna = {
        "cuisine": {
            food["cuisine"]: 1.0
        },
        "protein": {
            food["protein"]: 1.0
        },
    }

    features = calculate_taste_features(
        food,
        dna,
    )

    assert features["cuisine_match"] == 1.0
    assert features["protein_match"] == 1.0

    assert features["flavor_match"] == 0.0

    assert "taste_match_score" in features


def test_training_dataset_contains_taste_features():

    dna = {
        "U001": {
            "cuisine": {
                "Pakistani": 1.0
            },
            "protein": {
                "Chicken": 1.0
            },
        }
    }

    rows = build_training_dataset(
        FOODS_PATH,
        INTERACTIONS_PATH,
        dna,
    )

    row = rows[0]

    expected_features = [
        "cuisine_match",
        "protein_match",
        "flavor_match",
        "spice_level_match",
        "base_match",
        "meal_type_match",
        "taste_match_score",
    ]

    for feature in expected_features:
        assert feature in row


def test_training_dataset_contains_history_features():

    rows = build_training_dataset(
        FOODS_PATH,
        INTERACTIONS_PATH,
    )

    row = rows[0]

    expected_features = [
        "previous_likes",
        "previous_dislikes",
        "previous_saves",
        "previous_skips",
        "previous_interactions",
        "days_since_previous_interaction",
    ]

    for feature in expected_features:
        assert feature in row


def test_training_dataset_contains_complete_feature_set():

    dna = {
        "U001": {
            "cuisine": {
                "Pakistani": 1.0
            },
            "protein": {
                "Chicken": 1.0
            },
        }
    }

    rows = build_training_dataset(
        FOODS_PATH,
        INTERACTIONS_PATH,
        dna,
    )

    row = rows[0]

    expected_features = [
        # Food
        "cuisine",
        "protein",
        "flavor",
        "spice_level",
        "base",
        "meal_type",

        # Taste DNA
        "cuisine_match",
        "protein_match",
        "flavor_match",
        "spice_level_match",
        "base_match",
        "meal_type_match",
        "taste_match_score",

        # History
        "previous_likes",
        "previous_dislikes",
        "previous_saves",
        "previous_skips",
        "previous_interactions",
        "days_since_previous_interaction",

        # Context
        "hour",
        "day_of_week",

        # Target
        "target",
    ]

    for feature in expected_features:
        assert feature in row


def test_first_interaction_has_zero_history():

    interactions = [
        {
            "interaction_id": "I001",
            "user_id": "U001",
            "interaction_type": "like",
            "rating": "",
            "timestamp": "2026-01-01T10:00:00",
        }
    ]

    # Create a temporary food CSV.
    import tempfile

    foods_csv = (
        "food_id,name,cuisine,protein,flavor,"
        "spice_level,base,meal_type\n"
        "F001,Biryani,Pakistani,Chicken,"
        "Savory,High,Rice,Dinner\n"
    )

    interactions_csv = (
        "interaction_id,user_id,food_id,"
        "interaction_type,rating,timestamp\n"
        "I001,U001,F001,like,,2026-01-01T10:00:00\n"
    )

    with tempfile.TemporaryDirectory() as temp_dir:

        temp_path = Path(temp_dir)

        foods_path = temp_path / "foods.csv"
        interactions_path = temp_path / "interactions.csv"

        foods_path.write_text(
            foods_csv,
            encoding="utf-8",
        )

        interactions_path.write_text(
            interactions_csv,
            encoding="utf-8",
        )

        rows = build_training_dataset(
            foods_path,
            interactions_path,
        )

    row = rows[0]

    assert row["previous_likes"] == 0
    assert row["previous_dislikes"] == 0
    assert row["previous_saves"] == 0
    assert row["previous_skips"] == 0
    assert row["previous_interactions"] == 0