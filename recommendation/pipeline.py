from datetime import datetime
from typing import Dict, List, Optional

from recommendation.feature_builder import (
    build_recommendation_features,
)
from recommendation.scorer import score_food
from training.feature_matrix import FEATURE_COLUMNS


def recommend_foods(
    foods: List[Dict[str, str]],
    taste_dna: Dict[str, Dict[str, float]],
    history: Optional[Dict[str, float]] = None,
    timestamp: Optional[datetime] = None,
    top_k: int = 10,
) -> List[Dict]:
    """
    Generate ranked food recommendations.

    The trained Logistic Regression model provides the main
    recommendation probability.

    Taste DNA match is used as a secondary ranking signal when
    multiple foods receive the same model probability.

    Duplicate food names are removed from the final results.
    """

    if top_k <= 0:
        raise ValueError(
            "top_k must be greater than zero."
        )

    if not foods:
        return []

    scored_foods = []

    for food in foods:

        feature_dict = build_recommendation_features(
            food=food,
            taste_dna=taste_dna,
            history=history,
            timestamp=timestamp,
        )

        features = [
            feature_dict[feature]
            for feature in FEATURE_COLUMNS
        ]

        model_score = score_food(features)

        # Number of positive Taste DNA attribute matches.
        attribute_matches = sum(
            1
            for attribute in (
                "cuisine_match",
                "protein_match",
                "flavor_match",
                "spice_level_match",
                "base_match",
                "meal_type_match",
            )
            if feature_dict[attribute] > 0
        )

        scored_foods.append(
            {
                "food": food,
                "score": model_score,
                "_taste_match": feature_dict[
                    "taste_match_score"
                ],
                "_attribute_matches": attribute_matches,
            }
        )

    # ---------------------------------------------------------
    # Primary ranking:
    #   1. Model probability
    #
    # Secondary ranking:
    #   2. Taste DNA match score
    #   3. Number of matched attributes
    #
    # This resolves many otherwise-identical model scores
    # without changing the trained model.
    # ---------------------------------------------------------

    scored_foods.sort(
        key=lambda item: (
            item["score"],
            item["_taste_match"],
            item["_attribute_matches"],
        ),
        reverse=True,
    )

    # ---------------------------------------------------------
    # Remove duplicate food names
    # ---------------------------------------------------------

    unique_foods = []
    seen_names = set()

    for item in scored_foods:

        name = item["food"].get(
            "name",
            "",
        ).strip().lower()

        if name:
            if name in seen_names:
                continue

            seen_names.add(name)

        # Internal ranking fields are not returned.
        result = {
            "food": item["food"],
            "score": item["score"],
        }

        unique_foods.append(result)

        if len(unique_foods) >= top_k:
            break

    return unique_foods