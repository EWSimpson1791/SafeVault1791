# engine/actions/attack.py
from typing import Any, Dict

def _validate_attack_args(game_state: Any, attacker: str, from_terr: str, to_terr: str, armies: int) -> None:
    if not isinstance(armies, int) or armies < 1:
        raise ValueError("armies must be a positive integer")
    if not isinstance(from_terr, str) or not isinstance(to_terr, str):
        raise ValueError("territory names must be strings")

def _fallback_attack(game_state: Any, attacker: str, from_terr: str, to_terr: str, armies: int) -> Dict[str, Any]:
    territories = game_state.get("territories", {})
    src = territories.get(from_terr)
    dst = territories.get(to_terr)
    if not src or not dst:
        return {"ok": False, "error": "invalid territory"}
    if src.get("owner") != attacker:
        return {"ok": False, "error": "attacker does not own source"}
    if dst.get("owner") == attacker:
        return {"ok": False, "error": "cannot attack own territory"}
    if src.get("armies", 0) <= armies:
        return {"ok": False, "error": "not enough armies to attack (must leave one behind)"}

    # Deterministic simple resolution: attacker and defender each lose min(armies, defender_armies)
    atk = armies
    def_armies = dst.get("armies", 0)
    losses = min(atk, def_armies)
    def_armies -= losses
    atk -= losses

    # Remove used attacking armies from source (they were committed)
    src["armies"] = src.get("armies", 0) - armies

    if def_armies <= 0:
        # Attacker captures territory; move at least 1 army in (or remaining attacking armies)
        moved_in = max(1, atk)
        dst["owner"] = attacker
        dst["armies"] = moved_in
    else:
        dst["armies"] = def_armies

    return {"ok": True, "result": {"from": from_terr, "to": to_terr, "src_armies": src["armies"], "dst_armies": dst["armies"]}}

def attack(game_state: Any, attacker: str, from_terr: str, to_terr: str, armies: int) -> Dict[str, Any]:
    _validate_attack_args(game_state, attacker, from_terr, to_terr, armies)

    # Try legacy implementation if available
    try:
        from engine.legacy import attack as legacy_attack  # type: ignore
        if hasattr(legacy_attack, "attack"):
            return legacy_attack.attack(game_state, attacker, from_terr, to_terr, armies)
    except Exception:
        pass

    return _fallback_attack(game_state, attacker, from_terr, to_terr, armies)
