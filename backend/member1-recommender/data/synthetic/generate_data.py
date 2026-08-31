import csv
import random
from datetime import datetime, timedelta
from pathlib import Path


# ============================================================
# Configuration
# ============================================================

NUM_USERS = 50
NUM_FOODS = 100
NUM_INTERACTIONS = 5000

OUTPUT_DIR = Path(__file__).parent


# ============================================================
# Available food attributes
# ============================================================

CUISINES = [
    "Pakistani",
    "Chinese",
    "Italian",
    "Indian",
    "Thai",
    "Mexican",
]

PROTEINS = [
    "Chicken",
    "Beef",
    "Mutton",
    "Fish",
    "Vegetarian",
]

FLAVORS = [
    "Savory",
    "Spicy",
    "Sweet",
    "Sour",
    "Creamy",
]

SPICE_LEVELS = [
    "Low",
    "Medium",
    "High",
]

BASES = [
    "Rice",
    "Noodles",
    "Bread",
    "Pasta",
    "Curry",
]

MEAL_TYPES = [
    "Breakfast",
    "Lunch",
    "Dinner",
    "Snack",
]

INTERACTIONS = [
    "like",
    "dislike",
    "save",
    "click",
    "skip",
    "rating",
]


# ============================================================
# Helpers
# ============================================================

def random_timestamp():
    """
    Generate a timestamp within a 90-day period.
    """

    start = datetime(2026, 1, 1)

    random_days = random.randint(0, 89)
    random_minutes = random.randint(0, 1439)

    return start + timedelta(
        days=random_days,
        minutes=random_minutes,
    )


def choose_preferences(values, min_count=1, max_count=3):
    """
    Randomly select a small set of preferred values.
    """

    count = random.randint(
        min_count,
        min(max_count, len(values)),
    )

    return random.sample(values, count)


# ============================================================
# Generate foods
# ============================================================

def generate_foods():

    foods = []

    for i in range(1, NUM_FOODS + 1):

        food = {
            "food_id": f"F{i:03d}",
            "name": f"Food {i}",
            "cuisine": random.choice(CUISINES),
            "protein": random.choice(PROTEINS),
            "flavor": random.choice(FLAVORS),
            "spice_level": random.choice(SPICE_LEVELS),
            "base": random.choice(BASES),
            "meal_type": random.choice(MEAL_TYPES),
        }

        foods.append(food)

    return foods


# ============================================================
# Generate users
# ============================================================

def generate_users():

    return [
        {
            "user_id": f"U{i:03d}"
        }
        for i in range(1, NUM_USERS + 1)
    ]


# ============================================================
# Generate hidden user preferences
# ============================================================

def generate_user_preferences(users):

    preferences = []

    for user in users:

        preferences.append(
            {
                "user_id": user["user_id"],

                "preferred_cuisines": choose_preferences(
                    CUISINES
                ),

                "preferred_proteins": choose_preferences(
                    PROTEINS
                ),

                "preferred_flavors": choose_preferences(
                    FLAVORS
                ),

                "preferred_spice_levels": choose_preferences(
                    SPICE_LEVELS
                ),

                "preferred_bases": choose_preferences(
                    BASES
                ),

                "preferred_meal_types": choose_preferences(
                    MEAL_TYPES
                ),
            }
        )

    return preferences


# ============================================================
# Calculate food-user compatibility
# ============================================================

def calculate_match_score(user_preference, food):

    score = 0

    if food["cuisine"] in user_preference["preferred_cuisines"]:
        score += 1

    if food["protein"] in user_preference["preferred_proteins"]:
        score += 1

    if food["flavor"] in user_preference["preferred_flavors"]:
        score += 1

    if food["spice_level"] in user_preference["preferred_spice_levels"]:
        score += 1

    if food["base"] in user_preference["preferred_bases"]:
        score += 1

    if food["meal_type"] in user_preference["preferred_meal_types"]:
        score += 1

    return score


# ============================================================
# Convert compatibility into interaction probability
# ============================================================

def interaction_probability(match_score):

    """
    Higher compatibility means a higher probability
    of a positive interaction.
    """

    probabilities = {
        0: 0.10,
        1: 0.20,
        2: 0.35,
        3: 0.50,
        4: 0.65,
        5: 0.80,
        6: 0.92,
    }

    return probabilities[match_score]


# ============================================================
# Generate realistic interactions
# ============================================================

def generate_interactions(users, foods, user_preferences):

    preference_lookup = {
        preference["user_id"]: preference
        for preference in user_preferences
    }

    interactions = []

    for i in range(1, NUM_INTERACTIONS + 1):

        user = random.choice(users)
        food = random.choice(foods)

        user_preference = preference_lookup[
            user["user_id"]
        ]

        match_score = calculate_match_score(
            user_preference,
            food,
        )

        positive_probability = interaction_probability(
            match_score
        )

        # ----------------------------------------------------
        # Decide whether this interaction is positive
        # ----------------------------------------------------

        is_positive = random.random() < positive_probability

        if is_positive:

            interaction_type = random.choices(
                ["like", "save", "click", "rating"],
                weights=[45, 25, 20, 10],
                k=1,
            )[0]

        else:

            interaction_type = random.choices(
                ["dislike", "skip", "click"],
                weights=[40, 40, 20],
                k=1,
            )[0]

        # ----------------------------------------------------
        # Rating
        # ----------------------------------------------------

        rating = ""

        if interaction_type == "rating":

            if is_positive:
                rating = random.choice([4, 4, 5, 5])
            else:
                rating = random.choice([1, 2, 2])

        interaction = {
            "interaction_id": f"I{i:05d}",
            "user_id": user["user_id"],
            "food_id": food["food_id"],
            "interaction_type": interaction_type,
            "rating": rating,
            "timestamp": random_timestamp().isoformat(),
        }

        interactions.append(interaction)

    return interactions


# ============================================================
# CSV writer
# ============================================================

def save_csv(filename, rows, fieldnames):

    path = OUTPUT_DIR / filename

    with open(
        path,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)

    print(f"Created: {path}")


# ============================================================
# Main
# ============================================================

def main():

    random.seed(42)

    users = generate_users()

    foods = generate_foods()

    user_preferences = generate_user_preferences(
        users
    )

    interactions = generate_interactions(
        users,
        foods,
        user_preferences,
    )

    # --------------------------------------------------------
    # Users
    # --------------------------------------------------------

    save_csv(
        "users.csv",
        users,
        ["user_id"],
    )

    # --------------------------------------------------------
    # Foods
    # --------------------------------------------------------

    save_csv(
        "foods.csv",
        foods,
        [
            "food_id",
            "name",
            "cuisine",
            "protein",
            "flavor",
            "spice_level",
            "base",
            "meal_type",
        ],
    )

    # --------------------------------------------------------
    # User preferences
    # --------------------------------------------------------

    preference_rows = []

    for preference in user_preferences:

        preference_rows.append(
            {
                "user_id": preference["user_id"],
                "preferred_cuisines": "|".join(
                    preference["preferred_cuisines"]
                ),
                "preferred_proteins": "|".join(
                    preference["preferred_proteins"]
                ),
                "preferred_flavors": "|".join(
                    preference["preferred_flavors"]
                ),
                "preferred_spice_levels": "|".join(
                    preference["preferred_spice_levels"]
                ),
                "preferred_bases": "|".join(
                    preference["preferred_bases"]
                ),
                "preferred_meal_types": "|".join(
                    preference["preferred_meal_types"]
                ),
            }
        )

    save_csv(
        "user_preferences.csv",
        preference_rows,
        [
            "user_id",
            "preferred_cuisines",
            "preferred_proteins",
            "preferred_flavors",
            "preferred_spice_levels",
            "preferred_bases",
            "preferred_meal_types",
        ],
    )

    # --------------------------------------------------------
    # Interactions
    # --------------------------------------------------------

    save_csv(
        "interactions.csv",
        interactions,
        [
            "interaction_id",
            "user_id",
            "food_id",
            "interaction_type",
            "rating",
            "timestamp",
        ],
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print()
    print("Synthetic dataset generated successfully.")
    print(f"Users: {len(users)}")
    print(f"Foods: {len(foods)}")
    print(f"User preferences: {len(user_preferences)}")
    print(f"Interactions: {len(interactions)}")


if __name__ == "__main__":
    main()