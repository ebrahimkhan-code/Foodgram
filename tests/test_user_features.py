from taste_dna.schema import TasteDNA

from recommendation.user_features import (
    calculate_attribute_match,
    calculate_taste_features,
    build_user_food_features,
)


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


def make_history():
    return {
        "previous_likes": 3,
        "previous_dislikes": 1,
        "previous_saves": 2,
        "previous_skips": 1,
        "previous_interactions": 7,
        "days_since_previous_interaction": 4,
    }


def test_matching_attribute_returns_preference():

    food = make_food()

    dna = TasteDNA(
        user_id="U001",
        cuisine={
            "Pakistani": 1.0,
        },
    )

    result = calculate_attribute_match(
        food,
        dna,
        "cuisine",
    )

    assert result == 1.0


def test_disliked_attribute_returns_negative_preference():

    food = make_food()

    dna = TasteDNA(
        user_id="U001",
        cuisine={
            "Pakistani": -1.0,
        },
    )

    result = calculate_attribute_match(
        food,
        dna,
        "cuisine",
    )

    assert result == -1.0


def test_unknown_attribute_returns_zero():

    food = make_food()

    dna = TasteDNA(
        user_id="U001",
    )

    result = calculate_attribute_match(
        food,
        dna,
        "cuisine",
    )

    assert result == 0.0


def test_spice_level_maps_to_spice():

    food = make_food()

    dna = TasteDNA(
        user_id="U001",
        spice_level={
            "High": 1.0,
        },
    )

    result = calculate_attribute_match(
        food,
        dna,
        "spice_level",
    )

    assert result == 1.0


def test_all_taste_features_are_calculated():

    food = make_food()

    dna = TasteDNA(
        user_id="U001",

        cuisine={
            "Pakistani": 1.0,
        },

        protein={
            "Chicken": 1.0,
        },

        flavor={
            "Savory": 1.0,
        },

        spice_level={
            "High": 1.0,
        },

        base={
            "Rice": 1.0,
        },

        meal_type={
            "Dinner": 1.0,
        },
    )

    features = calculate_taste_features(
        food,
        dna,
    )

    assert features["cuisine_match"] == 1.0
    assert features["protein_match"] == 1.0
    assert features["flavor_match"] == 1.0
    assert features["spice_level_match"] == 1.0
    assert features["base_match"] == 1.0
    assert features["meal_type_match"] == 1.0

    assert features["taste_match_score"] == 1.0


def test_taste_match_score_is_average():

    food = make_food()

    dna = TasteDNA(
        user_id="U001",

        cuisine={
            "Pakistani": 1.0,
        },

        protein={
            "Chicken": 1.0,
        },

        flavor={
            "Savory": 1.0,
        },
    )

    features = calculate_taste_features(
        food,
        dna,
    )

    assert features["taste_match_score"] == 0.5


def test_build_user_food_features_returns_15_features():

    food = make_food()

    dna = TasteDNA(
        user_id="U001",
        cuisine={
            "Pakistani": 1.0,
        },
    )

    history = make_history()

    features = build_user_food_features(
        food=food,
        taste_dna=dna,
        historical_features=history,
        hour=20,
        day_of_week=5,
    )

    assert len(features) == 15


def test_build_user_food_features_preserves_feature_order():

    food = make_food()

    dna = TasteDNA(
        user_id="U001",

        cuisine={
            "Pakistani": 1.0,
        },

        protein={
            "Chicken": 1.0,
        },

        flavor={
            "Savory": 1.0,
        },

        spice_level={
            "High": 1.0,
        },

        base={
            "Rice": 1.0,
        },

        meal_type={
            "Dinner": 1.0,
        },
    )

    history = make_history()

    features = build_user_food_features(
        food=food,
        taste_dna=dna,
        historical_features=history,
        hour=20,
        day_of_week=5,
    )

    expected = [
        1.0,       # cuisine_match
        1.0,       # protein_match
        1.0,       # flavor_match
        1.0,       # spice_level_match
        1.0,       # base_match
        1.0,       # meal_type_match
        1.0,       # taste_match_score

        3,         # previous_likes
        1,         # previous_dislikes
        2,         # previous_saves
        1,         # previous_skips
        7,         # previous_interactions
        4,         # days_since_previous_interaction

        20.0,      # hour
        5.0,       # day_of_week
    ]

    assert features == expected


def test_taste_dna_changes_feature_vector():

    food = make_food()

    positive_dna = TasteDNA(
        user_id="U001",
        cuisine={
            "Pakistani": 1.0,
        },
    )

    negative_dna = TasteDNA(
        user_id="U002",
        cuisine={
            "Pakistani": -1.0,
        },
    )

    history = make_history()

    positive_features = build_user_food_features(
        food=food,
        taste_dna=positive_dna,
        historical_features=history,
        hour=20,
        day_of_week=5,
    )

    negative_features = build_user_food_features(
        food=food,
        taste_dna=negative_dna,
        historical_features=history,
        hour=20,
        day_of_week=5,
    )

    assert positive_features[0] == 1.0
    assert negative_features[0] == -1.0

    assert positive_features != negative_features