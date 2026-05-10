"""game_state.py

Lightweight container for the global game state. This is a placeholder
class used by other engine modules. Implement state mutation methods later.
"""

from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class GameState:
    """Minimal game state container."""
    players: Dict[str, Any] = field(default_factory=dict)
    territories: Dict[str, Any] = field(default_factory=dict)
    turn_order: list = field(default_factory=list)
    current_turn_index: int = 0

    def snapshot(self) -> Dict[str, Any]:
        """Return a shallow snapshot of the state for debugging/tests."""
        return {
            "players": list(self.players.keys()),
            "territories_count": len(self.territories),
            "turn_index": self.current_turn_index,
        }
