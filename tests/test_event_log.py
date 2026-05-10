# tests/test_event_log.py
from engine.event_log import EventLog

def test_event_log_append_and_export():
    gs = {}
    el = EventLog(gs)
    el.append({"turn": 1, "player": "Alice", "type": "reinforce", "desc": "Placed 3 on A"})
    text = el.export_text()
    assert "Alice" in text
    assert "Placed 3 on A" in text
