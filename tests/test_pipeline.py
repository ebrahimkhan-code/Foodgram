from datetime import datetime

from recommendation.pipeline import recommend_foods


def sample_foods():
    return [
        {
            "food_id": "F001",
            "name": "Chicken Biryani",
            "cuisine": "Pakistani",
            "protein": "Chicken",
            "flavor": "Savory",
            "spice_level": "High",
            "base": "Rice",
            "meal_type": "Dinner",
        },
        {
            "food_id": "F002",
            "name": "Chinese Noodles",
            "cuisine": "Chinese",
            "protein": "Chicken",
            "flavor": "Savory",
            "spice_level": "Medium",
            "base": "Noodles",
            "meal_type": "Dinner",
        },
        {
            "food_id": "F003",
            "name": "Italian Pasta",
            "cuisine": "Italian",
            "protein": "Vegetarian",
            "flavor": "Creamy",
            "spice_level": "Low",
            "base": "Pasta",
            "meal_type": "Dinner",
        },
    ]


def sample_dna():
    return {
        "cuisine": {
            "Pakistani": 1.0,
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


def test_recommend_foods_returns_results():

    results = recommend_foods(
        foods=sample_foods(),
        taste_dna=sample_dna(),
        top_k=2,
    )

    assert len(results) == 2


def test_recommend_foods_are_sorted():

    results = recommend_foods(
        foods=sample_foods(),
        taste_dna=sample_dna(),
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


def test_recommendation_contains_food_and_score():

    results = recommend_foods(
        foods=sample_foods(),
        taste_dna=sample_dna(),
        top_k=1,
    )

    result = results[0]

    assert "food" in result
    assert "score" in result

    assert isinstance(
        result["score"],
        float,
    )


def test_recommendation_score_is_probability():

    results = recommend_foods(
        foods=sample_foods(),
        taste_dna=sample_dna(),
        top_k=3,
    )

    for result in results:

        assert 0.0 <= result["score"] <= 1.0


def test_empty_food_catalog():

    results = recommend_foods(
        foods=[],
        taste_dna=sample_dna(),
    )

    assert results == []


def test_top_k_cannot_be_zero():

    try:
        recommend_foods(
            foods=sample_foods(),
            taste_dna=sample_dna(),
            top_k=0,
        )
        assert False
    except ValueError:
        assert True


def test_top_k_cannot_be_negative():

    try:
        recommend_foods(
            foods=sample_foods(),
            taste_dna=sample_dna(),
            top_k=-1,
        )
        assert False
    except ValueError:
        assert True