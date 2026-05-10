# ui/status.py
"""
Helpers to format a compact status view for the current player.
"""

from typing import Any

def format_status(game_state: Any, current_player: str) -> str:
    """
    Return a multi-line string summarizing territories, owners, armies,
    and pending reinforcements for the current player.
    """
    lines = []
    lines.append(f"Player: {current_player}")
    lines.append("")
    lines.append(f"{'Territory':<12}{'Owner':<14}{'Armies':>7}")
    lines.append("-" * 33)

    territories = game_state.get("territories", {}) if isinstance(game_state, dict) else {}
    for name in sorted(territories.keys()):
        info = territories.get(name, {}) or {}
        owner = info.get("owner") or "—"
        armies = info.get("armies") or 0
        lines.append(f"{name:<12}{str(owner):<14}{int(armies):>7}")

    pending = 0
    try:
        pending = int(game_state.get("pending_reinforcements", {}).get(current_player, 0) or 0)
    except Exception:
        pending = 0

    lines.append("")
    lines.append(f"Pending reinforcements: {pending}")
    return "\n".join(lines)
