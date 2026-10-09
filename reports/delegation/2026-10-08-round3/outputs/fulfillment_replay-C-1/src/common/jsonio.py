import json
from pathlib import Path

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def render(value):
    return json.dumps(value, sort_keys=True, indent=2)
