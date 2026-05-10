# scripts/demo_ui.py
"""
Small demo to exercise UI helpers: prints status, ASCII map, and event log.
Run: python -m scripts.demo_ui
"""

from ui.status import format_status
from ui.ascii_map import render_ascii_map
from engine.event_log import EventLog

def sample_game_state():
    return {
        "players": [{"name": "Alice"}, {"name": "Bob"}],
        "territories": {
            "A": {"owner": "Alice", "armies": 3},
            "B": {"owner": "Bob", "armies": 1},
            "C": {"owner": "Alice", "armies": 2},
        },
        "map_layout": ["T:A T:B . T:C"],
        "pending_reinforcements": {"Alice": 2, "Bob": 3},
        "event_log": [
            {"turn": 0, "player": "Alice", "type": "start", "desc": "Game started"},
        ],
        "rules": {}
    }

def main():
    gs = sample_game_state()
    print("=== STATUS ===")
    print(format_status(gs, "Alice"))
    print("\n=== ASCII MAP ===")
    print(render_ascii_map(gs))
    print("\n=== EVENT LOG ===")
    el = EventLog(gs)
    el.append({"turn": 1, "player": "Alice", "type": "reinforce", "desc": "Placed 2 on A"})
    el.append({"turn": 2, "player": "Bob", "type": "attack", "desc": "B attacked C"})
    print(el.export_text())

if __name__ == "__main__":
    main()
