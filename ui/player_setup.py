# ui/player_setup.py
"""
Player setup UI for Risk Battle Game A.

Provides an interactive, validated flow to:
- choose number of players
- enter unique player names
- choose player type (human or AI)
- assign a color from a palette (auto-assigned by default)

Returns a list of player descriptors:
[
    {"name": "Alice", "type": "human", "color": "red"},
    {"name": "Bot-1", "type": "ai", "color": "blue"},
    ...
]
"""

from typing import List, Dict, Tuple

DEFAULT_MIN_PLAYERS = 2
DEFAULT_MAX_PLAYERS = 6
COLOR_PALETTE = ["red", "blue", "green", "yellow", "magenta", "cyan"]


def _prompt_int(prompt: str, min_v: int, max_v: int, default: int) -> int:
    while True:
        raw = input(f"{prompt} [{default}]: ").strip()
        if raw == "":
            return default
        if not raw.isdigit():
            print("Please enter a number.")
            continue
        val = int(raw)
        if val < min_v or val > max_v:
            print(f"Please enter a number between {min_v} and {max_v}.")
            continue
        return val


def _prompt_choice(prompt: str, choices: List[str], default: str) -> str:
    choices_str = "/".join(choices)
    while True:
        raw = input(f"{prompt} ({choices_str}) [{default}]: ").strip().lower()
        if raw == "":
            return default
        if raw in choices:
            return raw
        print(f"Invalid choice. Choose one of: {choices_str}")


def _unique_name(name: str, existing: List[str]) -> bool:
    n = name.strip()
    if n == "":
        return False
    return n.lower() not in (e.lower() for e in existing)


def _assign_colors(n: int, overrides: Dict[int, str] = None) -> List[str]:
    overrides = overrides or {}
    colors: List[str] = []
    palette = COLOR_PALETTE.copy()
    for i in range(n):
        if i in overrides:
            colors.append(overrides[i])
            # remove if present to avoid duplicates
            if overrides[i] in palette:
                palette.remove(overrides[i])
            continue
        if palette:
            colors.append(palette.pop(0))
        else:
            # fallback: generate numbered color name
            colors.append(f"color-{i+1}")
    return colors


def player_setup_interactive(
    min_players: int = DEFAULT_MIN_PLAYERS,
    max_players: int = DEFAULT_MAX_PLAYERS,
) -> List[Dict[str, str]]:
    """
    Run interactive player setup.
    Returns list of player dicts: {"name": str, "type": "human"|"ai", "color": str}
    """
    print("\n=== Player Setup ===")
    print(f"Players allowed: {min_players} to {max_players}.\n")

    default_players = min_players
    num_players = _prompt_int("Number of players", min_players, max_players, default_players)

    players: List[Dict[str, str]] = []
    existing_names: List[str] = []

    for i in range(num_players):
        # default name suggestion
        default_name = f"Player-{i+1}"
        while True:
            raw = input(f"Name for player {i+1} [{default_name}]: ").strip()
            name = raw if raw != "" else default_name
            if not _unique_name(name, existing_names):
                print("Name is empty or already used. Choose a unique name.")
                continue
            existing_names.append(name)
            break

        # choose type
        ptype = _prompt_choice("Type", ["human", "ai"], "human")

        players.append({"name": name, "type": ptype, "color": ""})

    # color assignment phase
    print("\nAssigning colors to players.")
    print("You can accept the default color or type a color name to override.")
    assigned_colors = _assign_colors(num_players)

    for idx, p in enumerate(players):
        default_color = assigned_colors[idx]
        raw = input(f"Color for {p['name']} [{default_color}]: ").strip().lower()
        color = raw if raw != "" else default_color
        # ensure uniqueness: if user picks a color already used, warn and auto-resolve
        used = [pl["color"].lower() for pl in players if pl["color"]]
        if color.lower() in used:
            print(f"Color '{color}' already used; assigning next available color.")
            # recompute available palette
            remaining = [c for c in COLOR_PALETTE if c.lower() not in used]
            color = remaining[0] if remaining else f"color-{idx+1}"
        p["color"] = color

    print("\nPlayer setup complete. Players:")
    for p in players:
        print(f" - {p['name']} ({p['type']}) color={p['color']}")

    return players


# Convenience wrapper used by main to get names only (for compatibility)
def get_player_names_from_setup() -> List[str]:
    players = player_setup_interactive()
    return [p["name"] for p in players]
