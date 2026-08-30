from datetime import datetime
from typing import Dict, Optional

from training.dataset_builder import calculate_taste_features

MAX_HISTORY_INTERACTIONS = 90.0
MAX_RECENCY_DAYS = 30.0

def build_recommendation_features(
    food: Dict[str, str],
    taste_dna: Dict[str, Dict[str, float]],
    history: Optional[Dict[str, float]] = None,
    timestamp: Optional[datetime] = None,
) -> Dict[str, float]:
    """
    Build the 15 numerical features required by the trained model
    for a single food recommendation.

    Inputs:
        food:
            Food attributes.

        taste_dna:
            User's current Taste DNA.

        history:
            User's historical interaction features.

        timestamp:
            Current recommendation context time.

    Returns:
        Dictionary containing all 15 model features.
    """

    if timestamp is None:
        timestamp = datetime.now()

    if history is None:
        history = {
            "previous_likes": 0.0,
            "previous_dislikes": 0.0,
            "previous_saves": 0.0,
            "previous_skips": 0.0,
            "previous_interactions": 0.0,
            "days_since_previous_interaction": -1.0,
        }

    taste_features = calculate_taste_features(
        food,
        taste_dna,
    )

    return {
        # Taste DNA
        "cuisine_match": taste_features["cuisine_match"],
        "protein_match": taste_features["protein_match"],
        "flavor_match": taste_features["flavor_match"],
        "spice_level_match": taste_features["spice_level_match"],
        "base_match": taste_features["base_match"],
        "meal_type_match": taste_features["meal_type_match"],
        "taste_match_score": taste_features["taste_match_score"],

        # Historical behavior
                # Historical behavior
        "previous_likes": min(
            float(history.get("previous_likes", 0.0)),
            MAX_HISTORY_INTERACTIONS,
        ),
        "previous_dislikes": min(
            float(history.get("previous_dislikes", 0.0)),
            MAX_HISTORY_INTERACTIONS,
        ),
        "previous_saves": min(
            float(history.get("previous_saves", 0.0)),
            MAX_HISTORY_INTERACTIONS,
        ),
        "previous_skips": min(
            float(history.get("previous_skips", 0.0)),
            MAX_HISTORY_INTERACTIONS,
        ),
        "previous_interactions": min(
            float(history.get("previous_interactions", 0.0)),
            MAX_HISTORY_INTERACTIONS,
        ),
        "days_since_previous_interaction": min(
            float(
                history.get(
                    "days_since_previous_interaction",
                    -1.0,
                )
            ),
            MAX_RECENCY_DAYS,
        ),

        # Context
        "hour": float(timestamp.hour),
        "day_of_week": float(timestamp.weekday()),
    }