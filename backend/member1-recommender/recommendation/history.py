import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List

MAX_HISTORY_INTERACTIONS = 90.0
MAX_HISTORY_COUNT = 30.0
MAX_RECENCY_DAYS = 30.0


HISTORY_DEFAULTS = {
    "previous_likes": 0.0,
    "previous_dislikes": 0.0,
    "previous_saves": 0.0,
    "previous_skips": 0.0,
    "previous_interactions": 0.0,
    "days_since_previous_interaction": -1.0,
}


def load_interactions(
    path: str | Path,
) -> List[Dict[str, str]]:
    """
    Load interaction history from a CSV file.
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Interactions file not found: {path}"
        )

    with open(
        path,
        "r",
        encoding="utf-8",
        newline="",
    ) as file:

        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            raise ValueError(
                f"CSV file has no header: {path}"
            )

        return list(reader)


def build_user_history(
    interactions: List[Dict[str, str]],
    user_id: str,
    timestamp: datetime | None = None,
) -> Dict[str, float]:
    """
    Build historical behavior features for one user.

    Only interactions occurring before the supplied timestamp
    are considered.

    If timestamp is omitted, all available interactions for
    the user are considered.

    Recency is capped at MAX_RECENCY_DAYS so that live
    recommendation features stay within the same controlled
    range used during model training.
    """

    user_interactions = []

    for interaction in interactions:

        if interaction.get("user_id") != user_id:
            continue

        interaction_timestamp = datetime.fromisoformat(
            interaction["timestamp"]
        )

        if (
            timestamp is not None
            and interaction_timestamp >= timestamp
        ):
            continue

        user_interactions.append(
            (
                interaction_timestamp,
                interaction,
            )
        )

    user_interactions.sort(
        key=lambda item: item[0]
    )

    if not user_interactions:
        return dict(HISTORY_DEFAULTS)

    likes = 0
    dislikes = 0
    saves = 0
    skips = 0

    last_timestamp = None

    for interaction_timestamp, interaction in user_interactions:

        interaction_type = (
            interaction
            .get("interaction_type", "")
            .strip()
            .lower()
        )

        if interaction_type == "like":
            likes += 1

        elif interaction_type == "dislike":
            dislikes += 1

        elif interaction_type == "save":
            saves += 1

        elif interaction_type == "skip":
            skips += 1

        last_timestamp = interaction_timestamp

    reference_timestamp = (
        timestamp
        if timestamp is not None
        else datetime.now()
    )

    days_since_previous = (
        reference_timestamp - last_timestamp
    ).total_seconds() / 86400.0

    days_since_previous = min(
        days_since_previous,
        MAX_RECENCY_DAYS,
    )

    return {
        "previous_likes": float(
            min(likes, MAX_HISTORY_INTERACTIONS)
        ),
        "previous_dislikes": float(
            min(dislikes, MAX_HISTORY_INTERACTIONS)
        ),
        "previous_saves": float(
            min(saves, MAX_HISTORY_INTERACTIONS)
        ),
        "previous_skips": float(
            min(skips, MAX_HISTORY_INTERACTIONS)
        ),
        "previous_interactions": float(
            min(
                len(user_interactions),
                MAX_HISTORY_INTERACTIONS,
            )
        ),
        "days_since_previous_interaction": float(
            min(
                days_since_previous,
                30.0,
            )
        ),
     }