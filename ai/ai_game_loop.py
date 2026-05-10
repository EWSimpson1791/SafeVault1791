# ai/ai_game_loop.py
"""
AI-only game loop.

This loop is separate from the human UI loop. It iterates AI players,
asks the decision engine for an action, executes the action via engine.actions,
and advances turns automatically.
"""

import random
import time
from typing import Any, Dict, List, Optional

try:
    from engine.actions import attack as attack_action  # type: ignore
    from engine.actions import reinforce as reinforce_action  # type: ignore
    from engine.actions import fortify as fortify_action  # type: ignore
except Exception:
    attack_action = None  # type: ignore
    reinforce_action = None  # type: ignore
    fortify_action = None  # type: ignore

# Decision API expected: decide_action(game_state, player_name, difficulty) -> dict with keys: type, from, to, armies
try:
    from ai.decision import decide_action  # type: ignore
except Exception:
    decide_action = None  # type: ignore


def _ai_players_in_order(game_state: Any) -> List[str]:
    players = []
    try:
        p_list = game_state.get("players", [])
        for p in p_list:
            if isinstance(p, dict) and p.get("type", "").lower() == "ai":
                players.append(str(p.get("name")))
    except Exception:
        pass
    return players


def _player_difficulty(game_state: Any, player_name: str) -> Optional[str]:
    try:
        p_list = game_state.get("players", [])
        for p in p_list:
            if isinstance(p, dict) and p.get("name") == player_name:
                return p.get("difficulty")
    except Exception:
        pass
    return None


def _execute_action(game_state: Any, player_name: str, action: Dict[str, Any]) -> None:
    if not action or not isinstance(action, dict):
        print(f"[{player_name}] No action returned by decision engine.")
        return

    typ = action.get("type", "").lower()
    try:
        if typ == "attack" and attack_action:
            res = attack_action.attack(game_state, player_name, action.get("from"), action.get("to"), int(action.get("armies", 0)))
            print(f"[{player_name}] attack -> {res}")
        elif typ == "reinforce" and reinforce_action:
            res = reinforce_action.reinforce(game_state, player_name, action.get("territory"), int(action.get("armies", 0)))
            print(f"[{player_name}] reinforce -> {res}")
        elif typ == "fortify" and fortify_action:
            res = fortify_action.fortify(game_state, player_name, action.get("from"), action.get("to"), int(action.get("armies", 0)))
            print(f"[{player_name}] fortify -> {res}")
        elif typ in ("end", "pass", ""):
            print(f"[{player_name}] ends turn.")
        else:
            print(f"[{player_name}] Unknown action type: {typ}")
    except Exception as exc:
        print(f"[{player_name}] Action execution error: {exc}")


def ai_game_loop(game_state: Any, loop_delay: float = 0.5, jitter: float = 0.3, max_rounds: Optional[int] = None) -> None:
    """
    Run the AI loop until stopped or until max_rounds is reached.
    - loop_delay base seconds between AI turns
    - jitter randomizes delay to avoid perfectly deterministic timing
    - max_rounds optional limit to avoid infinite runs during tests
    """
    ai_players = _ai_players_in_order(game_state)
    if not ai_players:
        print("No AI players found. AI loop will not start.")
        return

    print("Starting AI game loop for players:", ai_players)
    round_count = 0
    idx = 0

    while True:
        if max_rounds is not None and round_count >= max_rounds:
            print("AI loop reached max_rounds, stopping.")
            break

        current = ai_players[idx % len(ai_players)]
        difficulty = _player_difficulty(game_state, current)

        # Simulate thinking time with jitter
        delay = loop_delay + random.uniform(-jitter, jitter)
        if delay > 0:
            time.sleep(delay)

        # Ask decision engine
        if decide_action is None:
            print("Decision engine not available. AI cannot act.")
            break

        try:
            action = decide_action(game_state, current, difficulty)
        except Exception as exc:
            print(f"[{current}] Decision engine error: {exc}")
            action = {"type": "end"}

        _execute_action(game_state, current, action)

        # Advance to next AI player
        idx += 1
        # If we cycled through all AI players, increment round counter
        if idx % len(ai_players) == 0:
            round_count += 1

        # Optional: break if victory detected by engine.game_rules
        try:
            from engine.game_rules import check_victory  # local import
            winner = check_victory(game_state)
            if winner:
                print(f"Game over. Winner: {winner}")
                break
        except Exception:
            pass
