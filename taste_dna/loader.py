import csv
from pathlib import Path
from typing import Dict

from taste_dna.schema import TasteDNA


ATTRIBUTE_COLUMNS = {
    "cuisine": "preferred_cuisines",
    "protein": "preferred_proteins",
    "flavor": "preferred_flavors",
    "spice_level": "preferred_spice_levels",
    "base": "preferred_bases",
    "meal_type": "preferred_meal_types",
}


def normalize_value(value: str) -> str:
    """
    Normalize Taste DNA values so they match the canonical
    lowercase representation used by the recommender.
    """

    return str(value).strip().lower()


def load_taste_dna(
    path: str | Path,
    user_id: str,
) -> TasteDNA:
    """
    Load a user's initial Taste DNA from the synthetic
    user_preferences.csv file.

    Preference values loaded from the CSV are represented
    as +1.0 because the synthetic preference file stores
    preferred values rather than explicit numeric strengths.

    Values are normalized to lowercase so they are compatible
    with the real food catalog.
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
        newline="",
    ) as file:

        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            raise ValueError(
                f"Taste DNA file has no header: {path}"
            )

        for row in reader:

            if row.get("user_id", "").strip() != user_id:
                continue

            dna = TasteDNA(
                user_id=user_id
            )

            for attribute, column in ATTRIBUTE_COLUMNS.items():

                values = row.get(
                    column,
                    "",
                )

                if not values.strip():
                    continue

                target = getattr(
                    dna,
                    attribute,
                )

                for value in values.split("|"):

                    value = normalize_value(value)

                    if not value:
                        continue

                    target[value] = 1.0

            return dna

    raise ValueError(
        f"User not found in Taste DNA data: {user_id}"
    )