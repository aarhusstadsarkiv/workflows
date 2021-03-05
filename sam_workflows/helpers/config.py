import os
import json
from typing import List, Dict
from pathlib import Path

# from sam_workflows.settings import PACKAGE_PATH


def load_config(env_vars: List[str]) -> None:
    """Loads the passed env_vars in the os.environ, if they're found in
    config.json.

    Parameters
    ----------
    env_vars : List[str]
        List of environment variables to load
    """
    # with open(PACKAGE_PATH / "config.json") as c:
    with open(Path.home() / ".sam_workflows" / "config.json") as c:
        config: Dict = json.load(c)
        for idx in env_vars:
            env = idx.lower()
            if env in config:
                os.environ[env.upper()] = config[env]
            else:
                raise KeyError(
                    f"Required environment variable not in config: {env}"
                )
