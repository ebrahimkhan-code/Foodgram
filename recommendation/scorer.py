from typing import List

from training.model_loader import load_model


EXPECTED_FEATURE_COUNT = 15


def score_food(features: List[float]) -> float:
    """
    Return the model's probability that a food is a
    positive recommendation for the user.

    The feature order must match
    training.feature_matrix.FEATURE_COLUMNS.
    """

    if len(features) != EXPECTED_FEATURE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_FEATURE_COUNT} features, "
            f"got {len(features)}."
        )

    model = load_model()

    probability = model.predict_proba(
        [features]
    )[0][1]

    return float(probability)


def rank_foods(
    food_features: List[List[float]],
) -> List[float]:
    """
    Score multiple foods and return probabilities
    in the same order as the input.
    """

    if not food_features:
        return []

    for features in food_features:
        if len(features) != EXPECTED_FEATURE_COUNT:
            raise ValueError(
                f"Expected {EXPECTED_FEATURE_COUNT} features, "
                f"got {len(features)}."
            )

    model = load_model()

    probabilities = model.predict_proba(
        food_features
    )[:, 1]

    return [
        float(probability)
        for probability in probabilities
    ]