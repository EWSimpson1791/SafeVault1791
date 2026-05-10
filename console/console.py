"""console.py

Minimal console UI placeholder. Real UI will render game state and accept
player input. For now it exposes a single function to print a short status.
"""

from typing import Dict, Any

def show_status(game_state: Dict[str, Any]) -> None:
    """Print a compact status summary (placeholder)."""
    print("Game status (placeholder):", game_state.get("name", "unnamed"))
