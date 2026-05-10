# engine/game_rules.py
from typing import Any, Dict, Optional, Tuple


def _collect_player_territory_counts(game_state: Any) -> Dict[str, int]:
    """
    Return a mapping player_name -> number_of_territories.
    Works with dict-based game_state where territories is a dict of {name: {owner, armies, ...}}.
    """
    counts: Dict[str, int] = {}
    try:
        territories = game_state.get("territories", {})
        if isinstance(territories, dict):
            for info in territories.values():
                if isinstance(info, dict):
                    owner = info.get("owner")
                    if owner:
                        counts[owner] = counts.get(owner, 0) + 1
    except Exception:
        # Defensive: return whatever we have
        pass
    return counts


def check_eliminations(game_state: Any) -> Dict[str, bool]:
    """
    Return a dict mapping player_name -> eliminated_bool.
    A player is eliminated if they own zero territories.
    """
    counts = _collect_player_territory_counts(game_state)
    eliminated: Dict[str, bool] = {}
    # Gather player list from game_state players if available
    players = []
    try:
        p_list = game_state.get("players")
        if isinstance(p_list, list):
            for p in p_list:
                if isinstance(p, dict) and "name" in p:
                    players.append(str(p["name"]))
    except Exception:
        pass

    # If players list is empty, infer from territory owners
    if not players:
        players = list(counts.keys())

    for p in players:
        eliminated[p] = counts.get(p, 0) == 0

    return eliminated


def check_victory(game_state: Any) -> Optional[str]:
    """
    Return the winner's name if a single player owns all territories, otherwise None.
    Also returns a winner if only one non-eliminated player remains.
    """
    counts = _collect_player_territory_counts(game_state)
    if not counts:
        return None

    # If a single player owns all territories
    total_territories = sum(counts.values())
    for player, c in counts.items():
        if c == total_territories and total_territories > 0:
            return player

    # If only one player has territories (others eliminated)
    active_players = [p for p, c in counts.items() if c > 0]
    if len(active_players) == 1:
        return active_players[0]

    return None
