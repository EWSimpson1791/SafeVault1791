# validate_map.py
from pathlib import Path
from data import load_and_validate

if __name__ == "__main__":
    path = Path("data/risk_map.json")
    try:
        data = load_and_validate(path)
        print("Map validated successfully. Map name:", data.get("name"))
    except Exception as e:
        print("Map validation failed:")
        print(e)
