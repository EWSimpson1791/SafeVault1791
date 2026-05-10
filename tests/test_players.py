from players.player_manager import create_players

def test_create_players():
    players = create_players(['Alice', 'Bob'])
    assert isinstance(players, dict)
    assert 'Alice' in players and 'Bob' in players
    assert players['Alice']['status'] == 'active'
