from os import environ as env
from typing import List, Dict, Any
from pathlib import Path

from azure.identity.aio import EnvironmentCredential
from azure.keyvault.secrets.aio import SecretClient
from azure.storage.blob.aio import ContainerClient


class ACAError(Exception):
    """Base exception for ACAStorage errors."""


class UploadError(ACAError):
    """Error to raise when upload and related functionality fails.
    This is implemented because it is unclear which exceptions are
    potentially raised from upload in the Azure Blob Storage SDK.
    Thus, we intercept all possible exceptions and re-raise with this.
    """


class ACAStorage(ContainerClient):
    def __init__(
        self,
        container: str,
        credential: Any,
    ) -> None:
        """
        Azure Blob Storage Backend
        """
        super().__init__(
            "https://acastorage.blob.core.windows.net/",
            container,
            credential=credential,
        )
        # TODO: Implement exists() check when MS adds it, cf.
        # https://github.com/Azure/azure-sdk-for-python/pull/16315

    async def upload_file(
        self, source: Path, dest_dir: str, overwrite: bool = False
    ) -> None:
        """Upload source file to a specified destination. The destination
        is always assumed to be a directory.

        Parameters
        ----------
        source : pathlib.Path
            The source file to upload.
        dest_dir: str
            The destination folder to upload to.
        overwrite: bool, optional
            Whether to overwrite the target file if it exists.
            Defaults to False.

        Raises
        ------
        FileNotFoundError
            If the source is not a file.
        UploadError
            If upload of the file fails. Reraises exceptions from
            Azure's ContainerClient in a more user-friendly format.
        """
        if not source.is_file():
            raise FileNotFoundError(f"Source {source} is not a file.")

        blob_name: str = f"{dest_dir}/{source.name}"
        blob_client = self.get_blob_client(blob_name)

        with source.open("rb") as data:
            try:
                await blob_client.upload_blob(data=data, overwrite=overwrite)
            except Exception as err:
                raise UploadError(f"Upload of {source} failed: {err}")
            finally:
                await blob_client.close()


async def upload_files(
    filelist: List[Dict],
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
    except Exception as e:
        raise UploadError(f"Error uploading: {e}")
    finally:
        # Close transporters
        await conn.close()
        await vault.close()
        await credential.close()
