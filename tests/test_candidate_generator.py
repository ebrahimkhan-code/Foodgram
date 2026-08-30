from pathlib import Path

# pyrefly: ignore [missing-import]
import pytest

from candidate_generation.generator import generate_candidates
from features.food_features import load_foods


FOODS_PATH = (
    Path(__file__).parent.parent
    / "data"
    / "synthetic"
    / "foods.csv"
)


def sample_dna():
    return {
        "cuisine": {
            "Pakistani": 1.0,
            "Chinese": 0.5,
        },
        "protein": {
            "Chicken": 1.0,
        },
        "flavor": {
            "Savory": 1.0,
        },
        "spice_level": {
            "High": 1.0,
        },
        "base": {
            "Rice": 1.0,
        },
        "meal_type": {
            "Dinner": 1.0,
        },
    }


def test_generate_candidates():

    foods = load_foods(FOODS_PATH)

    candidates = generate_candidates(
        foods,
        sample_dna(),
        top_k=10,
    )

    assert len(candidates) == 10


def test_candidates_are_sorted():

    foods = load_foods(FOODS_PATH)

    candidates = generate_candidates(
        foods,
        sample_dna(),
        top_k=20,
    )

    scores = [
        candidate["similarity_score"]
        for candidate in candidates
    ]

    assert scores == sorted(
        scores,
        reverse=True,
    )


def test_candidate_structure():

    foods = load_foods(FOODS_PATH)

    candidates = generate_candidates(
        foods,
        sample_dna(),
        top_k=5,
    )

    for candidate in candidates:

        assert "food_id" in candidate
        assert "name" in candidate
        assert "similarity_score" in candidate

        assert 0.0 <= candidate["similarity_score"] <= 1.0


def test_top_k_cannot_be_zero():

    foods = load_foods(FOODS_PATH)

    with pytest.raises(ValueError):

        generate_candidates(
            foods,
            sample_dna(),
            top_k=0,
        )


def test_top_k_cannot_be_negative():

    foods = load_foods(FOODS_PATH)

    with pytest.raises(ValueError):

        generate_candidates(
            foods,
            sample_dna(),
            top_k=-5,
        )


def test_empty_food_catalog():

    candidates = generate_candidates(
        [],
        sample_dna(),
        top_k=10,
    )

    assert candidates == []


def test_top_k_larger_than_catalog():

    foods = load_foods(FOODS_PATH)

    candidates = generate_candidates(
        foods,
        sample_dna(),
        top_k=500,
    )

    assert len(candidates) == len(foods)