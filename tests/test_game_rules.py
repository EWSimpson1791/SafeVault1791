# tests/test_game_rules.py
from engine.game_rules import check_victory, check_eliminations

def make_state_single_owner():
    return {
        "territories": {
            "A": {"owner": "Alice", "armies": 2},
            "B": {"owner": "Alice", "armies": 1},
        },
        "players": [{"name": "Alice"}, {"name": "Bob"}]
    }

def make_state_multiple():
    return {
        "territories": {
            "A": {"owner": "Alice", "armies": 2},
            "B": {"owner": "Bob", "armies": 1},
        },
        "players": [{"name": "Alice"}, {"name": "Bob"}]
    }

def test_victory_single_owner():
    s = make_state_single_owner()
    assert check_victory(s) == "Alice"

def test_no_victory():
    s = make_state_multiple()
    assert check_victory(s) is None

def test_eliminations():
    s = make_state_multiple()
    elim = check_eliminations(s)
    assert elim["Alice"] is False
    assert elim["Bob"] is False
