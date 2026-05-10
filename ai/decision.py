"""
AI decision engine for Risk_Battle_Game_A.

Provides:
  - decide_action(): public API used by ai_game_loop
  - fallback decision logic with difficulty tiers
"""

import random
from typing import Any, Dict, List, Optional


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def _owned_territories(game_state: Any, player: str) -> List[str]:
    try:
        terr = game_state.get("territories", {})
        return [
            name for name, info in terr.items()
            if isinstance(info, dict) and info.get("owner") == player
        ]
    except Exception:
        return []


def _neighbors_of(game_state: Any, territory: str) -> List[str]:
    try:
        terr = game_state.get("territories", {})
        info = terr.get(territory, {})
        return list(info.get("neighbors", []) or [])
    except Exception:
        return []


def _enemy_neighbors(game_state: Any, player: str, territory: str) -> List[str]:
    enemies = []
    try:
        terr = game_state.get("territories", {})
        for n in _neighbors_of(game_state, territory):
            info = terr.get(n)
            if isinstance(info, dict) and info.get("owner") != player:
                enemies.append(n)
    except Exception:
        pass
    return enemies


def _territory_armies(game_state: Any, territory: str) -> int:
    try:
        terr = game_state.get("territories", {})
        info = terr.get(territory, {})
        return int(info.get("armies", 0))
    except Exception:
        return 0


# ------------------------------------------------------------
# Legal action generators
# ------------------------------------------------------------
def _legal_attack_actions(game_state: Any, player: str) -> List[Dict[str, Any]]:
    actions = []
    for src in _owned_territories(game_state, player):
        src_armies = _territory_armies(game_state, src)
        if src_armies <= 1:
            continue

        enemies = _enemy_neighbors(game_state, player, src)
        for dst in enemies:
            max_attack = min(3, src_armies - 1)
            for a in range(1, max_attack + 1):
                actions.append({"type": "attack", "from": src, "to": dst, "armies": a})
    return actions


def _legal_reinforce_actions(game_state: Any, player: str) -> List[Dict[str, Any]]:
    actions = []
    for t in _owned_territories(game_state, player):
        for a in (1, 2, 3):
            actions.append({"type": "reinforce", "territory": t, "armies": a})
    return actions


def _legal_fortify_actions(game_state: Any, player: str) -> List[Dict[str, Any]]:
    actions = []
    owned = _owned_territories(game_state, player)
    for src in owned:
        src_armies = _territory_armies(game_state, src)
        if src_armies <= 1:
            continue
        for dst in owned:
            if dst == src:
                continue
            for a in (1, 2):
                actions.append({"type": "fortify", "from": src, "to": dst, "armies": a})
    return actions


# ------------------------------------------------------------
# Fallback decision engine
# ------------------------------------------------------------
def _fallback_decide(game_state: Any, player: str, difficulty: Optional[str]) -> Dict[str, Any]:
    difficulty = (difficulty or "medium").lower()

    attacks = _legal_attack_actions(game_state, player)
    reinforces = _legal_reinforce_actions(game_state, player)
    fortifies = _legal_fortify_actions(game_state, player)

    # Easy: random, often end
    if difficulty == "easy":
        pool = attacks + reinforces + fortifies + [{"type": "end"}]
        return random.choice(pool)

    # Medium: reinforce weak territories, else attack
    if difficulty == "medium":
        for t in _owned_territories(game_state, player):
            if _territory_armies(game_state, t) <= 2:
                for r in reinforces:
                    if r["territory"] == t:
                        return r
        if attacks:
            return random.choice(attacks)
        if reinforces:
            return random.choice(reinforces)
        if fortifies:
            return random.choice(fortifies)
        return {"type": "end"}

    # Hard: target weakest defender
    if difficulty == "hard":
        if attacks:
            scored = [( _territory_armies(game_state, a["to"]), a ) for a in attacks]
            scored.sort(key=lambda x: x[0])
            best = [a for _, a in scored[:3]]
            return random.choice(best)

        # reinforce weakest owned territory
        if reinforces:
            terrs = sorted(
                _owned_territories(game_state, player),
                key=lambda t: _territory_armies(game_state, t)
            )
            weakest = terrs[0] if terrs else None
            if weakest:
                for r in reinforces:
                    if r["territory"] == weakest:
                        return r
            return random.choice(reinforces)

        if fortifies:
            return random.choice(fortifies)

        return {"type": "end"}

    # Unknown difficulty
    return {"type": "end"}


# ------------------------------------------------------------
# Public API
# ------------------------------------------------------------
def decide_action(game_state: Any, player_name: str, difficulty: Optional[str] = None) -> Dict[str, Any]:
    """
    Main AI decision entry point.
    """
    return _fallback_decide(game_state, player_name, difficulty)
