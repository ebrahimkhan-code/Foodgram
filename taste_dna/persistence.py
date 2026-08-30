import json
from pathlib import Path

from taste_dna.schema import TasteDNA


TASTE_ATTRIBUTES = [
    "cuisine",
    "protein",
    "flavor",
    "spice_level",
    "base",
    "meal_type",
]


def save_taste_dna(
    taste_dna: TasteDNA,
    path: str | Path,
) -> None:
    """
    Save Taste DNA to a JSON file.
    """

    path = Path(path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            taste_dna.as_dict(),
            file,
            indent=2,
        )


def load_taste_dna_json(
    path: str | Path,
) -> TasteDNA:
    """
    Load Taste DNA from a JSON file.
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Taste DNA file not found: {path}"
        )

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:

        data = json.load(file)

    if "user_id" not in data:
        raise ValueError(
            "Taste DNA JSON is missing user_id."
        )

    dna = TasteDNA(
        user_id=data["user_id"],
    )

    for attribute in TASTE_ATTRIBUTES:

        values = data.get(
            attribute,
            {},
        )

        if not isinstance(values, dict):
            raise ValueError(
                f"Invalid Taste DNA attribute: {attribute}"
            )

        target = getattr(
            dna,
            attribute,
        )

        for value, preference in values.items():

            target[value] = float(preference)

    return dna