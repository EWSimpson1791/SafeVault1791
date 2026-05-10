# engine/reinforcement.py
from typing import Any, Dict, Optional


def _territory_count(game_state: Any, player_name: str) -> int:
    try:
        terr = game_state.get("territories", {})
        return sum(1 for _, info in terr.items() if isinstance(info, dict) and info.get("owner") == player_name)
    except Exception:
        return 0


def continent_bonus(game_state: Any, player_name: str) -> int:
    """
    Optional: compute continent control bonus.
    Return 0 if no continent bonuses are configured.
    Expected game_state["continents"] shape:
      { "North America": {"territories": ["A","B",...], "bonus": 5}, ... }
    """
    try:
        continents = game_state.get("continents", {})
        if not isinstance(continents, dict):
            return 0
        bonus = 0
        for cinfo in continents.values():
            if not isinstance(cinfo, dict):
                continue
            terrs = cinfo.get("territories", [])
            if not isinstance(terrs, list):
                continue
            # player controls continent if all territories owned by player
            owns_all = True
            for t in terrs:
                tinfo = game_state.get("territories", {}).get(t, {})
                if not isinstance(tinfo, dict) or tinfo.get("owner") != player_name:
                    owns_all = False
                    break
            if owns_all:
                bonus += int(cinfo.get("bonus", 0))
        return bonus
    except Exception:
        return 0


def calculate_reinforcements(game_state: Any, player_name: str) -> int:
    """
    Standard Risk rule:
      base = max(3, floor(territories_owned / 3))
    plus continent bonuses and any custom modifiers in game_state.
    """
    try:
        terr_count = _territory_count(game_state, player_name)
        base = terr_count // 3
        if base < 3:
            base = 3
        bonus = continent_bonus(game_state, player_name)
        # Allow custom modifiers in game_state, e.g., game_state.get("rules", {}).get("extra_reinforcements", {}).get(player_name, 0)
        extra = 0
        rules = game_state.get("rules", {}) if isinstance(game_state, dict) else {}
        if isinstance(rules, dict):
            extra_map = rules.get("extra_reinforcements", {})
            if isinstance(extra_map, dict):
                extra = int(extra_map.get(player_name, 0) or 0)
        total = int(base + bonus + extra)
        return max(0, total)
    except Exception:
        return 0


def apply_reinforcements(game_state: Any, player_name: str, territory: str, armies: int) -> Dict[str, Any]:
    """
    Apply reinforcement armies to a territory owned by player_name.
    Returns a result dict similar to your action adapters:
      {"ok": True, "result": "..."} or {"ok": False, "error": "..."}
    """
    try:
        if armies <= 0:
            return {"ok": False, "error": "armies must be positive"}
        terr = game_state.get("territories", {})
        if territory not in terr:
            return {"ok": False, "error": "unknown territory"}
        info = terr.get(territory)
        if not isinstance(info, dict):
            return {"ok": False, "error": "invalid territory data"}
        if info.get("owner") != player_name:
            return {"ok": False, "error": "territory not owned by player"}
        # mutate armies count
        current = int(info.get("armies", 0) or 0)
        info["armies"] = current + int(armies)
        # persist back (if game_state uses nested dicts this is enough)
        terr[territory] = info
        game_state["territories"] = terr
        return {"ok": True, "result": {"territory": territory, "armies": info["armies"]}}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
