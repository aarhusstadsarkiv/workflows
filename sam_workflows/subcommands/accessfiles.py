import json
import shutil
from os import environ as env
from typing import List, Dict
from pathlib import Path

from sam_workflows.acastorage.exceptions import UploadError

from sam_workflows.helpers.convert import PDFConvertError

from ..helpers import (
    load_csv_from_sam,
    save_csv_to_sam,
    upload_files,
    pdf_frontpage_to_image,
    generate_jpgs,
    ImageConvertError,
)

# -----------------------------------------------------------------------------
# Functions
# -----------------------------------------------------------------------------


async def generate_sam_access_files(
    csv_in: Path,
    csv_out: Path,
    no_watermark: bool = False,
    no_upload: bool = False,
    overwrite: bool = False,
    dryrun: bool = False,
) -> None:
    """Generates, uploads and copies access-images from the files in the
    csv-file.

    Parameters
    ----------
    csv_in : Path
        Csv-file exported from SAM
    csv_out: Path
        Csv-file to re-import into SAM
    no_watermark: bool
        Do not add watermarks to access-files. Defaults to False
    no_upload: bool
        Do not upload the generated access-files to Azure. Defaults to False
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

    # Load envvars
    if dryrun:
        ACCESS_PATH = Path.home() / "Downloads" / "sam_workflow_accessfiles"
        MASTER_PATH = (
            Path(__file__).parent.parent.parent.resolve()
            / "tests"
            / "testfiles"
        )
    elif env.get("OneDrive"):
        # OneDrive-folder with access-files
        ACCESS_PATH = (
            Path.home()
            / "Aarhus kommune"
            / "AFD-Aarhus Stadsarkiv - Dokumenter"
            / "_DIGITALT_ARKIV"
            / env["SAM_ACCESS_DIR"]
        )

        # Current master-path on the M-drive
        MASTER_PATH = Path(env["M_DRIVE_MASTER_PATH"])
    else:
        ACCESS_PATH = Path.home() / "Downloads" / "sam_access_accessfiles"
        MASTER_PATH = (
            Path(__file__).parent.parent.parent.resolve()
            / "tests"
            / "testfiles"
        )

    TEMP_PATH = Path.home() / env["APP_DIR"] / "temp"  # Used for pdf-files
    ACCESS_LARGE_SIZE = int(env["SAM_ACCESS_LARGE_SIZE"])
    ACCESS_MEDIUM_SIZE = int(env["SAM_ACCESS_MEDIUM_SIZE"])
    ACCESS_SMALL_SIZE = int(env["SAM_ACCESS_SMALL_SIZE"])
    IMAGE_FORMATS = env["SAM_IMAGE_FORMATS"].split(" ")
    ACASTORAGE_URL = "/".join(
        [env["ACASTORAGE_ROOT"], env["ACASTORAGE_CONTAINER"]]
    )

    # Load csv-file from SAM
    files: List[Dict] = load_csv_from_sam(csv_in)
    files_count: int = len(files)
    print(f"Csv-file loaded. {files_count} files to process.", flush=True)

    output: List[Dict] = []

    # Ensure existence of access-folder
    ACCESS_PATH.mkdir(parents=True, exist_ok=True)

    # Generate access-files
    for idx, row in enumerate(files, start=1):
        # Load SAM-metadata
        file_id: str = row["uniqueID"]
        data = json.loads(row["oasDataJsonEncoded"])
        legal_status: str = data.get("other_restrictions", "4")
        constractual_status: str = data.get("contractual_status", "1")
        filename: str = data["filename"]
        print(f"Processing {filename} ({idx} of {files_count})", flush=True)

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
        filepath = MASTER_PATH / filename
        if not filepath.exists():
            print(f"No file found at: {filepath}", flush=True)
            continue
        if not filepath.is_file():
            print(f"Filepath refers to a directory: {filepath}", flush=True)
            continue

        # ensure access-folder for this files access-copies
        Path(ACCESS_PATH / file_id).mkdir(exist_ok=True)

        # Common access_files for all formats
        output_files = [
            {
                "size": ACCESS_SMALL_SIZE,
                "filename": f"{file_id}_s.jpg",
            },
            {
                "size": ACCESS_MEDIUM_SIZE,
                "filename": f"{file_id}_m.jpg",
            },
        ]
        # If pdf-file
        if filepath.suffix == ".pdf":
            record_type = "web_document"
            # copy pdf to relevant sub-access-dir
            shutil.copy2(filepath, ACCESS_PATH / file_id / f"{file_id}_c.pdf")

            # generate png-file from first page in pdf-file
            TEMP_PATH.mkdir(exist_ok=True)
            try:
                filepath = pdf_frontpage_to_image(filepath, TEMP_PATH)
            except PDFConvertError as e:
                print(f"Error converting pdf: {e}", flush=True)
                continue

        # elif image-file
        elif filepath.suffix in IMAGE_FORMATS:
            record_type = "image"
            output_files.append(
                {
                    "size": ACCESS_LARGE_SIZE,
                    "filename": f"{file_id}_l.jpg",
                }
            )

        else:
            print(f"Unable to handle fileformat: {filename}", flush=True)
            continue

        # Generate access-files
        try:
            jpgs = generate_jpgs(
                filepath,
                out_folder=ACCESS_PATH / file_id,
                out_files=output_files,
                no_watermark=no_watermark,
                overwrite=overwrite,
            )
        except FileNotFoundError as e:
            print(f"Failed conversion. File not found: {e}", flush=True)
        except FileExistsError as e:
            print(f"Skipping conversion. File already exists: {e}", flush=True)
        except ImageConvertError as e:
            print(f"Failed to generate jpgs from {filename}: {e}", flush=True)
        else:
            print(f"Successfully converted {filename}", flush=True)

            filedata = {
                "oasid": file_id,
                "record_type": record_type,
            }
            if jpgs.get(ACCESS_SMALL_SIZE):
                filedata["thumbnail"] = str(jpgs[ACCESS_SMALL_SIZE])
            if jpgs.get(ACCESS_MEDIUM_SIZE):
                filedata["record_image"] = str(jpgs[ACCESS_MEDIUM_SIZE])
            if jpgs.get(ACCESS_LARGE_SIZE):
                filedata["large_image"] = str(jpgs[ACCESS_LARGE_SIZE])

            # Upload access-files
            if not no_upload:
                filepaths: List[Dict[str, Path]] = []
                for path in jpgs.values():
                    filepaths.append(
                        {
                            "filepath": path,
                            "dest_dir": Path(file_id),
                        }
                    )
                if record_type == "web_document":
                    filepaths.append(
                        {
                            "filepath": ACCESS_PATH
                            / file_id
                            / f"{file_id}_c.pdf",
                            "dest_dir": Path(file_id),
                        }
                    )
                try:
                    await upload_files(filepaths, overwrite=overwrite)
                except UploadError as e:
                    if not overwrite and "BlobAlreadyExists" in str(e):
                        print(
                            f"Skipping upload.{filename} already exists.",
                            flush=True,
                        )
                    else:
                        print(f"Failed to upload {filename}: {e}", flush=True)
                else:
                    print(f"Uploaded files for {filename}", flush=True)

                    if record_type == "web_document":
                        filedata["web_document_url"] = "/".join(
                            [
                                ACASTORAGE_URL,
                                file_id,
                                f"{file_id}_c.pdf",
                            ]
                        )
                    if jpgs.get(ACCESS_SMALL_SIZE):
                        filedata["thumbnail"] = "/".join(
                            [
                                ACASTORAGE_URL,
                                file_id,
                                jpgs[ACCESS_SMALL_SIZE].name,
                            ]
                        )
                    if jpgs.get(ACCESS_MEDIUM_SIZE):
                        filedata["record_image"] = "/".join(
                            [
                                ACASTORAGE_URL,
                                file_id,
                                jpgs[ACCESS_MEDIUM_SIZE].name,
                            ]
                        )
                    if jpgs.get(ACCESS_LARGE_SIZE):
                        filedata["large_image"] = "/".join(
                            [
                                ACASTORAGE_URL,
                                file_id,
                                jpgs[ACCESS_LARGE_SIZE].name,
                            ]
                        )

            output.append(filedata)

    if output:
        save_csv_to_sam(output, csv_out)
        print("Finished proccessing files", flush=True)

        if len(output) < files_count:
            print("One or more files were not processed", flush=True)
    else:
        print("No new accessfiles have been generated", flush=True)

    if TEMP_PATH.exists():
        shutil.rmtree(TEMP_PATH)
