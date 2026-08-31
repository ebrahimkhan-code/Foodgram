import csv
from pathlib import Path
from typing import Dict

from taste_dna.generator import generate_initial_taste_dna


ATTRIBUTE_MAPPING = {
    "preferred_cuisines": "cuisine",
    "preferred_proteins": "protein",
    "preferred_flavors": "flavor",
    "preferred_spice_levels": "spice_level",
    "preferred_bases": "base",
    "preferred_meal_types": "meal_type",
}


def load_synthetic_taste_dna(
    path: str | Path,
) -> Dict[str, Dict]:
    """
    Load synthetic user preferences and convert them
    into the same Taste DNA representation used by
    the application.
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"User preferences file not found: {path}"
        )

    taste_dna_by_user = {}

    with open(
        path,
        "r",
        encoding="utf-8",
        newline="",
    ) as file:

        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            raise ValueError(
                f"CSV file has no header: {path}"
            )

        for row in reader:

            user_id = row["user_id"]

            answers = []

            for csv_attribute, dna_attribute in (
                ATTRIBUTE_MAPPING.items()
            ):

                values = row[csv_attribute].strip()

                if not values:
                    continue

                for value in values.split("|"):

                    answers.append(
                        {
                            "attribute": dna_attribute,
                            "value": value,
                            "preference": 1,
                        }
                    )

            dna = generate_initial_taste_dna(
                user_id=user_id,
                game_answers=answers,
            )

            taste_dna_by_user[user_id] = (
                dna.as_dict()
            )

    return taste_dna_by_user