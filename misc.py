import json
import os

def parse_json(path: str):
    """
    json to python dict
    """
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None
