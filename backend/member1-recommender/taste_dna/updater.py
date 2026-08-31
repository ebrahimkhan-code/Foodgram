from typing import Dict

from taste_dna.schema import TasteDNA


TASTE_ATTRIBUTES = [
    "cuisine",
    "protein",
    "flavor",
    "spice_level",
    "base",
    "meal_type",
]


INTERACTION_UPDATES = {
    "like": 0.10,
    "save": 0.15,
    "dislike": -0.15,
    "skip": -0.05,
}


MIN_PREFERENCE = -1.0
MAX_PREFERENCE = 1.0


def clamp_preference(value: float) -> float:
    """
    Keep a preference value inside the allowed
    Taste DNA range of [-1.0, 1.0].
    """

    return max(
        MIN_PREFERENCE,
        min(MAX_PREFERENCE, value),
    )


def update_taste_dna(
    taste_dna: TasteDNA,
    food: Dict[str, str],
    interaction: str,
) -> TasteDNA:
    """
    Update a user's Taste DNA based on an interaction
    with a food.

    Supported interactions:

        like     -> +0.10
        save     -> +0.15
        dislike  -> -0.15
        skip     -> -0.05

    The food's six Taste DNA attributes are updated:

        cuisine
        protein
        flavor
        spice_level
        base
        meal_type

    Preference values are always clamped to [-1.0, 1.0].

    The TasteDNA object is updated in place and returned.
    """

    interaction = interaction.strip().lower()

    if interaction not in INTERACTION_UPDATES:
        raise ValueError(
            f"Unknown interaction: {interaction}"
        )

    update_amount = INTERACTION_UPDATES[interaction]

    for attribute in TASTE_ATTRIBUTES:

        if attribute not in food:
            continue

        food_value = food[attribute]

        if not food_value:
            continue

        preferences = getattr(
            taste_dna,
            attribute,
        )

        current_value = preferences.get(
            food_value,
            0.0,
        )

        preferences[food_value] = clamp_preference(
            current_value + update_amount
        )

    return taste_dna