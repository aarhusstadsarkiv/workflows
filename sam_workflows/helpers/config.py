import os
import json
from typing import List

from sam_workflows.settings import PACKAGE_PATH


def load_config(config_keys: List[str]) -> None:
    """Loads the passed config-keys in the os.environ, if they're found in
    config.json.

    Parameters
    ----------
    config_keys : List[str]
        List of uppercase config-keys to load
    """
    with open(PACKAGE_PATH / "config.json") as c:
        config = json.load(c)
        for k, v in config.items():
            if k.upper() in config_keys:
                os.environ[k.upper()] = v
