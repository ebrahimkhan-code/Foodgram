from taste_dna.generator import generate_initial_taste_dna


def test_initial_taste_dna():

    answers = [
        {
            "attribute": "cuisine",
            "value": "Pakistani",
            "preference": 1,
        },
        {
            "attribute": "cuisine",
            "value": "Chinese",
            "preference": 1,
        },
        {
            "attribute": "protein",
            "value": "Chicken",
            "preference": 1,
        },
        {
            "attribute": "flavor",
            "value": "Savory",
            "preference": 1,
        },
        {
            "attribute": "spice_level",
            "value": "High",
            "preference": 1,
        },
        {
            "attribute": "meal_type",
            "value": "Dinner",
            "preference": 1,
        },
    ]

    dna = generate_initial_taste_dna(
        user_id="U001",
        game_answers=answers,
    )

    assert dna.user_id == "U001"
    assert dna.cuisine["Pakistani"] == 1
    assert dna.cuisine["Chinese"] == 1
    assert dna.protein["Chicken"] == 1
    assert dna.flavor["Savory"] == 1
    assert dna.spice_level["High"] == 1
    assert dna.meal_type["Dinner"] == 1