from pathlib import Path

import orjson

dir_path = Path(__file__).parent
cfgpath = dir_path / 'config.json'
with open(cfgpath, 'rb') as f:
    config = orjson.loads(f.read())
