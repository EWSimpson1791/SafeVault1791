"""
Minimal interactive turn loop (human-only version).

This is the clean Step 4 baseline BEFORE any AI subsystem existed.
"""

from typing import Any, List, Tuple


# ------------------------------------------------------------
# Player order extraction
# ------------------------------------------------------------
def _get_player_order(game_state: Any) -> List[str]:
    if isinstance(game_state, dict):
        players = game_state.get("players")
        if isinstance(players, list):
            names = []
            for p in players:
                if isinstance(p, dict) and "name" in p:
                    names.append(str(p["name"]))
            if names:
                return names

        order = game_state.get("player_order")
        if isinstance(order, list) and all(isinstance(x, str) for x in order):
            return order[:]

    # Object-based
    try:
        players_attr = getattr(game_state, "players", None)
        if players_attr:
            names = []
            for p in players_attr:
                name = getattr(p, "name", None)
                if name:
                    names.append(str(name))
            if names:
                return names
    except Exception:
        pass

    return []


# ------------------------------------------------------------
# Fallback status printing
# ------------------------------------------------------------
def _print_status(game_state: Any, current_player: str) -> None:
    print("\n=== Game Status ===")
    print(f"Current player: {current_player}")

    try:
        if isinstance(game_state, dict):
            territories = game_state.get("territories")
            if isinstance(territories, dict):
                counts = {}
                for info in territories.values():
                    owner = info.get("owner") if isinstance(info, dict) else None
                    if owner:
                        counts[owner] = counts.get(owner, 0) + 1
                if counts:
                    print("Territories owned:")
                    for p, c in counts.items():
                        print(f"  {p}: {c}")
    except Exception:
        pass

    print("===================\n")


# ------------------------------------------------------------
# Command parsing
# ------------------------------------------------------------
def _parse_command(cmd: str) -> Tuple[str, List[str]]:
    tokens = cmd.strip().split()
    if not tokens:
        return "", []
    verb = tokens[0].lower()
    args = tokens[1:]
    return verb, args


# ------------------------------------------------------------
# Victory detection
# ------------------------------------------------------------
def _maybe_check_victory(game_state: Any) -> bool:
    try:
        from engine.game_rules import check_victory
    except Exception:
        return False

    try:
        winner = check_victory(game_state)
    except Exception:
        return False

    if winner:
        print(f"Game over. Winner: {winner}")
        return True

    # Optional elimination reporting
    try:
        from engine.game_rules import check_eliminations
        eliminated = check_eliminations(game_state)
        for p, is_elim in eliminated.items():
            if is_elim:
                print(f"Player eliminated: {p}")
    except Exception:
        pass

    return False


# ------------------------------------------------------------
# Main game loop
# ------------------------------------------------------------
def game_loop(game_state: Any) -> None:
    player_order = _get_player_order(game_state)
    if not player_order:
        print("No player order found in game_state. Cannot start loop.")
        return

    idx = 0
    print("Entering game loop. Type 'help' for commands.\n")

    while True:
        current = player_order[idx % len(player_order)]

        # Compute pending reinforcements at start of player's turn
        try:
            pending_map = game_state.setdefault("pending_reinforcements", {})
            if pending_map.get(current, 0) == 0:
                try:
                    from engine.reinforcement import calculate_reinforcements
                    pending = calculate_reinforcements(game_state, current)
                except Exception:
                    pending = 0
                pending_map[current] = pending
                if pending > 0:
                    print(f"{current} receives {pending} reinforcement armies to place.")
        except Exception:
            pass

        try:
            raw = input(f"[{current}]> ")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting game loop.")
            break

        verb, args = _parse_command(raw.strip())

        # End turn
        if verb == "" or verb == "end":
            idx += 1
            print(f"Ending {current}'s turn. Next player: {player_order[idx % len(player_order)]}")
            continue

        # Status
        if verb == "status":
            try:
                from ui.status import format_status
                print(format_status(game_state, current))
            except Exception:
                _print_status(game_state, current)
            continue

        # Help
        if verb == "help":
            print("Commands:")
            print("  status")
            print("  attack <from> <to> <armies>")
            print("  reinforce <territory> <armies>")
            print("  fortify <from> <to> <armies>")
            print("  end (or Enter) - end your turn")
            print("  quit")
            continue

        # Quit
        if verb == "quit":
            print("Quitting game loop.")
            break

        # Attack
        if verb == "attack":
            if len(args) < 3:
                print("Usage: attack <from> <to> <armies>")
                continue

            from_t, to_t, armies_s = args[0], args[1], args[2]

            try:
                armies = int(armies_s)
            except ValueError:
                print("Invalid armies count.")
                continue

            try:
                from engine.actions import attack as attack_action
                res = attack_action.attack(game_state, current, from_t, to_t, armies)
            except Exception as exc:
                print(f"Attack failed with exception: {exc}")
                continue

            if not res.get("ok"):
                print(f"Attack failed: {res.get('error')}")
            else:
                print(f"Attack result: {res.get('result')}")

            if _maybe_check_victory(game_state):
                break
            continue

        # Reinforce
        if verb == "reinforce":
            if len(args) < 2:
                print("Usage: reinforce <territory> <armies>")
                continue

            terr, armies_s = args[0], args[1]

            try:
                armies = int(armies_s)
            except ValueError:
                print("Invalid armies count.")
                continue

            pending = game_state.get("pending_reinforcements", {}).get(current, 0)
            if pending <= 0:
                print("No pending reinforcements to place.")
                continue
            if armies > pending:
                print(f"You only have {pending} armies to place.")
                continue

            try:
                from engine.reinforcement import apply_reinforcements
                res = apply_reinforcements(game_state, current, terr, armies)
            except Exception as exc:
                print(f"Reinforce failed with exception: {exc}")
                continue

            if not res.get("ok"):
                print(f"Reinforce failed: {res.get('error')}")
            else:
                game_state["pending_reinforcements"][current] = pending - armies
                print(f"Reinforce result: {res.get('result')}")

                remaining = game_state["pending_reinforcements"][current]
                if remaining > 0:
                    print(f"{remaining} reinforcement armies remaining to place.")
                else:
                    print("All reinforcements placed.")
            continue

        # Fortify
        if verb == "fortify":
            if len(args) < 3:
                print("Usage: fortify <from> <to> <armies>")
                continue

            from_t, to_t, armies_s = args[0], args[1], args[2]

            try:
                armies = int(armies_s)
            except ValueError:
                print("Invalid armies count.")
                continue

            try:
                from engine.actions import fortify as fortify_action
                res = fortify_action.fortify(game_state, current, from_t, to_t, armies)
            except Exception as exc:
                print(f"Fortify failed with exception: {exc}")
                continue

            if not res.get("ok"):
                print(f"Fortify failed: {res.get('error')}")
            else:
                print(f"Fortify result: {res.get('result')}")
            continue

        print("Unknown command. Type 'help' for available commands.")
