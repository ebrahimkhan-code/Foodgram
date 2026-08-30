from pathlib import Path

from taste_dna.synthetic_loader import (
    load_synthetic_taste_dna,
)
from recommendation.pipeline import recommend_foods


BASE_DIR = Path(__file__).parent.parent

PREFERENCES_PATH = (
    BASE_DIR
    / "data"
    / "synthetic"
    / "user_preferences.csv"
)


def make_foods():
    return [
        {
            "food_id": "F001",
            "name": "Chicken Biryani",
            "cuisine": "Indian",
            "protein": "Chicken",
            "flavor": "Savory",
            "spice_level": "High",
            "base": "Rice",
            "meal_type": "Lunch",
        },
        {
            "food_id": "F002",
            "name": "Beef Burger",
            "cuisine": "American",
            "protein": "Beef",
            "flavor": "Savory",
            "spice_level": "Low",
            "base": "Bread",
            "meal_type": "Dinner",
        },
        {
            "food_id": "F003",
            "name": "Chicken Pasta",
            "cuisine": "Italian",
            "protein": "Chicken",
            "flavor": "Creamy",
            "spice_level": "Low",
            "base": "Pasta",
            "meal_type": "Lunch",
        },
    ]


def test_real_synthetic_user_can_get_recommendations():

    dna_by_user = load_synthetic_taste_dna(
        PREFERENCES_PATH
    )

    user_dna = dna_by_user["U001"]

    results = recommend_foods(
        foods=make_foods(),
        taste_dna=user_dna,
        top_k=3,
    )

    assert len(results) == 3


def test_recommendations_are_sorted_for_synthetic_user():

    dna_by_user = load_synthetic_taste_dna(
        PREFERENCES_PATH
    )

    user_dna = dna_by_user["U001"]

    results = recommend_foods(
        foods=make_foods(),
        taste_dna=user_dna,
        top_k=3,
    )

    scores = [
        result["score"]
        for result in results
    ]

    assert scores == sorted(
        scores,
        reverse=True,
    )


def test_multiple_synthetic_users_can_recommend():

    dna_by_user = load_synthetic_taste_dna(
        PREFERENCES_PATH
    )

    foods = make_foods()

    for user_id in ["U001", "U002", "U003", "U004"]:

        results = recommend_foods(
            foods=foods,
            taste_dna=dna_by_user[user_id],
            top_k=2,
        )

        assert len(results) == 2

        assert all(
            "food" in result and "score" in result
            for result in results
        )

def test_different_users_produce_different_scores():

    dna_by_user = load_synthetic_taste_dna(
        PREFERENCES_PATH
    )

    foods = make_foods()

    user_1_results = recommend_foods(
        foods=foods,
        taste_dna=dna_by_user["U001"],
        top_k=3,
    )

    user_2_results = recommend_foods(
        foods=foods,
        taste_dna=dna_by_user["U002"],
        top_k=3,
    )

    user_1_scores = [
        result["score"]
        for result in user_1_results
    ]

    user_2_scores = [
        result["score"]
        for result in user_2_results
    ]

    assert user_1_scores != user_2_scores        