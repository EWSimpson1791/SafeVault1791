# tests/test_main_auth.py
import builtins
from unittest import mock
import importlib
import main.main as main_mod

def test_main_uses_authenticate(monkeypatch, tmp_path):
    # Mock authenticate to return True
    monkeypatch.setattr(main_mod, "authenticate", lambda u, p: True)
    monkeypatch.setattr(main_mod, "login", None)
    # Mock input to supply username/password if needed
    monkeypatch.setattr(builtins, "input", lambda prompt="": "dummy")
    # Mock load_and_validate and initialize_game_from_map to avoid file IO
    monkeypatch.setattr(main_mod, "load_and_validate", lambda p: {"name": "map"})
    monkeypatch.setattr(main_mod, "create_players", lambda names: {"Alice": {}, "Bob": {}})
    monkeypatch.setattr(main_mod, "initialize_game_from_map", lambda m, p: {"map_name": "map"})
    # Run main (should not raise)
    main_mod.main()
