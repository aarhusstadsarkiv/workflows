import os
from typing import List, Dict, Any
from pathlib import Path

# from azure.identity.aio import EnvironmentCredential
# from azure.keyvault.secrets.aio import SecretClient
# from azure.storage.blob.aio import ContainerClient

from azure.storage.blob.aio import BlobServiceClient, BlobClient, ContainerClient


class ACAError(Exception):
    """Base exception for ACAStorage errors."""


class UploadError(ACAError):
    """Error to raise when upload and related functionality fails.
    This is implemented because it is unclear which exceptions are
    potentially raised from upload in the Azure Blob Storage SDK.
    Thus, we intercept all possible exceptions and re-raise with this.
    """


async def upload_files_2(
    filelist: List[Dict],
    container: str = "sam-access",
    overwrite: bool = False,
) -> None:

    # Instantiate a BlobServiceClient using a connection string, and thereafter a ContainerClient
    # blob_service_client = BlobServiceClient.from_connection_string(os.getenv("AZURE_STORAGE_CONNECTION_STRING"))
    # container_client = blob_service_client.get_container_client(container)

    # Instantiate a ContainerClient directly
    container_client = ContainerClient.from_connection_string(os.getenv("AZURE_STORAGE_CONNECTION_STRING"), container)

    if not container_client.exists():
        raise ACAError(f"No such container exists: {container}")

    for f in filelist:
        source_file: Path = f["filepath"]
        dest_dir: str = f["dest_dir"]

        if not source_file.is_file():
            raise FileNotFoundError(f"Source {source_file} is not a file.")

        blob_name: str = f"{dest_dir}/{source_file.name}"

        # f["filepath"], f["dest_dir"], overwrite=overwrite
        with open(source_file, "rb") as data:
            await container_client.upload_blob(name=blob_name, data=data, overwrite=overwrite)

        # blob_client = self.get_blob_client(blob_name)
        # blob = BlobClient.from_connection_string(conn_str="<connection_string>", container_name="my_container", blob_name="my_blob")


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
                print(f"Trying to upload {blob_name} from within 'upload_file'. Filesize: {source.stat().st_size}", flush=True)
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
