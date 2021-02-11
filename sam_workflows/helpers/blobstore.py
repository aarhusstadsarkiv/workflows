from os import environ
from typing import List
from pathlib import Path

from azure.identity.aio import EnvironmentCredential
from azure.keyvault.secrets.aio import SecretClient
from acastorage import ACAStorage


async def upload_files(
    filelist: List[Path],
    upload_folder: Path = Path("."),
    overwrite: bool = False,
) -> List:

    credential = EnvironmentCredential()
    vault = SecretClient(
        vault_url="https://aca-keys.vault.azure.net", credential=credential
    )
    secret = await vault.get_secret(environ.get("AZURE_BLOBSTORE_VAULTKEY"))
    errors = []

    conn = ACAStorage("test", credential=secret.value)

    for file_ in filelist:
        try:
            await conn.upload_file(file_, upload_folder, overwrite=overwrite)
        except Exception as e:
            errors.append(e)

    return errors
