from recommendation import demo


def test_load_foods_returns_foods():

    foods = demo.load_foods()

    assert foods
    assert all("food_id" in food for food in foods)
    assert all("name" in food for food in foods)


def test_demo_uses_requested_user(monkeypatch):

    captured = {}

    def fake_load_taste_dna(path, user_id):
        captured["user_id"] = user_id

        from taste_dna.schema import TasteDNA

        return TasteDNA(
            user_id=user_id,
        )

    
    def fake_recommend_foods(
    foods,
    taste_dna,
    history,
    timestamp,
    top_k,
):
     return [
        {
            "food": {
                "name": "Test Food",
            },
            "score": 0.75,
        }
    ]

    monkeypatch.setattr(
        demo,
        "load_taste_dna",
        fake_load_taste_dna,
    )

    monkeypatch.setattr(
        demo,
        "recommend_foods",
        fake_recommend_foods,
    )

    monkeypatch.setattr(
        demo.sys,
        "argv",
        [
            "demo.py",
            "U002",
        ],
    )

    demo.main()

    assert captured["user_id"] == "U002"


def test_demo_defaults_to_u001(monkeypatch):

    captured = {}

    def fake_load_taste_dna(path, user_id):
        captured["user_id"] = user_id

        from taste_dna.schema import TasteDNA

        return TasteDNA(
            user_id=user_id,
        )

    def fake_recommend_foods(
    foods,
    taste_dna,
    history,
    timestamp,
    top_k,
):
     return [
          {
            "food": {
                "name": "Test Food",
            },
            "score": 0.75,
        }
    ]

    monkeypatch.setattr(
        demo,
        "load_taste_dna",
        fake_load_taste_dna,
    )

    monkeypatch.setattr(
        demo,
        "recommend_foods",
        fake_recommend_foods,
    )

    monkeypatch.setattr(
        demo.sys,
        "argv",
        [
            "demo.py",
        ],
    )

    demo.main()

    assert captured["user_id"] == "U001"