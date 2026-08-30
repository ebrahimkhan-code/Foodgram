from training.split_dataset import split_by_user_time


def make_rows():

    return [
        {
            "interaction_id": "I001",
            "user_id": "U001",
            "timestamp": "2026-01-01T10:00:00",
            "target": 1,
        },
        {
            "interaction_id": "I002",
            "user_id": "U001",
            "timestamp": "2026-01-02T10:00:00",
            "target": 0,
        },
        {
            "interaction_id": "I003",
            "user_id": "U001",
            "timestamp": "2026-01-03T10:00:00",
            "target": 1,
        },
        {
            "interaction_id": "I004",
            "user_id": "U001",
            "timestamp": "2026-01-04T10:00:00",
            "target": 0,
        },
        {
            "interaction_id": "I005",
            "user_id": "U001",
            "timestamp": "2026-01-05T10:00:00",
            "target": 1,
        },
        {
            "interaction_id": "I006",
            "user_id": "U001",
            "timestamp": "2026-01-06T10:00:00",
            "target": 0,
        },
    ]


def test_split_creates_three_sets():

    rows = make_rows()

    train, validation, test = split_by_user_time(
        rows,
        train_ratio=0.50,
        validation_ratio=0.25,
    )

    assert len(train) > 0
    assert len(validation) > 0
    assert len(test) > 0


def test_no_interaction_appears_in_multiple_sets():

    rows = make_rows()

    train, validation, test = split_by_user_time(
        rows,
        train_ratio=0.50,
        validation_ratio=0.25,
    )

    train_ids = {
        row["interaction_id"]
        for row in train
    }

    validation_ids = {
        row["interaction_id"]
        for row in validation
    }

    test_ids = {
        row["interaction_id"]
        for row in test
    }

    assert train_ids.isdisjoint(validation_ids)
    assert train_ids.isdisjoint(test_ids)
    assert validation_ids.isdisjoint(test_ids)


def test_split_is_chronological():

    rows = make_rows()

    # Deliberately provide them out of order.
    rows = [
        rows[5],
        rows[1],
        rows[3],
        rows[0],
        rows[4],
        rows[2],
    ]

    train, validation, test = split_by_user_time(
        rows,
        train_ratio=0.50,
        validation_ratio=0.25,
    )

    assert train[0]["interaction_id"] == "I001"
    assert validation[0]["interaction_id"] == "I004"
    assert test[0]["interaction_id"] == "I005"


def test_users_are_kept_in_each_split_when_history_allows():

    rows = []

    for user_id in ["U001", "U002"]:

        for i in range(6):

            rows.append(
                {
                    "interaction_id": (
                        f"{user_id}_{i}"
                    ),
                    "user_id": user_id,
                    "timestamp": (
                        f"2026-01-{i + 1:02d}"
                        "T10:00:00"
                    ),
                    "target": i % 2,
                }
            )

    train, validation, test = split_by_user_time(
        rows,
        train_ratio=0.50,
        validation_ratio=0.25,
    )

    assert {
        row["user_id"]
        for row in train
    } == {"U001", "U002"}

    assert {
        row["user_id"]
        for row in validation
    } == {"U001", "U002"}

    assert {
        row["user_id"]
        for row in test
    } == {"U001", "U002"}


def test_empty_rows_rejected():

    try:
        split_by_user_time([])
        assert False
    except ValueError:
        assert True