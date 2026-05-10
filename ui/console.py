# ui/console.py
"""
Small console helper for colorized output with a safe fallback when colorama is missing.
"""

from typing import Any

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    _COLORS = {
        "player": Fore.CYAN,
        "enemy": Fore.RED,
        "info": Fore.GREEN,
        "warning": Fore.YELLOW,
        "error": Fore.RED + Style.BRIGHT,
        "title": Fore.MAGENTA + Style.BRIGHT,
    }
    _RESET = Style.RESET_ALL
except Exception:
    # Fallback: no colors available
    _COLORS = {k: "" for k in ("player", "enemy", "info", "warning", "error", "title")}
    _RESET = ""

def color_text(text: str, role: str = "info") -> str:
    """
    Return text wrapped in a color code for the given role.
    Roles: player, enemy, info, warning, error, title
    """
    color = _COLORS.get(role, "")
    return f"{color}{text}{_RESET}"
