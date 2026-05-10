# ai/decision_example.py
"""
Example AI decision engine for Risk_Battle_Game_A.

Provides a single public function:
    decide_action(game_state, player_name, difficulty=None) -> dict

The function returns an action dict compatible with the engine.actions adapters:
  - attack:   {"type":"attack", "from":"A", "to":"B", "armies":3}
  - reinforce:{"type":"reinforce", "territory":"A", "armies":2}
  - fortify:  {"type":"fortify", "from":"A", "to":"C", "armies":2}
  - end/pass: {"type":"end"}

This example is intentionally simple, readable, and easy to extend.
"""

import random
from typing import Any, Dict, List, Optional, Tuple


def _owned_territories(game_state: Any, player: str) -> List[str]:
    try:
        terr = game_state.get("territories", {})
        return [name for name, info in terr.items() if isinstance(info, dict) and info.get("owner") == player]
    except Exception:
        return []


def _territory_info(game_state: Any, name: str) -> Dict[str, Any]:
    try:
        return game_state.get("territories", {}).get(name, {}) or {}
    except Exception:
        return {}


def _neighbors(game_state: Any, name: str) -> List[str]:
    return list(_territory_info(game_state, name).get("neighbors", []) or [])


def _armies(game_state: Any, name: str) -> int:
    try:
        return int(_territory_info(game_state, name).get("armies", 0))
    except Exception:
        return 0


def _legal_attacks(game_state: Any, player: str) -> List[Dict[str, Any]]:
    actions = []
    for src in _owned_territories(game_state, player):
        src_arm = _armies(game_state, src)
        if src_arm <= 1:
            continue
        for dst in _neighbors(game_state, src):
            dst_info = _territory_info(game_state, dst)
            if not isinstance(dst_info, dict):
                continue
            if dst_info.get("owner") == player:
                continue
            # allow attacking with up to src_arm - 1, but cap to 3 for simplicity
            max_attack = max(1, min(3, src_arm - 1))
            for a in range(1, max_attack + 1):
                actions.append({"type": "attack", "from": src, "to": dst, "armies": a})
    return actions


def _legal_reinforces(game_state: Any, player: str) -> List[Dict[str, Any]]:
    actions = []
    for t in _owned_territories(game_state, player):
        for a in (1, 2, 3):
            actions.append({"type": "reinforce", "territory": t, "armies": a})
    return actions


def _legal_fortifies(game_state: Any, player: str) -> List[Dict[str, Any]]:
    actions = []
    owned = _owned_territories(game_state, player)
    for src in owned:
        src_arm = _armies(game_state, src)
        if src_arm <= 1:
            continue
        for dst in owned:
            if dst == src:
                continue
            for a in (1, 2):
                actions.append({"type": "fortify", "from": src, "to": dst, "armies": a})
    return actions


def _score_attack(game_state: Any, action: Dict[str, Any]) -> float:
    """
    Score an attack: prefer low-defender armies and larger attacking force.
    Higher score = more attractive.
    """
    dst = action.get("to")
    atk = int(action.get("armies", 0))
    def_arm = _armies(game_state, dst)
    # prefer attacks where attacker has advantage; penalize high defender armies
    score = (atk * 2.0) - (def_arm * 1.5)
    # small bonus for capturing border to many enemy neighbors (strategic)
    try:
        enemy_neighbors = sum(
            1 for n in _neighbors(game_state, dst)
            if _territory_info(game_state, n).get("owner") != _territory_info(game_state, action.get("from")).get("owner")
        )
        score += 0.1 * enemy_neighbors
    except Exception:
        pass
    return score


def _choose_attack(game_state: Any, player: str, attacks: List[Dict[str, Any]], difficulty: str) -> Optional[Dict[str, Any]]:
    if not attacks:
        return None
    if difficulty == "easy":
        # random small attacks or end
        return random.choice(attacks + [{"type": "end"}] * 2)
    if difficulty == "medium":
        # prefer attacks with positive score, otherwise random
        scored = sorted((( _score_attack(game_state, a), a) for a in attacks), key=lambda x: x[0], reverse=True)
        best_score, best_action = scored[0]
        if best_score > 0:
            return best_action
        return random.choice(attacks + [{"type": "end"}])
    # hard
    scored = sorted((( _score_attack(game_state, a), a) for a in attacks), key=lambda x: x[0], reverse=True)
    # pick among top 3 scored actions to add variety
    top = [a for s, a in scored[:3]] if scored else []
    return random.choice(top) if top else random.choice(attacks)


def _choose_reinforce(game_state: Any, player: str, reinforces: List[Dict[str, Any]], difficulty: str) -> Optional[Dict[str, Any]]:
    if not reinforces:
        return None
    if difficulty == "easy":
        return random.choice(reinforces + [{"type": "end"}])
    # medium/hard: reinforce weakest owned territory
    owned = _owned_territories(game_state, player)
    if not owned:
        return random.choice(reinforces)
    weakest = min(owned, key=lambda t: _armies(game_state, t))
    # pick a reinforce action that targets weakest if available
    for r in reinforces:
        if r.get("territory") == weakest:
            return r
    return random.choice(reinforces)


def _choose_fortify(game_state: Any, player: str, fortifies: List[Dict[str, Any]], difficulty: str) -> Optional[Dict[str, Any]]:
    if not fortifies:
        return None
    if difficulty == "easy":
        return random.choice(fortifies + [{"type": "end"}])
    # medium/hard: move from strongest to weakest owned territory if possible
    owned = _owned_territories(game_state, player)
    if len(owned) < 2:
        return random.choice(fortifies)
    strongest = max(owned, key=lambda t: _armies(game_state, t))
    weakest = min(owned, key=lambda t: _armies(game_state, t))
    for f in fortifies:
        if f.get("from") == strongest and f.get("to") == weakest:
            return f
    return random.choice(fortifies)


def decide_action(game_state: Any, player_name: str, difficulty: Optional[str] = None) -> Dict[str, Any]:
    """
    Public API. Returns a single action dict.
    difficulty: "easy", "medium", "hard" (defaults to medium)
    """
    diff = (str(difficulty).lower() if difficulty else "medium")
    if diff not in ("easy", "medium", "hard"):
        diff = "medium"

    # Build legal action lists
    attacks = _legal_attacks(game_state, player_name)
    reinforces = _legal_reinforces(game_state, player_name)
    fortifies = _legal_fortifies(game_state, player_name)

    # Decision priority by difficulty:
    # - easy: often reinforce or end, occasional attack/fortify
    # - medium: reinforce if weak, else attack, else fortify
    # - hard: prefer high-value attacks, then reinforce, then fortify

    if diff == "easy":
        pool = []
        pool.extend(reinforces * 3)
        pool.extend(fortifies * 1)
        pool.extend(attacks * 1)
        pool.append({"type": "end"})
        return random.choice(pool) if pool else {"type": "end"}

    if diff == "medium":
        # if any owned territory has <=2 armies, reinforce it
        for t in _owned_territories(game_state, player_name):
            if _armies(game_state, t) <= 2 and reinforces:
                for r in reinforces:
                    if r.get("territory") == t:
                        return r
        # otherwise try a reasonable attack
        attack_choice = _choose_attack(game_state, player_name, attacks, diff)
        if attack_choice:
            return attack_choice
        # else reinforce or fortify
        reinforce_choice = _choose_reinforce(game_state, player_name, reinforces, diff)
        if reinforce_choice:
            return reinforce_choice
        fort_choice = _choose_fortify(game_state, player_name, fortifies, diff)
        if fort_choice:
            return fort_choice
        return {"type": "end"}

    # hard
    attack_choice = _choose_attack(game_state, player_name, attacks, diff)
    if attack_choice:
        return attack_choice
    reinforce_choice = _choose_reinforce(game_state, player_name, reinforces, diff)
    if reinforce_choice:
        return reinforce_choice
    fort_choice = _choose_fortify(game_state, player_name, fortifies, diff)
    if fort_choice:
        return fort_choice

    return {"type": "end"}
