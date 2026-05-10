def test_calculate_reinforcements_basic():
    gs = {
        "territories": {
            "A": {"owner": "Alice", "armies": 1},
            "B": {"owner": "Alice", "armies": 1},
            "C": {"owner": "Bob", "armies": 1},
            "D": {"owner": "Alice", "armies": 1},
        },
        "continents": {},
        "rules": {}
    }
    assert calculate_reinforcements(gs, "Alice") == max(3, 3 // 3)  # 3 territories -> base 1 -> min 3

def test_apply_reinforcements():
    gs = {"territories": {"A": {"owner": "Alice", "armies": 2}}}
    res = apply_reinforcements(gs, "Alice", "A", 3)
    assert res["ok"]
    assert gs["territories"]["A"]["armies"] == 5
