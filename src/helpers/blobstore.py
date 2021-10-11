from os import environ as env
from typing import List, Dict
from pathlib import Path

from azure.identity.aio import EnvironmentCredential
from azure.keyvault.secrets.aio import SecretClient
from src.acastorage import ACAStorage


async def upload_files(
    filelist: List[Dict[str, Path]],
    overwrite: bool = False,
) -> None:

    credential = EnvironmentCredential()
    try:
        vault = SecretClient(
            vault_url="https://aca-keys.vault.azure.net", credential=credential
        )
        secret = await vault.get_secret(env["AZURE_BLOBSTORE_VAULTKEY"])

        container = env["ACASTORAGE_CONTAINER"]
        conn = ACAStorage(container, credential=secret.value)

        for f in filelist:
            await conn.upload_file(
                f["filepath"], f["dest_dir"], overwrite=overwrite
            )

    finally:
        # Close transporters
        await conn.close()
        await vault.close()
        await credential.close()
