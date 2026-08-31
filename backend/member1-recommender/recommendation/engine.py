from typing import Dict, List

from recommendation.scorer import score_food
from training.feature_matrix import FEATURE_COLUMNS


def rank_candidates(
    candidates: List[Dict],
) -> List[Dict]:
    """
    Score and rank candidate foods.

    Each candidate must contain a numerical value for every
    feature in FEATURE_COLUMNS.

    Returns candidates sorted from highest score to lowest.
    """

    if not candidates:
        return []

    scored_candidates = []

    for candidate in candidates:

        features = []

        for feature in FEATURE_COLUMNS:

            if feature not in candidate:
                raise ValueError(
                    f"Candidate is missing feature: {feature}"
                )

            features.append(
                float(candidate[feature])
            )

        score = score_food(features)

        result = dict(candidate)
        result["recommendation_score"] = score

        scored_candidates.append(result)

    scored_candidates.sort(
        key=lambda candidate: candidate["recommendation_score"],
        reverse=True,
    )

    return scored_candidates


def get_top_recommendations(
    candidates: List[Dict],
    top_k: int = 10,
) -> List[Dict]:
    """
    Return the top K candidates ranked by recommendation score.
    """

    if top_k <= 0:
        raise ValueError(
            "top_k must be greater than zero."
        )

    ranked = rank_candidates(candidates)

    return ranked[:top_k]