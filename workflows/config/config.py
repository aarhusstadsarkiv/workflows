import os
import json
# import toml
from typing import Dict
from pathlib import Path

CONFIG_DIR = Path.home() / ".aca" / "workflows"
JSON_FILE = "config.json"
# TOML_FILE = "config.toml"

CONFIG_KEYS = [
    "azure_tenant_id",
    "azure_client_id",
    "azure_client_secret",
    "azure_blobstore_vaultkey",
    "azure_storage_connection_string",
    "acastorage_root",
    "acastorage_container",
    "m_drive_master_path",
    "sam_backup_path",
    "sam_master_dir",
    "sam_access_dir",
    "sam_access_large_size",
    "sam_access_medium_size",
    "sam_access_small_size",
    "sam_watermark_width",
    "sam_watermark_height",
    "sam_watermark_white",
    "sam_watermark_black",
    "sam_image_formats",
    "sam_video_formats",
]


# def load_toml_configuration() -> Dict:
#     """Returns config as dict"""
#     conf = CONFIG_DIR / TOML_FILE
#     if not conf.is_file():
#         raise FileNotFoundError("Konfigurationsfilen blev ikke fundet.")

#     config_dict = toml.load(conf)
#     config_dict["app_dir"] = ".aca/workflows"
#     return dict(config_dict)


def load_json_configuration() -> None:
    """Loads all CONFIG_KEYS from config.json into the environment"""

    conf = CONFIG_DIR / JSON_FILE
    if not conf.is_file():
        raise FileNotFoundError("Konfigurationsfilen blev ikke fundet.")

    with open(conf) as c:
        try:
            config: Dict = json.load(c)
        except ValueError as e:
            raise ValueError(
                f"Konfigurationsfilen kan ikke parses korrekt: {e}"
            )
        else:
            for k, v in config.items():
                if k.lower() in CONFIG_KEYS:
                    os.environ[k.upper()] = str(v)
            os.environ["APP_DIR"] = ".aca/workflows"
