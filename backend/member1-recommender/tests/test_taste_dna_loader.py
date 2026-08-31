from pathlib import Path

# pyrefly: ignore [missing-import]
import pytest

from taste_dna.loader import load_taste_dna


DATA_PATH = (
    Path(__file__).parent.parent
    / "data"
    / "synthetic"
    / "user_preferences.csv"
)


def test_load_taste_dna():

    dna = load_taste_dna(
        DATA_PATH,
        "U001",
    )

    assert dna.user_id == "U001"

    assert dna.cuisine
    assert dna.protein
    assert dna.flavor
    assert dna.spice_level
    assert dna.base
    assert dna.meal_type


def test_loaded_preferences_have_positive_values():

    dna = load_taste_dna(
        DATA_PATH,
        "U001",
    )

    for preferences in [
        dna.cuisine,
        dna.protein,
        dna.flavor,
        dna.spice_level,
        dna.base,
        dna.meal_type,
    ]:

        for value in preferences.values():
            assert value == 1.0


def test_unknown_user_is_rejected():

    with pytest.raises(ValueError):

        load_taste_dna(
            DATA_PATH,
            "U999",
        )


def test_missing_file_is_rejected():

    with pytest.raises(FileNotFoundError):

        load_taste_dna(
            "does_not_exist.csv",
            "U001",
        )