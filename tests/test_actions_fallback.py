# tests/test_actions_fallback.py
from engine.actions import attack, reinforce, fortify

def make_state():
    return {
        "territories": {
            "A": {"owner": "Alice", "armies": 5},
            "B": {"owner": "Bob", "armies": 3},
            "C": {"owner": "Alice", "armies": 2},
        },
        "players": [{"name": "Alice"}, {"name": "Bob"}]
    }

def test_reinforce():
    s = make_state()
    res = reinforce.reinforce(s, "Alice", "A", 2)
    assert res["ok"] and s["territories"]["A"]["armies"] == 7

def test_attack_capture():
    s = make_state()
    res = attack.attack(s, "Alice", "A", "B", 3)
    assert res["ok"]
    assert s["territories"]["B"]["owner"] in ("Alice", "Bob")

def test_fortify():
    s = make_state()
    res = fortify.fortify(s, "Alice", "A", "C", 2)
    assert res["ok"]
    assert s["territories"]["A"]["armies"] == 3
    assert s["territories"]["C"]["armies"] == 4
