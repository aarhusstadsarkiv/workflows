from typing import List
from pathlib import Path

from azure.identity import EnvironmentCredential
from acastorage import ACAStorage


async def upload_files(
    filelist: List[Path],
    upload_folder: Path = Path("."),
    overwrite: bool = False,
) -> None:
    credential = EnvironmentCredential()
    conn = ACAStorage("test", credential=credential)

    for file_ in filelist:
        try:
            await conn.upload_file(file_, upload_folder, overwrite=overwrite)
        except Exception as e:
            raise e
