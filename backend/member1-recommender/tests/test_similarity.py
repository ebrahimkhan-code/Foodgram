# pyrefly: ignore [missing-import]
import numpy as np

from candidate_generation.similarity import (
    calculate_food_similarity,
    cosine_similarity,
    food_vector,
)


def sample_dna():
    return {
        "cuisine": {
            "Pakistani": 1.0,
            "Chinese": 0.5,
        },
        "protein": {
            "Chicken": 1.0,
        },
        "flavor": {
            "Savory": 1.0,
        },
        "spice_level": {
            "High": 1.0,
        },
        "base": {
            "Rice": 1.0,
        },
        "meal_type": {
            "Dinner": 1.0,
        },
    }


def sample_food():
    return {
        "food_id": "F001",
        "name": "Chicken Biryani",
        "cuisine": "Pakistani",
        "protein": "Chicken",
        "flavor": "Savory",
        "spice_level": "High",
        "base": "Rice",
        "meal_type": "Dinner",
    }


def test_food_vector():

    food = sample_food()
    dna = sample_dna()

    vector = food_vector(food, dna)

    assert isinstance(vector, np.ndarray)

    assert vector.shape == (6,)

    assert np.all(vector >= 0)


def test_cosine_similarity_identical_vectors():

    vector = np.array([1.0, 1.0, 1.0])

    similarity = cosine_similarity(vector, vector)

    assert similarity == 1.0


def test_cosine_similarity_zero_vector():

    vector_a = np.array([1.0, 0.0])
    vector_b = np.array([0.0, 0.0])

    similarity = cosine_similarity(vector_a, vector_b)

    assert similarity == 0.0


def test_food_similarity():

    food = sample_food()
    dna = sample_dna()

    similarity = calculate_food_similarity(food, dna)

    assert 0.0 <= similarity <= 1.0


def test_matching_food_gets_positive_similarity():

    food = sample_food()
    dna = sample_dna()

    similarity = calculate_food_similarity(food, dna)

    assert similarity > 0.0