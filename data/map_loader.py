"""
map_loader.py
Utilities to load, validate, and normalize map JSON files.
Designed to be safe and deterministic for the board game engine.
"""

from pathlib import Path
from typing import Dict, Tuple, List
import json

def load_json(path: Path) -> Dict:
    """Load JSON from path and return dict."""
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def validate_map(map_data: Dict) -> Tuple[bool, List[str]]:
    """
    Validate basic map invariants.
    Returns (is_valid, errors).
    """
    errors: List[str] = []
    if not isinstance(map_data, dict):
        return False, ["Map root is not a JSON object."]
    if "territories" not in map_data:
        errors.append("Missing 'territories' key.")
        return False, errors

    territories = map_data.get("territories", {})
    if not isinstance(territories, dict):
        errors.append("'territories' must be an object mapping names to info.")
        return False, errors

    # Check adjacency symmetry and references
    for name, info in territories.items():
        if not isinstance(info, dict):
            errors.append(f"Territory '{name}' info must be an object.")
            continue
        adj = info.get("adjacent", [])
        if not isinstance(adj, list):
            errors.append(f"Territory '{name}' adjacent must be a list.")
            continue
        for neighbor in adj:
            if neighbor not in territories:
                errors.append(f"Territory '{name}' references unknown neighbor '{neighbor}'.")
            else:
                neighbor_adj = territories[neighbor].get("adjacent", [])
                if name not in neighbor_adj:
                    errors.append(f"Asymmetric adjacency: '{name}' -> '{neighbor}' but not vice versa.")

    # Check continents reference
    continents = map_data.get("continents", {})
    if not isinstance(continents, dict):
        errors.append("'continents' must be an object mapping names to info.")
    else:
        for cname, cinfo in continents.items():
            if not isinstance(cinfo, dict):
                errors.append(f"Continent '{cname}' info must be an object.")
                continue
            for t in cinfo.get("territories", []):
                if t not in territories:
                    errors.append(f"Continent '{cname}' references unknown territory '{t}'.")

    return (len(errors) == 0), errors

def load_and_validate(path: Path) -> Dict:
    """Load JSON map and validate. Raises ValueError on validation failure."""
    data = load_json(path)
    valid, errors = validate_map(data)
    if not valid:
        raise ValueError("Map validation failed: " + "; ".join(errors))
    return data
