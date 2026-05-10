"""game_initializer.py

Placeholder for game setup routines: loading map, creating players, initial
troop placement. No logic here yet — just safe APIs.
"""

from pathlib import Path
from typing import Dict
from data import load_and_validate

def load_map(path: Path) -> Dict:
    """Load and validate a map JSON. Returns the parsed map dict."""
    return load_and_validate(path)

def initialize_game_from_map(map_data: Dict, player_names: list):
    """
    Create an initial GameState from map_data and player_names.
    This is a placeholder: return a dict describing what would be created.
    """
    return {
        "map_name": map_data.get("name"),
        "players": player_names,
        "territory_count": len(map_data.get("territories", {})),
    }
