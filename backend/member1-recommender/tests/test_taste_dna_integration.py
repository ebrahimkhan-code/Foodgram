from recommendation.feature_builder import (
    build_recommendation_features,
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

def test_updated_taste_dna_changes_recommendation_features():
    food = make_food()

    dna = TasteDNA(
        user_id="U001",
    )

    initial_features = build_recommendation_features(
        food=food,
        taste_dna=dna.as_dict(),
    )

    update_taste_dna(
        taste_dna=dna,
        food=food,
        interaction="like",
    )

    updated_features = build_recommendation_features(
        food=food,
        taste_dna=dna.as_dict(),
    )

    assert (
        updated_features["cuisine_match"]
        > initial_features["cuisine_match"]
    )

    assert (
        updated_features["protein_match"]
        > initial_features["protein_match"]
    )

    assert (
        updated_features["flavor_match"]
        > initial_features["flavor_match"]
    )

    assert (
        updated_features["spice_level_match"]
        > initial_features["spice_level_match"]
    )

    assert (
        updated_features["base_match"]
        > initial_features["base_match"]
    )

    assert (
        updated_features["meal_type_match"]
        > initial_features["meal_type_match"]
    )

    assert (
        updated_features["taste_match_score"]
        > initial_features["taste_match_score"]
    )

def test_updated_taste_dna_changes_recommendation_score():
    from recommendation.scorer import score_food
    from training.feature_matrix import FEATURE_COLUMNS

    food = make_food()

    dna = TasteDNA(
        user_id="U001",
    )

    initial_features = build_recommendation_features(
        food=food,
        taste_dna=dna.as_dict(),
    )

    initial_vector = [
        initial_features[feature]
        for feature in FEATURE_COLUMNS
    ]

    initial_score = score_food(
        initial_vector
    )

    update_taste_dna(
        taste_dna=dna,
        food=food,
        interaction="like",
    )

    updated_features = build_recommendation_features(
        food=food,
        taste_dna=dna.as_dict(),
    )

    updated_vector = [
        updated_features[feature]
        for feature in FEATURE_COLUMNS
    ]

    updated_score = score_food(
        updated_vector
    )

    assert updated_score != initial_score


def test_updated_taste_dna_changes_pipeline_recommendation():
    from recommendation.pipeline import recommend_foods

    foods = [
        make_food(),
        {
            "food_id": "F002",
            "name": "Chicken Karahi",
            "cuisine": "Pakistani",
            "protein": "Chicken",
            "flavor": "Savory",
            "spice_level": "High",
            "base": "Gravy",
            "meal_type": "Dinner",
        },
    ]

    dna = TasteDNA(
        user_id="U001",
    )

    initial_results = recommend_foods(
        foods=foods,
        taste_dna=dna.as_dict(),
        top_k=2,
    )

    initial_scores = [
        result["score"]
        for result in initial_results
    ]

    update_taste_dna(
        taste_dna=dna,
        food=foods[0],
        interaction="like",
    )

    updated_results = recommend_foods(
        foods=foods,
        taste_dna=dna.as_dict(),
        top_k=2,
    )

    updated_scores = [
        result["score"]
        for result in updated_results
    ]

    assert updated_scores != initial_scores


def test_complete_taste_learning_cycle():
    from recommendation.pipeline import recommend_foods

    foods = [
        make_food(),
        {
            "food_id": "F002",
            "name": "Chicken Karahi",
            "cuisine": "Pakistani",
            "protein": "Chicken",
            "flavor": "Savory",
            "spice_level": "High",
            "base": "Gravy",
            "meal_type": "Dinner",
        },
        {
            "food_id": "F003",
            "name": "Beef Burger",
            "cuisine": "American",
            "protein": "Beef",
            "flavor": "Savory",
            "spice_level": "Low",
            "base": "Bread",
            "meal_type": "Dinner",
        },
    ]

    dna = TasteDNA(
        user_id="U001",
    )

    # Initial recommendation
    initial_results = recommend_foods(
        foods=foods,
        taste_dna=dna.as_dict(),
        top_k=3,
    )

    assert len(initial_results) == 3

    initial_scores = {
        result["food"]["food_id"]: result["score"]
        for result in initial_results
    }

    # User likes Chicken Biryani
    update_taste_dna(
        taste_dna=dna,
        food=foods[0],
        interaction="like",
    )

    # Recommendation after interaction
    updated_results = recommend_foods(
        foods=foods,
        taste_dna=dna.as_dict(),
        top_k=3,
    )

    assert len(updated_results) == 3

    updated_scores = {
        result["food"]["food_id"]: result["score"]
        for result in updated_results
    }

    # The liked food's score should change.
    assert (
        updated_scores["F001"]
        != initial_scores["F001"]
    )

    # Taste DNA should contain the learned preferences.
    assert dna.cuisine["Pakistani"] == 0.10
    assert dna.protein["Chicken"] == 0.10
    assert dna.flavor["Savory"] == 0.10
    assert dna.spice_level["High"] == 0.10
    assert dna.base["Rice"] == 0.10
    assert dna.meal_type["Dinner"] == 0.10

def test_liked_food_score_increases():
    from recommendation.scorer import score_food
    from training.feature_matrix import FEATURE_COLUMNS

    food = make_food()

    dna = TasteDNA(
        user_id="U001",
    )

    initial_features = build_recommendation_features(
        food=food,
        taste_dna=dna.as_dict(),
    )

    initial_vector = [
        initial_features[feature]
        for feature in FEATURE_COLUMNS
    ]

    initial_score = score_food(
        initial_vector
    )

    update_taste_dna(
        taste_dna=dna,
        food=food,
        interaction="like",
    )

    updated_features = build_recommendation_features(
        food=food,
        taste_dna=dna.as_dict(),
    )

    updated_vector = [
        updated_features[feature]
        for feature in FEATURE_COLUMNS
    ]

    updated_score = score_food(
        updated_vector
    )

    assert updated_score > initial_score

def test_disliked_food_score_decreases():
    from recommendation.scorer import score_food
    from training.feature_matrix import FEATURE_COLUMNS

    food = make_food()

    dna = TasteDNA(
        user_id="U001",
    )

    initial_features = build_recommendation_features(
        food=food,
        taste_dna=dna.as_dict(),
    )

    initial_vector = [
        initial_features[feature]
        for feature in FEATURE_COLUMNS
    ]

    initial_score = score_food(
        initial_vector
    )

    update_taste_dna(
        taste_dna=dna,
        food=food,
        interaction="dislike",
    )

    updated_features = build_recommendation_features(
        food=food,
        taste_dna=dna.as_dict(),
    )

    updated_vector = [
        updated_features[feature]
        for feature in FEATURE_COLUMNS
    ]

    updated_score = score_food(
        updated_vector
    )

    assert updated_score < initial_score

def test_saved_food_score_increases():
    from recommendation.scorer import score_food
    from training.feature_matrix import FEATURE_COLUMNS

    food = make_food()

    dna = TasteDNA(
        user_id="U001",
    )

    initial_features = build_recommendation_features(
        food=food,
        taste_dna=dna.as_dict(),
    )

    initial_vector = [
        initial_features[feature]
        for feature in FEATURE_COLUMNS
    ]

    initial_score = score_food(initial_vector)

    update_taste_dna(
        taste_dna=dna,
        food=food,
        interaction="save",
    )

    updated_features = build_recommendation_features(
        food=food,
        taste_dna=dna.as_dict(),
    )

    updated_vector = [
        updated_features[feature]
        for feature in FEATURE_COLUMNS
    ]

    updated_score = score_food(updated_vector)

    assert updated_score > initial_score


def test_skipped_food_score_decreases():
    from recommendation.scorer import score_food
    from training.feature_matrix import FEATURE_COLUMNS

    food = make_food()

    dna = TasteDNA(
        user_id="U001",
    )

    initial_features = build_recommendation_features(
        food=food,
        taste_dna=dna.as_dict(),
    )

    initial_vector = [
        initial_features[feature]
        for feature in FEATURE_COLUMNS
    ]

    initial_score = score_food(initial_vector)

    update_taste_dna(
        taste_dna=dna,
        food=food,
        interaction="skip",
    )

    updated_features = build_recommendation_features(
        food=food,
        taste_dna=dna.as_dict(),
    )

    updated_vector = [
        updated_features[feature]
        for feature in FEATURE_COLUMNS
    ]

    updated_score = score_food(updated_vector)

    assert updated_score < initial_score

def test_disliked_food_score_decreases():
    from recommendation.scorer import score_food
    from training.feature_matrix import FEATURE_COLUMNS

    food = make_food()

    dna = TasteDNA(
        user_id="U001",
    )

    initial_features = build_recommendation_features(
        food=food,
        taste_dna=dna.as_dict(),
    )

    initial_vector = [
        initial_features[feature]
        for feature in FEATURE_COLUMNS
    ]

    initial_score = score_food(
        initial_vector
    )

    update_taste_dna(
        taste_dna=dna,
        food=food,
        interaction="dislike",
    )

    updated_features = build_recommendation_features(
        food=food,
        taste_dna=dna.as_dict(),
    )

    updated_vector = [
        updated_features[feature]
        for feature in FEATURE_COLUMNS
    ]

    updated_score = score_food(
        updated_vector
    )

    assert updated_score < initial_score    
