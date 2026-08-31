import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from training.history_features import build_history_features

from training.target import interaction_to_target


TASTE_ATTRIBUTES = [
    "cuisine",
    "protein",
    "flavor",
    "spice_level",
    "base",
    "meal_type",
]


def load_csv(path: str | Path) -> List[Dict[str, str]]:
    """Load a CSV file into a list of dictionaries."""

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    with open(path, "r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            raise ValueError(f"CSV file has no header: {path}")

        rows = list(reader)

    if not rows:
        raise ValueError(f"CSV file is empty: {path}")

    return rows


def parse_rating(value: str) -> Optional[float]:
    """Convert a CSV rating value into float or None."""

    value = value.strip()

    if not value:
        return None

    return float(value)

def normalize_attribute_value(
    attribute: str,
    value: str,
) -> str:
    """
    Normalize food/Taste DNA attribute values into the
    canonical vocabulary used by the recommender.
    """

    value = str(value).strip().lower()

    if not value:
        return "unknown"

    if attribute == "spice_level":
        spice_mapping = {
            "hot": "high",
            "mild": "medium",
            "none": "none",
            "low": "low",
            "medium": "medium",
            "high": "high",
            "unknown": "unknown",
        }

        return spice_mapping.get(
            value,
            "unknown",
        )

    return value


def calculate_attribute_match(
    food: Dict[str, str],
    taste_dna: Dict[str, Dict[str, float]],
    attribute: str,
) -> float:
    """
    Return the user's preference strength for the food's
    normalized attribute value.

    Unknown values do not count as positive matches.
    """

    value = normalize_attribute_value(
        attribute,
        food.get(attribute, "unknown"),
    )

    if value == "unknown":
        return 0.0

    dna_attribute = taste_dna.get(
        attribute,
        {},
    )

    normalized_dna = {
        normalize_attribute_value(
            attribute,
            key,
        ): float(score)
        for key, score in dna_attribute.items()
    }

    return float(
        normalized_dna.get(
            value,
            0.0,
        )
    )

def calculate_taste_features(
    food: Dict[str, str],
    taste_dna: Dict[str, Dict[str, float]],
) -> Dict[str, float]:
    """Calculate personalized Taste DNA features for one food."""

    features = {}

    for attribute in TASTE_ATTRIBUTES:

        feature_name = f"{attribute}_match"

        features[feature_name] = (
            calculate_attribute_match(
                food,
                taste_dna,
                attribute,
            )
        )

    match_values = list(features.values())

    features["taste_match_score"] = (
        sum(match_values) / len(match_values)
        if match_values
        else 0.0
    )

    return features

def build_training_dataset(
    foods_path: str | Path,
    interactions_path: str | Path,
    taste_dna_by_user: Optional[
        Dict[str, Dict[str, Dict[str, float]]]
    ] = None,
) -> List[Dict]:
    """
    Build ML training examples from:

        user
        + food
        + Taste DNA
        + historical behavior
        + context
        + target
    """

    foods = load_csv(foods_path)
    interactions = load_csv(interactions_path)

    foods_by_id = {
        food["food_id"]: food
        for food in foods
    }

    if taste_dna_by_user is None:
        taste_dna_by_user = {}

    # --------------------------------------------------------
    # Build leakage-safe history.
    #
    # Each interaction gets history from BEFORE that
    # interaction only.
    # --------------------------------------------------------

    history_features = build_history_features(
        interactions
    )

    training_rows = []

    for interaction in interactions:

        rating = parse_rating(
            interaction.get("rating", "")
        )

        target = interaction_to_target(
            interaction["interaction_type"],
            rating,
        )

        # Ignore ambiguous interactions.
        if target is None:
            continue

        food_id = interaction["food_id"]

        if food_id not in foods_by_id:
            raise ValueError(
                f"Interaction references unknown food_id: {food_id}"
            )

        food = foods_by_id[food_id]

        timestamp = datetime.fromisoformat(
            interaction["timestamp"]
        )

        user_id = interaction["user_id"]

        # ----------------------------------------------------
        # Taste DNA
        # ----------------------------------------------------

        user_dna = taste_dna_by_user.get(
            user_id,
            {},
        )

        taste_features = calculate_taste_features(
            food,
            user_dna,
        )

        # ----------------------------------------------------
        # Historical behavior
        # ----------------------------------------------------

        historical_features = history_features[
            interaction["interaction_id"]
        ]

        # ----------------------------------------------------
        # Combine everything
        # ----------------------------------------------------

        training_row = {
            # Identity
            "interaction_id": interaction[
                "interaction_id"
            ],
            "user_id": user_id,
            "food_id": food_id,
            "timestamp": interaction["timestamp"],

            # Food
            "cuisine": food["cuisine"],
            "protein": food["protein"],
            "flavor": food["flavor"],
            "spice_level": food["spice_level"],
            "base": food["base"],
            "meal_type": food["meal_type"],

            # Taste DNA
            "cuisine_match": taste_features[
                "cuisine_match"
            ],
            "protein_match": taste_features[
                "protein_match"
            ],
            "flavor_match": taste_features[
                "flavor_match"
            ],
            "spice_level_match": taste_features[
                "spice_level_match"
            ],
            "base_match": taste_features[
                "base_match"
            ],
            "meal_type_match": taste_features[
                "meal_type_match"
            ],
            "taste_match_score": taste_features[
                "taste_match_score"
            ],

            # Historical behavior
            "previous_likes": historical_features[
                "previous_likes"
            ],
            "previous_dislikes": historical_features[
                "previous_dislikes"
            ],
            "previous_saves": historical_features[
                "previous_saves"
            ],
            "previous_skips": historical_features[
                "previous_skips"
            ],
            "previous_interactions": historical_features[
                "previous_interactions"
            ],
            "days_since_previous_interaction": (
                historical_features[
                    "days_since_previous_interaction"
                ]
            ),

            # Context
            "hour": timestamp.hour,
            "day_of_week": timestamp.weekday(),

            # Target
            "target": target,
        }

        training_rows.append(training_row)

    if not training_rows:
        raise ValueError(
            "No usable training rows were produced."
        )

    return training_rows