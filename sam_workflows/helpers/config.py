import os
import json
from pathlib import Path


def load_config(config_file: Path) -> None:
    with open(config_file) as c:
        config = json.load(c)
        for k, v in config.items():
            os.environ[k.upper()] = v
