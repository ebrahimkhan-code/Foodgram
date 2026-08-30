from pathlib import Path

# pyrefly: ignore [missing-import]
import numpy as np
# pyrefly: ignore [missing-import]
import pytest

from features.food_features import (
    CATEGORICAL_COLUMNS,
    FoodFeatureEncoder,
    load_foods,
)


FOODS_PATH = (
    Path(__file__).parent.parent
    / "data"
    / "synthetic"
    / "foods.csv"
)


def test_load_foods():

    foods = load_foods(FOODS_PATH)

    assert len(foods) == 100

    first_food = foods[0]

    assert first_food["food_id"]
    assert first_food["name"]
    assert first_food["cuisine"]
    assert first_food["protein"]
    assert first_food["flavor"]
    assert first_food["spice_level"]
    assert first_food["base"]
    assert first_food["meal_type"]


def test_food_ids_are_unique():

    foods = load_foods(FOODS_PATH)

    food_ids = [food["food_id"] for food in foods]

    assert len(food_ids) == len(set(food_ids))


def test_food_feature_encoding():

    foods = load_foods(FOODS_PATH)

    encoder = FoodFeatureEncoder()

    features = encoder.fit_transform(foods)

    assert isinstance(features, np.ndarray)

    assert features.shape[0] == len(foods)

    assert features.shape[1] > 0

    assert features.dtype.kind == "f"


def test_feature_names_match_feature_matrix():

    foods = load_foods(FOODS_PATH)

    encoder = FoodFeatureEncoder()

    features = encoder.fit_transform(foods)
    feature_names = encoder.get_feature_names()

    assert features.shape[1] == len(feature_names)


def test_unknown_category_does_not_break_encoder():

    foods = load_foods(FOODS_PATH)

    encoder = FoodFeatureEncoder()
    encoder.fit(foods)

    new_food = dict(foods[0])
    new_food["cuisine"] = "UnknownCuisine"

    features = encoder.transform([new_food])

    assert features.shape[0] == 1
    assert features.shape[1] == len(encoder.get_feature_names())


def test_transform_before_fit_fails():

    foods = load_foods(FOODS_PATH)

    encoder = FoodFeatureEncoder()

    with pytest.raises(RuntimeError):
        encoder.transform(foods)