"""
main.py

Entry point for Risk_Battle_Game_A.
Handles login, map loading, player creation, and game initialization.
"""

from pathlib import Path
from typing import Any, List

from data import load_and_validate
from engine.setup.game_initializer import initialize_game_from_map
from players.player_manager import create_players

from ui.game_shell import game_shell
from auth.auth_manager import auth_menu
from ui.player_setup import player_setup_interactive
from ui.game_loop import game_loop


def _extract_player_names(created_players: Any) -> List[str]:
    """
    Normalize the output of create_players into a list of player names.

    Accepts:
      - dict mapping name -> player object
      - list of names (list[str])
      - list of player descriptors (list[dict] with 'name' key)
    Raises ValueError if the structure is not recognized.
    """
    if isinstance(created_players, dict):
        return list(created_players.keys())

    if isinstance(created_players, list):
        # list of names?
        if all(isinstance(x, str) for x in created_players):
            return created_players[:]  # shallow copy

        # list of descriptors?
        if all(isinstance(x, dict) and "name" in x for x in created_players):
            return [str(x["name"]) for x in created_players]

    raise ValueError("Unexpected player structure returned from create_players().")


def main() -> None:
    """Start the application: require login, show shell, load map, create players, initialize engine."""
    print("=== Risk Battle Game A ===")

    # Authentication
    try:
        auth_ok = auth_menu()
    except Exception as exc:
        print("Authentication subsystem error:", exc)
        return

    if not auth_ok:
        print("Exiting game.")
        return

    # Optional title/shell
    try:
        choice = game_shell()
    except Exception as exc:
        print("Game shell error:", exc)
        return

    if choice == "exit":
        print("Goodbye.")
        return

    # Player setup (only when user chose to play)
    player_names: List[str] = []
    if choice == "play":
        print("\nStarting player setup...\n")
        try:
            players_info = player_setup_interactive()
        except Exception as exc:
            print("Player setup failed:", exc)
            return

        # Normalize players_info into List[str]
        if isinstance(players_info, list) and all(isinstance(x, str) for x in players_info):
            player_names = list(players_info)
        elif isinstance(players_info, list) and all(isinstance(x, dict) and "name" in x for x in players_info):
            player_names = [str(d["name"]) for d in players_info]
        else:
            print("Unexpected player setup result; aborting.")
            return

    # Load map data
    map_path = Path("data/risk_map.json")
    if not map_path.exists():
        print(f"Map file not found: {map_path}")
        return

    try:
        map_data = load_and_validate(map_path)
    except Exception as exc:
        print("Failed to load/validate map:", exc)
        return

    # Create players using the player manager
    try:
        if player_names:
            created_players = create_players(player_names)
        else:
            # fallback default players
            created_players = create_players(["Alice", "Bob"])
    except Exception as exc:
        print("Failed to create players:", exc)
        return

    # Extract player names for engine initialization
    try:
        player_names_for_init = _extract_player_names(created_players)
    except Exception as exc:
        print("Failed to extract player names:", exc)
        return

    if not player_names_for_init:
        print("No player names available for initialization; aborting.")
        return

    # Initialize game engine
    try:
        init = initialize_game_from_map(map_data, player_names_for_init)
    except Exception as exc:
        print("Failed to initialize game:", exc)
        return

    print("Initialization complete:", init)

    # Start the interactive game loop using the initialized game state
    try:
        game_loop(init)
    except Exception as exc:
        print("Game loop terminated with an error:", exc)


if __name__ == "__main__":
    main()


