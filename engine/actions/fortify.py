# engine/actions/fortify.py
from typing import Any, Dict

def _fallback_fortify(game_state: Any, player: str, from_terr: str, to_terr: str, armies: int) -> Dict[str, Any]:
    if not isinstance(armies, int) or armies < 1:
        return {"ok": False, "error": "armies must be a positive integer"}
    territories = game_state.get("territories", {})
    src = territories.get(from_terr)
    dst = territories.get(to_terr)
    if not src or not dst:
        return {"ok": False, "error": "invalid territory"}
    if src.get("owner") != player or dst.get("owner") != player:
        return {"ok": False, "error": "both territories must be owned by player"}
    if src.get("armies", 0) <= armies:
        return {"ok": False, "error": "not enough armies to move (must leave one behind)"}

    src["armies"] = src.get("armies", 0) - armies
    dst["armies"] = dst.get("armies", 0) + armies
    return {"ok": True, "result": {"from": from_terr, "to": to_terr, "moved": armies}}

def fortify(game_state: Any, player: str, from_terr: str, to_terr: str, armies: int) -> Dict[str, Any]:
    try:
        from engine.legacy import fortify as legacy_fortify  # type: ignore
        if hasattr(legacy_fortify, "fortify"):
            return legacy_fortify.fortify(game_state, player, from_terr, to_terr, armies)
    except Exception:
        pass

    return _fallback_fortify(game_state, player, from_terr, to_terr, armies)
