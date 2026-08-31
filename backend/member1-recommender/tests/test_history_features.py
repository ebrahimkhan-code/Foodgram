from training.history_features import build_history_features


def test_first_interaction_has_no_history():

    interactions = [
        {
            "interaction_id": "I001",
            "user_id": "U001",
            "interaction_type": "like",
            "timestamp": "2026-01-01T10:00:00",
        }
    ]

    features = build_history_features(
        interactions
    )

    row = features["I001"]

    assert row["previous_likes"] == 0
    assert row["previous_dislikes"] == 0
    assert row["previous_saves"] == 0
    assert row["previous_skips"] == 0
    assert row["previous_interactions"] == 0
    assert row["days_since_previous_interaction"] == -1


def test_history_only_contains_previous_interactions():

    interactions = [
        {
            "interaction_id": "I001",
            "user_id": "U001",
            "interaction_type": "like",
            "timestamp": "2026-01-01T10:00:00",
        },
        {
            "interaction_id": "I002",
            "user_id": "U001",
            "interaction_type": "save",
            "timestamp": "2026-01-02T10:00:00",
        },
    ]

    features = build_history_features(
        interactions
    )

    first = features["I001"]
    second = features["I002"]

    # Nothing existed before I001.
    assert first["previous_likes"] == 0
    assert first["previous_saves"] == 0
    assert first["previous_interactions"] == 0

    # I001 existed before I002.
    assert second["previous_likes"] == 1
    assert second["previous_saves"] == 0
    assert second["previous_interactions"] == 1


def test_history_is_per_user():

    interactions = [
        {
            "interaction_id": "I001",
            "user_id": "U001",
            "interaction_type": "like",
            "timestamp": "2026-01-01T10:00:00",
        },
        {
            "interaction_id": "I002",
            "user_id": "U002",
            "interaction_type": "like",
            "timestamp": "2026-01-01T11:00:00",
        },
    ]

    features = build_history_features(
        interactions
    )

    assert features["I001"]["previous_interactions"] == 0
    assert features["I002"]["previous_interactions"] == 0


def test_recency_is_calculated():

    interactions = [
        {
            "interaction_id": "I001",
            "user_id": "U001",
            "interaction_type": "like",
            "timestamp": "2026-01-01T10:00:00",
        },
        {
            "interaction_id": "I002",
            "user_id": "U001",
            "interaction_type": "click",
            "timestamp": "2026-01-03T10:00:00",
        },
    ]

    features = build_history_features(
        interactions
    )

    assert (
        features["I002"][
            "days_since_previous_interaction"
        ]
        == 2.0
    )


def test_future_interaction_does_not_leak():

    interactions = [
        {
            "interaction_id": "I001",
            "user_id": "U001",
            "interaction_type": "like",
            "timestamp": "2026-01-01T10:00:00",
        },
        {
            "interaction_id": "I002",
            "user_id": "U001",
            "interaction_type": "dislike",
            "timestamp": "2026-01-02T10:00:00",
        },
    ]

    features = build_history_features(
        interactions
    )

    # I001 must not know about the future dislike.
    assert features["I001"]["previous_dislikes"] == 0
    assert features["I001"]["previous_interactions"] == 0