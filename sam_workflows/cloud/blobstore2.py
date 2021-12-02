from logging import error
import os
from typing import List, Dict, Any
from pathlib import Path

from azure.identity.aio import EnvironmentCredential
from azure.keyvault.secrets.aio import SecretClient
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


async def upload_files(
    filelist: List[Dict],
    container: str,
    subpath: str,
    overwrite: bool = False,
) -> None:

    # Instantiate a BlobServiceClient using a connection string, and thereafter a ContainerClient
    # blob_service_client = BlobServiceClient.from_connection_string(os.getenv("AZURE_STORAGE_CONNECTION_STRING"))
    # container_client = blob_service_client.get_container_client(container)

    # Instantiate a ContainerClient directly
    container_client = ContainerClient.from_connection_string(os.getenv("AZURE_STORAGE_CONNECTION_STRING"), container)

    if not await container_client.exists():
        raise ACAError(f"No such container exists: {container}")

    for f in filelist:
        source: Path = f["filepath"]

        if not source.is_file():
            raise FileNotFoundError(f"Source {source} is not a file.")

        blob_name: str = f"{subpath}/{source.name}"

        with open(source, "rb") as data:
            try:
                await container_client.upload_blob(name=blob_name, data=data, overwrite=overwrite)
            except Exception as error:
                raise UploadError(f"Upload of {source.name} failed: {error}")
    
    await container_client.close()
