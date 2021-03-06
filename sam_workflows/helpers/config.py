import os
import json
from typing import Dict
from pathlib import Path


def load_config() -> None:
    """Loads all key-value pairs from config.json into the environment"""

    with open(Path.home() / ".sam_workflows" / "config.json") as c:
        config: Dict = json.load(c)
        for k, v in config.items():
            os.environ[k.upper()] = str(v)


# def load_envvars(env_vars: List[str]) -> None:
#     """Loads the passed env_vars in the os.environ, if they're found in
#     config.json.

#     Parameters
#     ----------
#     env_vars : List[str]
#         List of environment variables to load
#     """
#     with open(Path.home() / ".sam_workflows" / "config.json") as c:
#         config: Dict = json.load(c)
#         for idx in env_vars:
#             env = idx.lower()
#             if env in config:
#                 os.environ[env.upper()] = config[env]
#             else:
#                 raise KeyError(
#                     f"Required environment variable not in config: {env}"
#                 )
