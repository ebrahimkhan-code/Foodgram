from typing import Dict, List

from taste_dna.schema import TasteDNA


TASTE_ATTRIBUTES = [
    "cuisine",
    "protein",
    "flavor",
    "spice_level",
    "base",
    "meal_type",
]


def calculate_attribute_match(
    food: Dict[str, str],
    taste_dna: TasteDNA,
    food_attribute: str,
) -> float:
    """
    Calculate how strongly the user's Taste DNA matches
    the food's attribute.
    """

    if food_attribute not in TASTE_ATTRIBUTES:
        raise ValueError(
            f"Unknown food attribute: {food_attribute}"
        )

    food_value = food[food_attribute]

    preferences = getattr(
        taste_dna,
        food_attribute,
    )

    return float(
        preferences.get(food_value, 0.0)
    )


def calculate_taste_features(
    food: Dict[str, str],
    taste_dna: TasteDNA,
) -> Dict[str, float]:
    """
    Build the seven Taste DNA features required by the model.
    """

    features = {}

    for attribute in TASTE_ATTRIBUTES:

        features[f"{attribute}_match"] = (
            calculate_attribute_match(
                food,
                taste_dna,
                attribute,
            )
        )

    match_values = [
        features[f"{attribute}_match"]
        for attribute in TASTE_ATTRIBUTES
    ]

    features["taste_match_score"] = (
        sum(match_values) / len(match_values)
    )

    return features


def build_user_food_features(
    food: Dict[str, str],
    taste_dna: TasteDNA,
    historical_features: Dict[str, float],
    hour: int,
    day_of_week: int,
) -> List[float]:
    """
    Build the complete 15-feature vector expected by
    the trained recommendation model.

    Feature order MUST remain identical to
    training.feature_matrix.FEATURE_COLUMNS.
    """

    taste_features = calculate_taste_features(
        food,
        taste_dna,
    )

    return [
        # Taste DNA
        taste_features["cuisine_match"],
        taste_features["protein_match"],
        taste_features["flavor_match"],
        taste_features["spice_level_match"],
        taste_features["base_match"],
        taste_features["meal_type_match"],
        taste_features["taste_match_score"],

        # Historical behavior
        historical_features["previous_likes"],
        historical_features["previous_dislikes"],
        historical_features["previous_saves"],
        historical_features["previous_skips"],
        historical_features["previous_interactions"],
        historical_features[
            "days_since_previous_interaction"
        ],

        # Context
        float(hour),
        float(day_of_week),
    ]