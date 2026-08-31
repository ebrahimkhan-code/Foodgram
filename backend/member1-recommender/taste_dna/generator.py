from typing import Dict, List

from taste_dna.schema import TasteDNA


ATTRIBUTE_NAMES = [
    "cuisine",
    "protein",
    "flavor",
    "spice_level",
    "base",
    "meal_type",
]


def generate_initial_taste_dna(
    user_id: str,
    game_answers: List[Dict[str, str]],
) -> TasteDNA:
    """
    Convert Taste Game answers into an initial Taste DNA.

    Expected answer format:

    {
        "attribute": "cuisine",
        "value": "Pakistani",
        "preference": 1
    }

    preference:
        1  -> prefer
        0  -> neutral
       -1  -> dislike
    """

    dna = TasteDNA(user_id=user_id)

    for answer in game_answers:
        attribute = answer["attribute"]
        value = answer["value"]
        preference = float(answer["preference"])

        if attribute not in ATTRIBUTE_NAMES:
            raise ValueError(
                f"Unknown Taste DNA attribute: {attribute}"
            )

        target = getattr(dna, attribute)

        # If the same attribute/value appears more than once,
        # accumulate the evidence.
        target[value] = target.get(value, 0.0) + preference

    return dna