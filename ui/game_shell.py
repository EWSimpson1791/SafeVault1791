# ui/game_shell.py
"""
Text-based Game Shell for Risk Battle Game A
Adds ANSI color polish and a simple loading spinner for resource operations.
"""

import sys
import time
import threading
from typing import Any, Callable

# ANSI escape sequences (works in most terminals)
CSI = "\033["
RESET = CSI + "0m"
BOLD = CSI + "1m"
FG_CYAN = CSI + "36m"
FG_YELLOW = CSI + "33m"
FG_GREEN = CSI + "32m"
FG_MAGENTA = CSI + "35m"
FG_RED = CSI + "31m"

# Spinner control
_spinner_running = False
_spinner_thread: threading.Thread | None = None


def _spinner(text: str = "Loading", delay: float = 0.08) -> None:
    """Internal spinner loop; runs in a background thread while _spinner_running is True."""
    frames = ["|", "/", "-", "\\"]
    idx = 0
    try:
        while _spinner_running:
            frame = frames[idx % len(frames)]
            sys.stdout.write(f"\r{FG_CYAN}{text} {frame}{RESET}")
            sys.stdout.flush()
            time.sleep(delay)
            idx += 1
    finally:
        # clear spinner line when done
        sys.stdout.write("\r" + " " * (len(text) + 4) + "\r")
        sys.stdout.flush()


def start_spinner(text: str = "Loading") -> None:
    """Start spinner in a background thread. Call stop_spinner() to stop."""
    global _spinner_running, _spinner_thread
    if _spinner_running:
        return
    _spinner_running = True
    _spinner_thread = threading.Thread(target=_spinner, args=(text,), daemon=True)
    _spinner_thread.start()


def stop_spinner() -> None:
    """Stop the background spinner and wait briefly for the thread to clear the line."""
    global _spinner_running, _spinner_thread
    if not _spinner_running:
        return
    _spinner_running = False
    # Give the spinner thread a moment to exit and clear the line
    if _spinner_thread is not None:
        _spinner_thread.join(timeout=0.2)
    # small pause to ensure terminal state is stable
    time.sleep(0.02)
    _spinner_thread = None


def show_title_screen() -> None:
    """Display the colored title/splash screen."""
    print(FG_MAGENTA + BOLD + r"""
┌──────────────────────────────────────────────────────────┐
│                                                          │
│                RISK BATTLE GAME A                        │
│                    Version 0.1                           │
│                                                          │
│        A Turn-Based Strategy Simulation Engine           │
│                                                          │
└──────────────────────────────────────────────────────────┘
""" + RESET)
    print(FG_YELLOW + "Type a command and press Enter. Try 'play' to begin." + RESET)
    print()


def game_shell() -> str:
    """
    Risk Game Shell (text-based UI).
    Returns one of: "play", "rules", "credits", "exit"
    """
    show_title_screen()

    while True:
        print(BOLD + FG_GREEN + "Commands:" + RESET)
        print(FG_CYAN + "  play       " + RESET + "Begin a new game")
        print(FG_CYAN + "  rules      " + RESET + "View rules")
        print(FG_CYAN + "  credits    " + RESET + "About the game")
        print(FG_CYAN + "  exit       " + RESET + "Quit")
        print()

        try:
            cmd = input(FG_YELLOW + "> " + RESET).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return "exit"

        if cmd == "play":
            return "play"

        elif cmd == "rules":
            show_rules()

        elif cmd == "credits":
            show_credits()

        elif cmd == "exit":
            return "exit"

        else:
            print(FG_RED + "Unknown command. Try again." + RESET)
            print()


def show_rules() -> None:
    """Print the game rules."""
    print(BOLD + FG_MAGENTA + "\n=== GAME RULES ===" + RESET)
    print(FG_YELLOW + "• Capture all territories to win." + RESET)
    print(FG_YELLOW + "• Each turn has 3 phases:" + RESET)
    print(FG_CYAN + "    1. Reinforce" + RESET)
    print(FG_CYAN + "    2. Attack" + RESET)
    print(FG_CYAN + "    3. Fortify" + RESET)
    print(FG_YELLOW + "• Dice rolls determine battle outcomes." + RESET)
    print(FG_YELLOW + "• More detailed rules will be added as the engine evolves.\n" + RESET)


def show_credits() -> None:
    """Print credits."""
    print(BOLD + FG_MAGENTA + "\n=== CREDITS ===" + RESET)
    print(FG_YELLOW + "Risk Battle Game A" + RESET)
    print(FG_YELLOW + "Designed and implemented by Eugene Wendell Simpson" + RESET)
    print(FG_YELLOW + "Text-based prototype version\n" + RESET)


def load_with_spinner(func: Callable[..., Any], *args: Any, text: str = "Loading", **kwargs: Any) -> Any:
    """
    Run func(*args, **kwargs) while showing a spinner.
    Returns the function result or re-raises the same exception.
    """
    start_spinner(text)
    try:
        return func(*args, **kwargs)
    finally:
        stop_spinner()
