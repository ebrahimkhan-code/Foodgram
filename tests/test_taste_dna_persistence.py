from pathlib import Path

# pyrefly: ignore [missing-import]
import pytest

from taste_dna.persistence import (
    load_taste_dna_json,
    save_taste_dna,
)
from taste_dna.schema import TasteDNA
from taste_dna.updater import update_taste_dna


def make_food():
    return {
        "food_id": "F001",
        "name": "Chicken Biryani",
        "cuisine": "Pakistani",
        "protein": "Chicken",
        "flavor": "Savory",
        "spice_level": "High",
        "base": "Rice",
        "meal_type": "Dinner",
    }


def test_save_and_load_taste_dna(tmp_path):

    dna = TasteDNA(
        user_id="U001",
        cuisine={"Pakistani": 0.5},
        protein={"Chicken": 0.3},
        flavor={"Savory": 0.7},
        spice_level={"High": 0.2},
        base={"Rice": 0.4},
        meal_type={"Dinner": 0.6},
    )

    path = tmp_path / "taste_dna.json"

    save_taste_dna(
        dna,
        path,
    )

    loaded = load_taste_dna_json(
        path,
    )

    assert loaded.user_id == "U001"
    assert loaded.cuisine["Pakistani"] == 0.5
    assert loaded.protein["Chicken"] == 0.3
    assert loaded.flavor["Savory"] == 0.7
    assert loaded.spice_level["High"] == 0.2
    assert loaded.base["Rice"] == 0.4
    assert loaded.meal_type["Dinner"] == 0.6


def test_updated_taste_dna_survives_persistence(tmp_path):

    dna = TasteDNA(
        user_id="U001",
    )

    update_taste_dna(
        taste_dna=dna,
        food=make_food(),
        interaction="like",
    )

    path = tmp_path / "taste_dna.json"

    save_taste_dna(
        dna,
        path,
    )

    loaded = load_taste_dna_json(
        path,
    )

    assert loaded.cuisine["Pakistani"] == 0.10
    assert loaded.protein["Chicken"] == 0.10
    assert loaded.flavor["Savory"] == 0.10
    assert loaded.spice_level["High"] == 0.10
    assert loaded.base["Rice"] == 0.10
    assert loaded.meal_type["Dinner"] == 0.10


def test_missing_json_file_is_rejected(tmp_path):

    path = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError):

        load_taste_dna_json(path)


def test_invalid_json_without_user_id_is_rejected(tmp_path):

    path = tmp_path / "invalid.json"

    path.write_text(
        '{"cuisine": {"Pakistani": 1.0}}',
        encoding="utf-8",
    )

    with pytest.raises(ValueError):

        load_taste_dna_json(path)

def test_reloaded_taste_dna_produces_same_recommendation_score(tmp_path):

    from recommendation.pipeline import recommend_foods

    food = make_food()

    foods = [food]

    dna = TasteDNA(
        user_id="U001",
    )

    update_taste_dna(
        taste_dna=dna,
        food=food,
        interaction="like",
    )

    original_results = recommend_foods(
        foods=foods,
        taste_dna=dna.as_dict(),
        top_k=1,
    )

    original_score = original_results[0]["score"]

    path = tmp_path / "taste_dna.json"

    save_taste_dna(
        dna,
        path,
    )

    loaded_dna = load_taste_dna_json(
        path,
    )

    loaded_results = recommend_foods(
        foods=foods,
        taste_dna=loaded_dna.as_dict(),
        top_k=1,
    )

    loaded_score = loaded_results[0]["score"]

    assert loaded_score == original_score        