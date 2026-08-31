from typing import Optional


POSITIVE_INTERACTIONS = {
    "like",
    "save",
}

NEGATIVE_INTERACTIONS = {
    "dislike",
    "skip",
}


def interaction_to_target(
    interaction_type: str,
    rating: Optional[float] = None,
) -> Optional[int]:
    """
    Convert a raw interaction into an ML target.

    Returns:
        1 -> positive interaction
        0 -> negative interaction
        None -> insufficient/ambiguous signal
    """

    interaction_type = interaction_type.lower().strip()

    if interaction_type in POSITIVE_INTERACTIONS:
        return 1

    if interaction_type in NEGATIVE_INTERACTIONS:
        return 0

    if interaction_type == "rating":
        if rating is None:
            return None

        if rating >= 4:
            return 1

        if rating <= 2:
            return 0

        # 3-star rating is ambiguous for now.
        return None

    # Click is intentionally not classified yet.
    if interaction_type == "click":
        return None

    return None