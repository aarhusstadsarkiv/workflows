import json
from os import environ
from typing import List, Dict
from pathlib import Path
from shutil import copy2

from acastorage.exceptions import UploadError

from sam_workflows.helpers.convert import PDFConvertError
from sam_workflows.helpers.config import load_config

from ..helpers import (
    load_csv_from_sam,
    save_csv_to_sam,
    upload_files,
    pdf_frontpage_to_image,
    generate_jpgs,
    ImageConvertError,
)
from ..settings import (
    SAM_ACCESS_PATH,
    SAM_ACCESS_LARGE_SIZE,
    SAM_ACCESS_MEDIUM_SIZE,
    SAM_ACCESS_SMALL_SIZE,
    SAM_MASTER_PATH,
    SAM_IMAGE_FORMATS,
    ACASTORAGE_CONTAINER,
    PACKAGE_PATH,
)

# -----------------------------------------------------------------------------
# Functions
# -----------------------------------------------------------------------------


async def generate_sam_access_files(
    csv_in: Path,
    csv_out: Path,
    watermark: bool = False,
    upload: bool = False,
    overwrite: bool = False,
) -> None:
    """Generates, uploads and copies access-images from the files in the
    csv-file.

    Parameters
    ----------
    csv_in : Path
        Csv-file exported from SAM
    csv_out: Path
        Csv-file to re-import into SAM
    watermark: bool
        Watermark access-files. Defaults to False
    upload: bool
        Upload the generated access-files to Azure. Defaults to False
    overwrite: bool
        Overwrite existing files in both local storage and Azure. Defaults to
        False

    Raises
    ------
    PDFConvertError
        Raised when errors in conversion occur. Errors from PIL are caught
        and re-raised with this error. If no pdf-files are loaded, this error
        is raised as well.
    ImageConvertError
        Raised when errors in conversion occur. Errors from PIL are caught
        and re-raised with this error. If no pdf-files are loaded, this error
        is raised as well.
    """

    # load relevant config-key, if not in environment
    if not environ.get("AZURE_BLOBSTORE_VAULTKEY"):
        blobstore_vars = [
            "AZURE_BLOBSTORE_VAULTKEY",
            "AZURE_TENANT_ID",
            "AZURE_CLIENT_ID",
            "AZURE_CLIENT_SECRET",
        ]
        load_config(blobstore_vars)

    # Load SAM-csv with rows of file-references
    files: List[Dict] = load_csv_from_sam(csv_in)
    print("Csv-file loaded", flush=True)

    output: List[Dict] = []

    # Ensure existence of root-access-folder
    SAM_ACCESS_PATH.mkdir(parents=True, exist_ok=True)

    # Generate access-files
    for row in files:
        # Load SAM-data
        file_id: str = row["uniqueID"]
        data = json.loads(row["oasDataJsonEncoded"])
        legal_status: str = data.get("other_restrictions", "4")
        constractual_status: str = data.get("contractual_status", "1")
        filename: str = data["filename"]

        # Check rights
        if int(legal_status.split(";")[0]) > 1:
            print(f"Skipping {filename} due to legal restrictions", flush=True)
            continue
        if int(constractual_status.split(";")[0]) < 3:
            print(
                f"Skipping {filename} due to contractual restrictions",
                flush=True,
            )
            continue

        # filepath
        filepath = SAM_MASTER_PATH / filename
        if not filepath.exists():
            print(f"No file found at: {filepath}", flush=True)
            continue
        if not filepath.is_file():
            print(f"Filepath refers to a directory: {filepath}", flush=True)
            continue

        # generate access-folder for this file
        Path(SAM_ACCESS_PATH / file_id).mkdir(parents=True, exist_ok=True)

        # Common access_files for all formats
        output_files = [
            {
                "size": SAM_ACCESS_SMALL_SIZE,
                "filename": f"{file_id}_s.jpg",
            },
            {
                "size": SAM_ACCESS_MEDIUM_SIZE,
                "filename": f"{file_id}_m.jpg",
            },
        ]
        # If image-file
        if filepath.suffix in SAM_IMAGE_FORMATS:
            record_type = "image"
            output_files.append(
                {
                    "size": SAM_ACCESS_LARGE_SIZE,
                    "filename": f"{file_id}_l.jpg",
                }
            )
        # Elif pdf-file
        elif filepath.suffix == ".pdf":
            record_type = "web_document"
            # copy pdf to relevant sub-access-dir
            copy2(filepath, SAM_ACCESS_PATH / file_id / f"{file_id}_c.pdf")

            # generate png-file from first page in pdf-file
            try:
                filepath = pdf_frontpage_to_image(
                    filepath, PACKAGE_PATH / "images" / "temp"
                )
            except PDFConvertError as e:
                print(e, flush=True)
                continue

        else:
            print(f"Unable to handle fileformat: {filename}", flush=True)
            continue

        # Generate access-files
        try:
            jpgs = generate_jpgs(
                filepath,
                out_folder=SAM_ACCESS_PATH / file_id,
                out_files=output_files,
                watermark=watermark,
                overwrite=overwrite,
            )
        except FileNotFoundError as e:
            print(f"Failed to generate jpgs. File not found: {e}", flush=True)
        except ImageConvertError as e:
            print(f"Failed to generate jpgs from {filename}: {e}", flush=True)
        else:
            print(f"Successfully converted {filename}", flush=True)

            # Upload access-files
            if upload:
                filepaths: List[Dict[str, Path]] = []
                for size, path in jpgs.items():
                    filepaths.append(
                        {
                            "filepath": path,
                            "dest_dir": Path(file_id),
                        }
                    )
                if record_type == "web_document":
                    filepaths.append(
                        {
                            "filepath": SAM_ACCESS_PATH
                            / file_id
                            / f"{file_id}_c.pdf",
                            "dest_dir": Path(file_id),
                        }
                    )
                try:
                    await upload_files(filepaths, overwrite=overwrite)
                except UploadError as e:
                    print(f"{filename} not uploaded. {e}", flush=True)
                else:
                    print(f"Uploaded files for {filename}", flush=True)

                    filedata = {
                        "oasid": file_id,
                        "record_type": record_type,
                    }
                    if record_type == "web_document":
                        filedata["web_document_url"] = "/".join(
                            [
                                ACASTORAGE_CONTAINER,
                                file_id,
                                f"{file_id}_c.pdf",
                            ]
                        )
                    if jpgs.get(SAM_ACCESS_SMALL_SIZE):
                        filedata["thumbnail"] = "/".join(
                            [
                                ACASTORAGE_CONTAINER,
                                file_id,
                                jpgs[SAM_ACCESS_SMALL_SIZE].name,
                            ]
                        )
                    if jpgs.get(SAM_ACCESS_MEDIUM_SIZE):
                        filedata["record_image"] = "/".join(
                            [
                                ACASTORAGE_CONTAINER,
                                file_id,
                                jpgs[SAM_ACCESS_MEDIUM_SIZE].name,
                            ]
                        )
                    if jpgs.get(SAM_ACCESS_LARGE_SIZE):
                        filedata["large_image"] = "/".join(
                            [
                                ACASTORAGE_CONTAINER,
                                file_id,
                                jpgs[SAM_ACCESS_LARGE_SIZE].name,
                            ]
                        )
                    output.append(filedata)

    if output:
        save_csv_to_sam(output, csv_out)

    print("Done", flush=True)
