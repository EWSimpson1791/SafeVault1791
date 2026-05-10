from pathlib import Path
from engine.setup.game_initializer import load_map, initialize_game_from_map

def test_initialize_game_from_map():
    map_path = Path('data/risk_map.json')
    map_data = load_map(map_path)
    result = initialize_game_from_map(map_data, ['Player1', 'Player2'])
    assert result['map_name'] == map_data.get('name')
    assert result['territory_count'] == len(map_data.get('territories', {}))
    assert 'players' in result
