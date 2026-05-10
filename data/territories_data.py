"""
territories_data.py
Lightweight Python access to the map data for tests and engine bootstrapping.
No side effects on import.
"""

from pathlib import Path
import json
from typing import Dict, List

DATA_DIR = Path(__file__).parent
DEFAULT_MAP_FILE = DATA_DIR / "risk_map.json"

def load_map(path: Path = DEFAULT_MAP_FILE) -> Dict:
    """Load and return the JSON map as a Python dict."""
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def get_territories(map_data: Dict = None) -> Dict[str, Dict]:
    """Return the territories mapping from the loaded map."""
    if map_data is None:
        map_data = load_map()
    return map_data.get("territories", {})

def get_continents(map_data: Dict = None) -> Dict[str, Dict]:
    """Return the continents mapping from the loaded map."""
    if map_data is None:
        map_data = load_map()
    return map_data.get("continents", {})

def adjacency_list(territory_name: str, map_data: Dict = None) -> List[str]:
    """Return adjacency list for a territory. Returns empty list if unknown."""
    territories = get_territories(map_data)
    return territories.get(territory_name, {}).get("adjacent", []).copy()
