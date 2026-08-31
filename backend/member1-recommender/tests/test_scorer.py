# pyrefly: ignore [missing-import]
import pytest

from recommendation.scorer import (
    score_food,
    rank_foods,
)


def test_score_food_returns_probability():

    features = [0.0] * 15

    score = score_food(features)

    assert 0.0 <= score <= 1.0


def test_score_food_requires_15_features():

    features = [0.0] * 14

    with pytest.raises(ValueError):
        score_food(features)


def test_score_food_rejects_extra_features():

    features = [0.0] * 16

    with pytest.raises(ValueError):
        score_food(features)


def test_rank_foods_returns_scores():

    foods = [
        [0.0] * 15,
        [1.0] * 15,
        [0.5] * 15,
    ]

    scores = rank_foods(foods)

    assert len(scores) == 3

    for score in scores:
        assert 0.0 <= score <= 1.0


def test_rank_foods_empty_input():

    assert rank_foods([]) == []


def test_rank_foods_requires_15_features():

    foods = [
        [0.0] * 15,
        [0.0] * 14,
    ]

    with pytest.raises(ValueError):
        rank_foods(foods)