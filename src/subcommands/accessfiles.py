import json
import shutil
from os import environ as env
from typing import List, Dict
from pathlib import Path

from src.acastorage.exceptions import UploadError
import src.converters.pdf as pdf_conv
import src.converters.video as video_conv
import src.converters.image as image_conv

# from src.helpers.convert import PDFConvertError

from src.helpers import (
    load_csv_from_sam,
    save_csv_to_sam,
    upload_files,
)

# -----------------------------------------------------------------------------
# Functions
# -----------------------------------------------------------------------------


async def generate_sam_access_files(
    csv_in: Path,
    csv_out: Path,
    no_watermark: bool = False,
    local: bool = False,
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
    local: bool
        Do not upload the generated access-files to Azure. Defaults to False
    overwrite: bool
        Overwrite existing files in both local storage and Azure. Defaults to
        False
    """

    ################
    # Load envvars #
    ################
    if dryrun:
        ACCESS_PATH = Path.home() / "Downloads" / "workflow_accessfiles"
        MASTER_PATH = Path.home() / "Downloads" / "workflow_masterfiles"

    # If run from an administrative PC
    # OneDrive-folder with access-files, M-drive-folder with master-files
    elif env.get("OneDrive"):
        ACCESS_PATH = (
            Path.home()
            / "Aarhus kommune"
            / "AFD-Aarhus Stadsarkiv - Dokumenter"
            / "_DIGITALT_ARKIV"
            / env["SAM_ACCESS_DIR"]
        )
        MASTER_PATH = Path(env["M_DRIVE_MASTER_PATH"])

    else:
        raise Exception("You are not using an administrative PC or a dryrun")

    if not MASTER_PATH.exists():
        raise Exception("Path to Masterfiles does not exist.")

    # Ensure existence of access and temp folder
    ACCESS_PATH.mkdir(parents=True, exist_ok=True)
    TEMP_PATH: Path = Path.home() / env["APP_DIR"] / "temp"
    TEMP_PATH.mkdir(parents=True, exist_ok=True)

    ACCESS_LARGE_SIZE = int(env["SAM_ACCESS_LARGE_SIZE"])
    ACCESS_MEDIUM_SIZE = int(env["SAM_ACCESS_MEDIUM_SIZE"])
    ACCESS_SMALL_SIZE = int(env["SAM_ACCESS_SMALL_SIZE"])
    IMAGE_FORMATS = env["SAM_IMAGE_FORMATS"].split(" ")
    VIDEO_FORMATS = env["SAM_VIDEO_FORMATS"].split(" ")
    ACASTORAGE_URL = "/".join(
        [env["ACASTORAGE_ROOT"], env["ACASTORAGE_CONTAINER"]]
    )

    ##########################
    # Load csv-file from SAM #
    ##########################
    files: List[Dict] = load_csv_from_sam(csv_in)
    files_count: int = len(files)
    print(f"Csv-file loaded. {files_count} files to process.", flush=True)

    # Generate access-files
    output: List[Dict] = []
    for idx, row in enumerate(files, start=1):
        # vars
        file_id: str = row["uniqueID"]
        data = json.loads(row["oasDataJsonEncoded"])
        legal_status: str = data.get("other_restrictions", "4")
        constractual_status: str = data.get("contractual_status", "1")
        filename: str = data["filename"]
        out_dir = ACCESS_PATH / file_id
        Path(ACCESS_PATH / file_id).mkdir(exist_ok=True)

        print(f"Processing {idx} of {files_count}: {filename}", flush=True)

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

        # validate filepath
        filepath = MASTER_PATH / filename
        if not filepath.exists():
            print(f"No file found at: {filepath}", flush=True)
            continue
        if not filepath.is_file():
            print(f"Filepath refers to a directory: {filepath}", flush=True)
            continue

        if filepath.suffix == ".pdf":
            try:
                # copy master-pdf to relevant sub-access-dir
                shutil.copy2(filepath, out_dir / f"{file_id}_c.pdf")
                # thumbnails
                ts = pdf_conv.thumbnails(
                    filepath,
                    out_dir,
                    watermark=no_watermark,
                    overwrite=overwrite,
                )
            except pdf_conv.PDFConvertError as e:
                print(f"PDFConvertError converting pdf: {e}", flush=True)
                continue
            except Exception as e:
                print(f"Exception raised when converting pdf: {e}", flush=True)
                continue

            filedata = {
                "oasid": file_id,
                "record_type": "web_document",
                "thumbnail": ts[0],
                "record_image": ts[1],
                "web_document_url": out_dir / f"{file_id}_c.pdf",
            }

            if not local:
                dest_dir = ACASTORAGE_URL / file_id
                paths: List[Dict] = [
                    {"filepath": v, "dest_dir": dest_dir}
                    for k, v in filedata
                    if k in ("thumbnail", "record_image", "web_document_url")
                ]
                try:
                    await upload_files(paths, overwrite=overwrite)
                except UploadError as e:
                    if not overwrite and "BlobAlreadyExists" in str(e):
                        print(
                            f"Skipping upload.{filename} already exists.",
                            flush=True,
                        )
                    else:
                        print(f"Failed to upload {filename}: {e}", flush=True)
                except Exception as e:
                    print(f"Failed to upload {filename}: {e}", flush=True)


                print(f"Uploaded files for {filename}", flush=True)
                filedata.update({
                    "thumbnail": ts[0],
                    "record_image": ts[1],
                    "web_document_url": out_dir / f"{file_id}_c.pdf",
                })

        elif filepath.suffix in VIDEO_FORMATS:

            try:
                record_file = out_dir / f"{file_id}.mp4"
                video_conv.convert(filepath, record_file)
                thumbnails = video_conv.thumbnails(
                    filepath,
                    out_dir,
                    watermark=no_watermark,
                    overwrite=overwrite,
                )
            except video_conv.VideoConvertError as e:
                print(f"VideoConvertError converting video: {e}", flush=True)
                continue
            except Exception as e:
                print(
                    f"Exception raised when converting video: {e}", flush=True
                )
                continue

            filedata = {
                "oasid": file_id,
                "record_type": "video",
                "thumbnail": thumbnails[0],
                "record_image": thumbnails[1],
                "record_file": record_file,
            }

        elif filepath.suffix in IMAGE_FORMATS:
            try:
                ts = image_conv.thumbnails(
                    filepath,
                    out_dir,
                    thumbnails=[
                        {"size": 150, "suffix": "_s"},
                        {"size": 640, "suffix": "_m"},
                        {"size": 1920, "suffix": "_l"},
                    ],
                    watermark=no_watermark,
                    overwrite=overwrite,
                )
            except image_conv.ImageConvertError as e:
                print(f"ImageConvertError converting image: {e}", flush=True)
                continue
            except Exception as e:
                print(
                    f"Exception raised when converting image: {e}", flush=True
                )
                continue

            filedata = {
                "oasid": file_id,
                "record_type": "image",
                "thumbnail": ts[0],
                "record_image": ts[1],
                "large_image": ts[2],
            }

        else:
            print(f"Unable to handle fileformat: {filename}", flush=True)
            continue

    # Upload access-files
    if not local:
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
                    "filepath": ACCESS_PATH / file_id / f"{file_id}_c.pdf",
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

    ########################
    # save to SAM csv-file #
    ########################
    if output:
        save_csv_to_sam(output, csv_out)
        print("Finished proccessing files", flush=True)

        if len(output) < files_count:
            print("One or more files were not processed", flush=True)
    else:
        print("No new accessfiles have been generated", flush=True)

    # Remove temp-folder
    if TEMP_PATH.exists():
        shutil.rmtree(TEMP_PATH)
