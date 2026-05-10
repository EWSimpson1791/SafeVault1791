"""data package for Risk_Battle_Game_A

Exports stable loader and accessor functions for map data.
"""
"""data package for Risk_Battle_Game_A"""

from .territories_data import load_map, get_territories, get_continents, adjacency_list
from .map_loader import load_and_validate, validate_map

__all__ = [
    "load_map",
    "get_territories",
    "get_continents",
    "adjacency_list",
    "load_and_validate",
    "validate_map",
]
