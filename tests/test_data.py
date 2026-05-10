from pathlib import Path
from data import load_and_validate

def test_load_map():
    path = Path('data/risk_map.json')
    assert path.exists(), 'risk_map.json must exist in data/'
    m = load_and_validate(path)
    assert isinstance(m, dict)
    assert 'territories' in m
    assert 'continents' in m
