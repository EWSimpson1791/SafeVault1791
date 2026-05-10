# ui/ascii_map.py
"""
Simple ASCII map renderer.

Expect game_state["map_layout"] to be a list of strings where tokens are:
  - "T:NAME" for a territory cell
  - "." or other tokens for empty space or separators

Example layout:
  ["T:A T:B . T:C", " . T:D T:E ."]
"""

from typing import Any
from ui.console import color_text

def render_ascii_map(game_state: Any) -> str:
    layout = game_state.get("map_layout", []) if isinstance(game_state, dict) else []
    terrs = game_state.get("territories", {}) if isinstance(game_state, dict) else {}
    rows = []
    for row in layout:
        cells = []
        for token in row.split():
            if token.startswith("T:"):
                name = token[2:]
                info = terrs.get(name, {}) or {}
                owner = info.get("owner")
                armies = info.get("armies", 0) or 0
                # short cell: NAME(armies) truncated to 6 chars for compactness
                cell_text = f"{name[:2]}({armies})"
                role = "player" if owner else "info"
                cells.append(color_text(cell_text, role))
            else:
                cells.append(token)
        rows.append(" ".join(cells))
    return "\n".join(rows)
