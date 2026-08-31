from datetime import datetime
from typing import Dict, List


MAX_HISTORY_COUNT = 30.0
MAX_RECENCY_DAYS = 30.0


def build_history_features(
    interactions: List[Dict[str, str]],
) -> Dict[str, Dict[str, float]]:
    """
    Build leakage-safe historical features.

    For every interaction, only interactions occurring BEFORE
    that interaction are used.

    History counts and recency are capped so that training
    and live recommendation features remain within controlled
    ranges.
    """

    if not interactions:
        return {}

    sorted_interactions = sorted(
        interactions,
        key=lambda row: datetime.fromisoformat(
            row["timestamp"]
        ),
    )

    user_history = {}
    features_by_interaction = {}

    for interaction in sorted_interactions:

        interaction_id = interaction["interaction_id"]
        user_id = interaction["user_id"]

        timestamp = datetime.fromisoformat(
            interaction["timestamp"]
        )

        history = user_history.setdefault(
            user_id,
            {
                "likes": 0,
                "dislikes": 0,
                "saves": 0,
                "skips": 0,
                "interactions": 0,
                "last_timestamp": None,
            },
        )

        # Calculate features BEFORE adding the current
        # interaction. This prevents data leakage.

        previous_timestamp = history["last_timestamp"]

        if previous_timestamp is None:
            days_since_previous = -1.0
        else:
            days_since_previous = (
                timestamp - previous_timestamp
            ).total_seconds() / 86400.0

            days_since_previous = min(
                days_since_previous,
                MAX_RECENCY_DAYS,
            )

        features_by_interaction[interaction_id] = {
            "previous_likes": min(
                float(history["likes"]),
                MAX_HISTORY_COUNT,
            ),
            "previous_dislikes": min(
                float(history["dislikes"]),
                MAX_HISTORY_COUNT,
            ),
            "previous_saves": min(
                float(history["saves"]),
                MAX_HISTORY_COUNT,
            ),
            "previous_skips": min(
                float(history["skips"]),
                MAX_HISTORY_COUNT,
            ),
            "previous_interactions": min(
                float(history["interactions"]),
                MAX_HISTORY_COUNT,
            ),
            "days_since_previous_interaction": (
                days_since_previous
            ),
        }

        # Now update history using the current interaction.

        interaction_type = (
            interaction["interaction_type"]
            .lower()
            .strip()
        )

        if interaction_type == "like":
            history["likes"] += 1

        elif interaction_type == "dislike":
            history["dislikes"] += 1

        elif interaction_type == "save":
            history["saves"] += 1

        elif interaction_type == "skip":
            history["skips"] += 1

        history["interactions"] += 1
        history["last_timestamp"] = timestamp

    return features_by_interaction