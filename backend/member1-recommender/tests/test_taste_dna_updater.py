# pyrefly: ignore [missing-import]
import pytest

from taste_dna.schema import TasteDNA
from taste_dna.updater import (
    INTERACTION_UPDATES,
    clamp_preference,
    update_taste_dna,
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


def make_dna():
    return TasteDNA(
        user_id="U001",
    )


def test_like_increases_all_food_preferences():

    dna = make_dna()
    food = make_food()

    update_taste_dna(
        dna,
        food,
        "like",
    )

    for attribute in [
        "cuisine",
        "protein",
        "flavor",
        "spice_level",
        "base",
        "meal_type",
    ]:
        value = food[attribute]

        assert getattr(dna, attribute)[value] == 0.10


def test_dislike_decreases_all_food_preferences():

    dna = make_dna()
    food = make_food()

    update_taste_dna(
        dna,
        food,
        "dislike",
    )

    for attribute in [
        "cuisine",
        "protein",
        "flavor",
        "spice_level",
        "base",
        "meal_type",
    ]:
        value = food[attribute]

        assert getattr(dna, attribute)[value] == -0.15


def test_save_has_stronger_positive_update_than_like():

    dna = make_dna()
    food = make_food()

    update_taste_dna(
        dna,
        food,
        "like",
    )

    like_value = dna.cuisine["Pakistani"]

    dna = make_dna()

    update_taste_dna(
        dna,
        food,
        "save",
    )

    save_value = dna.cuisine["Pakistani"]

    assert save_value > like_value


def test_skip_has_small_negative_update():

    dna = make_dna()
    food = make_food()

    update_taste_dna(
        dna,
        food,
        "skip",
    )

    assert dna.cuisine["Pakistani"] == -0.05


def test_repeated_likes_are_accumulated():

    dna = make_dna()
    food = make_food()

    update_taste_dna(
        dna,
        food,
        "like",
    )

    update_taste_dna(
        dna,
        food,
        "like",
    )

    assert dna.cuisine["Pakistani"] == 0.20
    assert dna.protein["Chicken"] == 0.20


def test_preference_cannot_exceed_one():

    dna = TasteDNA(
        user_id="U001",
        cuisine={
            "Pakistani": 0.95,
        },
    )

    food = make_food()

    update_taste_dna(
        dna,
        food,
        "like",
    )

    assert dna.cuisine["Pakistani"] == 1.0


def test_preference_cannot_go_below_negative_one():

    dna = TasteDNA(
        user_id="U001",
        cuisine={
            "Pakistani": -0.95,
        },
    )

    food = make_food()

    update_taste_dna(
        dna,
        food,
        "dislike",
    )

    assert dna.cuisine["Pakistani"] == -1.0


def test_existing_preferences_are_updated():

    dna = TasteDNA(
        user_id="U001",
        cuisine={
            "Pakistani": 0.5,
        },
        protein={
            "Chicken": -0.2,
        },
    )

    food = make_food()

    update_taste_dna(
        dna,
        food,
        "like",
    )

    assert dna.cuisine["Pakistani"] == 0.6
    assert dna.protein["Chicken"] == -0.1


def test_spice_level_is_updated():

    dna = make_dna()
    food = make_food()

    update_taste_dna(
        dna,
        food,
        "like",
    )

    assert dna.spice_level["High"] == 0.10


def test_unknown_interaction_is_rejected():

    dna = make_dna()
    food = make_food()

    with pytest.raises(ValueError):
        update_taste_dna(
            dna,
            food,
            "unknown",
        )


def test_interaction_names_are_case_insensitive():

    dna = make_dna()
    food = make_food()

    update_taste_dna(
        dna,
        food,
        "LIKE",
    )

    assert dna.cuisine["Pakistani"] == 0.10


def test_empty_food_attribute_is_ignored():

    dna = make_dna()

    food = make_food()
    food["flavor"] = ""

    update_taste_dna(
        dna,
        food,
        "like",
    )

    assert dna.flavor == {}


def test_missing_food_attribute_does_not_break_update():

    dna = make_dna()

    food = make_food()
    del food["base"]

    update_taste_dna(
        dna,
        food,
        "like",
    )

    assert dna.cuisine["Pakistani"] == 0.10
    assert dna.base == {}


def test_clamp_preference():

    assert clamp_preference(2.0) == 1.0
    assert clamp_preference(-2.0) == -1.0
    assert clamp_preference(0.5) == 0.5


def test_interaction_update_values():

    assert INTERACTION_UPDATES["like"] == 0.10
    assert INTERACTION_UPDATES["save"] == 0.15
    assert INTERACTION_UPDATES["dislike"] == -0.15
    assert INTERACTION_UPDATES["skip"] == -0.05