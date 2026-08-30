from datetime import datetime

# pyrefly: ignore [missing-import]
import pytest

from recommendation.history import (
    build_user_history,
)


def make_interactions():
    return [
        {
            "interaction_id": "I001",
            "user_id": "U001",
            "food_id": "F001",
            "interaction_type": "like",
            "timestamp": "2026-01-01T10:00:00",
        },
        {
            "interaction_id": "I002",
            "user_id": "U001",
            "food_id": "F002",
            "interaction_type": "save",
            "timestamp": "2026-01-02T10:00:00",
        },
        {
            "interaction_id": "I003",
            "user_id": "U001",
            "food_id": "F003",
            "interaction_type": "dislike",
            "timestamp": "2026-01-03T10:00:00",
        },
        {
            "interaction_id": "I004",
            "user_id": "U001",
            "food_id": "F004",
            "interaction_type": "skip",
            "timestamp": "2026-01-04T10:00:00",
        },
        {
            "interaction_id": "I005",
            "user_id": "U002",
            "food_id": "F005",
            "interaction_type": "like",
            "timestamp": "2026-01-04T10:00:00",
        },
    ]


def test_user_history_counts_interactions():

    history = build_user_history(
        make_interactions(),
        "U001",
    )

    assert history["previous_likes"] == 1
    assert history["previous_dislikes"] == 1
    assert history["previous_saves"] == 1
    assert history["previous_skips"] == 1
    assert history["previous_interactions"] == 4


def test_history_is_per_user():

    history = build_user_history(
        make_interactions(),
        "U002",
    )

    assert history["previous_likes"] == 1
    assert history["previous_interactions"] == 1
    assert history["previous_saves"] == 0


def test_future_interactions_are_ignored():

    history = build_user_history(
        make_interactions(),
        "U001",
        datetime.fromisoformat(
            "2026-01-03T09:00:00"
        ),
    )

    assert history["previous_likes"] == 1
    assert history["previous_saves"] == 1
    assert history["previous_dislikes"] == 0
    assert history["previous_skips"] == 0
    assert history["previous_interactions"] == 2

def test_recency_is_calculated():

    history = build_user_history(
        make_interactions(),
        "U001",
        datetime.fromisoformat(
            "2026-01-05T10:00:00"
        ),
    )

    assert (
        history["days_since_previous_interaction"]
        == 1.0
    )


def test_unknown_user_has_empty_history():

    history = build_user_history(
        make_interactions(),
        "U999",
    )

    assert history["previous_likes"] == 0
    assert history["previous_dislikes"] == 0
    assert history["previous_saves"] == 0
    assert history["previous_skips"] == 0
    assert history["previous_interactions"] == 0
    assert (
        history["days_since_previous_interaction"]
        == -1.0
    )