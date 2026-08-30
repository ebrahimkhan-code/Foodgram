from typing import Dict, List, Tuple


def split_by_user_time(
    rows: List[Dict],
    train_ratio: float = 0.70,
    validation_ratio: float = 0.15,
) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Split interactions chronologically for every user.

    For each user:

        earliest 70%  -> train
        next 15%      -> validation
        latest 15%     -> test

    This prevents future interactions from appearing in the
    training data when evaluating later behavior.
    """

    if not rows:
        raise ValueError("rows cannot be empty.")

    if not 0 < train_ratio < 1:
        raise ValueError(
            "train_ratio must be between 0 and 1."
        )

    if not 0 < validation_ratio < 1:
        raise ValueError(
            "validation_ratio must be between 0 and 1."
        )

    if train_ratio + validation_ratio >= 1:
        raise ValueError(
            "train_ratio + validation_ratio must be less than 1."
        )

    users = {}

    for row in rows:
        user_id = row["user_id"]

        users.setdefault(
            user_id,
            []
        ).append(row)

    train = []
    validation = []
    test = []

    for user_rows in users.values():

        # Oldest → newest
        user_rows = sorted(
            user_rows,
            key=lambda row: row["timestamp"],
        )

        # The dataset currently has interaction IDs that
        # reflect generation order, so they provide a
        # stable chronological ordering here.
        n = len(user_rows)

        train_end = int(n * train_ratio)

        validation_end = int(
            n * (train_ratio + validation_ratio)
        )

        # Make sure very small user histories don't produce
        # an empty training section.
        if n >= 3:
            train_end = max(1, train_end)
            validation_end = max(
                train_end + 1,
                validation_end,
            )
            validation_end = min(
                validation_end,
                n - 1,
            )

        train.extend(
            user_rows[:train_end]
        )

        validation.extend(
            user_rows[
                train_end:validation_end
            ]
        )

        test.extend(
            user_rows[
                validation_end:
            ]
        )

    if not train:
        raise ValueError(
            "Training split is empty."
        )

    if not validation:
        raise ValueError(
            "Validation split is empty."
        )

    if not test:
        raise ValueError(
            "Test split is empty."
        )

    return train, validation, test 