from os import environ
from typing import List
from pathlib import Path

from azure.identity.aio import EnvironmentCredential
from azure.keyvault.secrets.aio import SecretClient
from acastorage import ACAStorage

from sam_workflows.helpers import load_config


PACKAGE_PATH: Path = Path(__file__).parent.parent.resolve()


async def upload_files(
    filelist: List[Path],
    upload_folder: Path = Path("."),
    overwrite: bool = False,
) -> None:

    # if config not loaded, fetch it
    if not environ.get("AZURE_BLOBSTORE_VAULTKEY"):
        load_config(PACKAGE_PATH / "config.json")

    credential = EnvironmentCredential()
    try:
        vault = SecretClient(
            vault_url="https://aca-keys.vault.azure.net", credential=credential
        )
        secret = await vault.get_secret(
            environ.get("AZURE_BLOBSTORE_VAULTKEY")
        )

        conn = ACAStorage("test", credential=secret.value)

        for file_ in filelist:
            await conn.upload_file(file_, upload_folder, overwrite=overwrite)
    finally:
        # Close transporters
        await conn.close()
        await vault.close()
        await credential.close()
