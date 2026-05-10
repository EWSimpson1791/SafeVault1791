# engine/actions/reinforce.py
from typing import Any, Dict

def _fallback_reinforce(game_state: Any, player: str, territory: str, armies: int) -> Dict[str, Any]:
    if not isinstance(armies, int) or armies < 1:
        return {"ok": False, "error": "armies must be a positive integer"}
    territories = game_state.get("territories", {})
    terr = territories.get(territory)
    if not terr:
        return {"ok": False, "error": "invalid territory"}
    if terr.get("owner") != player:
        return {"ok": False, "error": "player does not own territory"}

    terr["armies"] = terr.get("armies", 0) + armies
    return {"ok": True, "result": {"territory": territory, "armies": terr["armies"]}}

def reinforce(game_state: Any, player: str, territory: str, armies: int) -> Dict[str, Any]:
    try:
        from engine.legacy import reinforce as legacy_reinforce  # type: ignore
        if hasattr(legacy_reinforce, "reinforce"):
            return legacy_reinforce.reinforce(game_state, player, territory, armies)
    except Exception:
        pass

    return _fallback_reinforce(game_state, player, territory, armies)
