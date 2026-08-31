from datetime import datetime

from recommendation.feature_builder import (
    build_recommendation_features,
)


def sample_food():
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


def test_feature_builder_returns_15_features():

    features = build_recommendation_features(
        food=sample_food(),
        taste_dna=sample_dna(),
    )

    assert len(features) == 15


def test_feature_builder_returns_numeric_features():

    features = build_recommendation_features(
        food=sample_food(),
        taste_dna=sample_dna(),
    )

    assert all(
        isinstance(value, (int, float))
        for value in features.values()
    )


def test_feature_builder_matches_taste_preferences():

    features = build_recommendation_features(
        food=sample_food(),
        taste_dna=sample_dna(),
    )

    assert features["cuisine_match"] == 1.0
    assert features["protein_match"] == 1.0
    assert features["flavor_match"] == 1.0
    assert features["spice_level_match"] == 1.0
    assert features["base_match"] == 1.0
    assert features["meal_type_match"] == 1.0

    assert features["taste_match_score"] == 1.0


def test_feature_builder_uses_history():

    history = {
        "previous_likes": 5,
        "previous_dislikes": 1,
        "previous_saves": 3,
        "previous_skips": 2,
        "previous_interactions": 11,
        "days_since_previous_interaction": 4,
    }

    features = build_recommendation_features(
        food=sample_food(),
        taste_dna=sample_dna(),
        history=history,
    )

    assert features["previous_likes"] == 5.0
    assert features["previous_dislikes"] == 1.0
    assert features["previous_saves"] == 3.0
    assert features["previous_skips"] == 2.0
    assert features["previous_interactions"] == 11.0
    assert features["days_since_previous_interaction"] == 4.0


def test_feature_builder_uses_timestamp():

    timestamp = datetime(
        2026,
        8,
        29,
        19,
        30,
    )

    features = build_recommendation_features(
        food=sample_food(),
        taste_dna=sample_dna(),
        timestamp=timestamp,
    )

    assert features["hour"] == 19.0
    assert features["day_of_week"] == 5.0