# tests/test_ui_render.py
from ui.ascii_map import render_ascii_map
from ui.status import format_status

def test_ascii_map_render():
    gs = {
        "territories": {"A": {"owner": "Alice", "armies": 3}, "B": {"owner": "Bob", "armies": 1}},
        "map_layout": ["T:A T:B"]
    }
    out = render_ascii_map(gs)
    assert "A(3)" in out and "B(1)" in out

def test_format_status_contains_pending():
    gs = {
        "territories": {"A": {"owner": "Alice", "armies": 3}},
        "pending_reinforcements": {"Alice": 5}
    }
    s = format_status(gs, "Alice")
    assert "Pending reinforcements" in s
    assert "A" in s
