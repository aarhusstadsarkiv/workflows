import json
from pathlib import Path
from typing import List, Dict

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
    PAR_PATH,
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

    # Load SAM-csv with rows of file-references
    try:
        files: List[Dict] = load_csv_from_sam(csv_in)
        print("Csv-file loaded", flush=True)
    except Exception as e:
        raise e

    output: List[Dict] = []

    # Generate access-files
    for file in files:
        # Load SAM-data
        data = json.loads(file["oasDataJsonEncoded"])
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

        # filesizes
        filesizes = {SAM_ACCESS_SMALL_SIZE: "_s", SAM_ACCESS_MEDIUM_SIZE: "_m"}

        # If image-file
        if filepath.suffix in SAM_IMAGE_FORMATS:
            filesizes[SAM_ACCESS_LARGE_SIZE] = "_l"
            record_type = "image"
        # Elif pdf-file
        elif filepath.suffix == ".pdf":
            try:
                filepath = pdf_frontpage_to_image(
                    filepath, PAR_PATH / "images" / "temp"
                )
            except Exception as e:
                print(f"Failed pdf-conversion for {filename}: {e}", flush=True)
                continue
            record_type = "web_document"
        else:
            print(f"Unable to handle format: {filepath.suffix}", flush=True)
            continue

        # Generate access-files
        try:
            convert_resp = generate_jpgs(
                filepath,
                out_folder=SAM_ACCESS_PATH,
                sizes=filesizes,
                watermark=watermark,
            )
        except FileNotFoundError as e:
            print(f"Failed to generate jpgs. File not found: {e}", flush=True)
        except ImageConvertError as e:
            print(f"Failed to generate jpgs from {filename}: {e}", flush=True)

        print(f"Successfully converted {filename}", flush=True)

        small_path = convert_resp[SAM_ACCESS_SMALL_SIZE]
        medium_path = convert_resp[SAM_ACCESS_MEDIUM_SIZE]
        large_path = convert_resp.get(SAM_ACCESS_LARGE_SIZE)

        # Upload access-files
        if upload:
            filepaths = [small_path, medium_path]
            if large_path:
                filepaths.append(large_path)

            errors = await upload_files(filepaths, overwrite=overwrite)
            if errors:
                print(f"Failed upload for {filename}:", flush=True)
                print(f"Error: {errors[0]}", flush=True)
                continue

            print(f"Uploaded files for {filename}", flush=True)

            output.append(
                {
                    "oasid": filepath.stem,
                    "thumbnail": "/".join(
                        [ACASTORAGE_CONTAINER, small_path.name]
                    ),
                    "record_image": "/".join(
                        [ACASTORAGE_CONTAINER, medium_path.name]
                    ),
                    "record_type": record_type,
                    "large_image": "/".join(
                        [ACASTORAGE_CONTAINER, large_path.name]
                    )
                    if large_path
                    else "",
                    "web_document_url": "web_url",
                }
            )
    if output:
        save_csv_to_sam(output, csv_out)

    print("Done", flush=True)
