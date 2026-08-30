from typing import Dict, List

# pyrefly: ignore [missing-import]
import numpy as np


CATEGORICAL_ATTRIBUTES = [
    "cuisine",
    "protein",
    "flavor",
    "spice_level",
    "base",
    "meal_type",
]


def food_vector(
    food: Dict[str, str],
    dna: Dict[str, Dict[str, float]],
) -> np.ndarray:
    """
    Create a preference-aware vector for a food.

    Each food attribute receives the user's preference score
    for that attribute value.

    Example:

        User likes:
            cuisine = Pakistani -> 1.0
            protein = Chicken   -> 1.0

        Food:
            Pakistani + Chicken

        Result:
            [1.0, 1.0, ...]
    """

    vector = []

    for attribute in CATEGORICAL_ATTRIBUTES:

        value = food[attribute]

        preference = dna.get(attribute, {}).get(value, 0.0)

        vector.append(float(preference))

    return np.array(vector, dtype=float)


def cosine_similarity(
    vector_a: np.ndarray,
    vector_b: np.ndarray,
) -> float:
    """
    Calculate cosine similarity between two vectors.
    """

    vector_a = np.asarray(vector_a, dtype=float)
    vector_b = np.asarray(vector_b, dtype=float)

    norm_a = np.linalg.norm(vector_a)
    norm_b = np.linalg.norm(vector_b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    similarity = np.dot(vector_a, vector_b) / (norm_a * norm_b)

    # Protect against tiny floating-point errors.
    similarity = np.clip(similarity, -1.0, 1.0)

    return float(similarity)


def calculate_food_similarity(
    food: Dict[str, str],
    dna: Dict[str, Dict[str, float]],
) -> float:
    """
    Calculate how well a food matches the user's Taste DNA.
    """

    vector = food_vector(food, dna)

    # Reference vector representing the user's preference signal
    # across the same attribute dimensions.
    user_vector = np.array(
        [
            max(dna.get(attribute, {}).values(), default=0.0)
            for attribute in CATEGORICAL_ATTRIBUTES
        ],
        dtype=float,
    )

    return cosine_similarity(vector, user_vector)