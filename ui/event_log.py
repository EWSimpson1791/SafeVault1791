# engine/event_log.py
"""
Append-only event log stored inside game_state for persistence and replay.
"""

from typing import Any, Dict, List

class EventLog:
    def __init__(self, game_state: Dict[str, Any]):
        # Ensure event_log exists in game_state
        self._list = game_state.setdefault("event_log", [])

    def append(self, event: Dict[str, Any]) -> None:
        """
        Append an event dict. Recommended keys: turn, player, type, desc, meta.
        """
        try:
            self._list.append(event)
        except Exception:
            # Best-effort: ignore logging failures to avoid breaking game flow
            pass

    def last(self, n: int = 10) -> List[Dict[str, Any]]:
        return self._list[-n:]

    def export_text(self) -> str:
        lines = []
        for e in self._list:
            turn = e.get("turn", "?")
            player = e.get("player", "Unknown")
            etype = e.get("type", "event")
            desc = e.get("desc", "")
            lines.append(f"Turn {turn}: [{player}] {etype} - {desc}")
        return "\n".join(lines)
