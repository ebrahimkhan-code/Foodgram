from typing import Dict, List

from candidate_generation.similarity import (
    calculate_food_similarity,
)


def generate_candidates(
    foods: List[Dict[str, str]],
    taste_dna: Dict[str, Dict[str, float]],
    top_k: int = 20,
) -> List[Dict]:
    """
    Generate a ranked candidate pool based on Taste DNA similarity.

    Args:
        foods: Food catalog.
        taste_dna: User's current Taste DNA.
        top_k: Number of candidates to return.

    Returns:
        Foods ranked by similarity score.
    """

    if top_k <= 0:
        raise ValueError("top_k must be greater than zero.")

    if not foods:
        return []

    scored_foods = []

    for food in foods:

        similarity = calculate_food_similarity(
            food,
            taste_dna,
        )

        scored_foods.append(
            {
                "food_id": food["food_id"],
                "name": food["name"],
                "similarity_score": similarity,
            }
        )

    scored_foods.sort(
        key=lambda item: item["similarity_score"],
        reverse=True,
    )

    return scored_foods[:top_k]