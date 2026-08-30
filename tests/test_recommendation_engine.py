# pyrefly: ignore [missing-import]
import pytest

from recommendation.engine import (
    rank_candidates,
    get_top_recommendations,
)


FEATURES = [
    "cuisine_match",
    "protein_match",
    "flavor_match",
    "spice_level_match",
    "base_match",
    "meal_type_match",
    "taste_match_score",
    "previous_likes",
    "previous_dislikes",
    "previous_saves",
    "previous_skips",
    "previous_interactions",
    "days_since_previous_interaction",
    "hour",
    "day_of_week",
]


def make_candidate(value=0.0, food_id="F001"):
    candidate = {
        "food_id": food_id,
    }

    for feature in FEATURES:
        candidate[feature] = value

    return candidate


def test_rank_candidates_returns_results():

    candidates = [
        make_candidate(0.0, "F001"),
        make_candidate(1.0, "F002"),
    ]

    ranked = rank_candidates(candidates)

    assert len(ranked) == 2

    for candidate in ranked:
        assert "recommendation_score" in candidate
        assert 0.0 <= candidate["recommendation_score"] <= 1.0


def test_rank_candidates_sorted_descending():

    candidates = [
        make_candidate(0.0, "F001"),
        make_candidate(1.0, "F002"),
        make_candidate(0.5, "F003"),
    ]

    ranked = rank_candidates(candidates)

    scores = [
        candidate["recommendation_score"]
        for candidate in ranked
    ]

    assert scores == sorted(
        scores,
        reverse=True,
    )


def test_empty_candidates():

    assert rank_candidates([]) == []


def test_missing_feature_rejected():

    candidate = make_candidate()

    del candidate["cuisine_match"]

    with pytest.raises(ValueError):
        rank_candidates([candidate])


def test_top_k_returns_correct_number():

    candidates = [
        make_candidate(0.0, "F001"),
        make_candidate(0.2, "F002"),
        make_candidate(0.4, "F003"),
        make_candidate(0.6, "F004"),
        make_candidate(0.8, "F005"),
    ]

    recommendations = get_top_recommendations(
        candidates,
        top_k=3,
    )

    assert len(recommendations) == 3


def test_top_k_cannot_be_zero():

    with pytest.raises(ValueError):
        get_top_recommendations(
            [],
            top_k=0,
        )


def test_top_k_cannot_be_negative():

    with pytest.raises(ValueError):
        get_top_recommendations(
            [],
            top_k=-1,
        )
