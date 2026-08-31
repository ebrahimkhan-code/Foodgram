from pathlib import Path

from taste_dna.synthetic_loader import (
    load_synthetic_taste_dna,
)


BASE_DIR = Path(__file__).parent.parent

PREFERENCES_PATH = (
    BASE_DIR
    / "data"
    / "synthetic"
    / "user_preferences.csv"
)


def test_load_synthetic_taste_dna():

    dna_by_user = load_synthetic_taste_dna(
        PREFERENCES_PATH
    )

    assert len(dna_by_user) == 50

    assert "U001" in dna_by_user

    user_dna = dna_by_user["U001"]

    assert "cuisine" in user_dna
    assert "protein" in user_dna
    assert "flavor" in user_dna
    assert "spice_level" in user_dna
    assert "base" in user_dna
    assert "meal_type" in user_dna


def test_synthetic_taste_dna_contains_preferences():

    dna_by_user = load_synthetic_taste_dna(
        PREFERENCES_PATH
    )

    user_dna = dna_by_user["U001"]

    assert len(user_dna["cuisine"]) > 0
    assert len(user_dna["protein"]) > 0
    assert len(user_dna["flavor"]) > 0
    assert len(user_dna["spice_level"]) > 0
    assert len(user_dna["base"]) > 0
    assert len(user_dna["meal_type"]) > 0