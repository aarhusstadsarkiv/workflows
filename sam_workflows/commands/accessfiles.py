import json
import shutil
import time

from os import environ as env
from typing import List, Dict, Union
from pathlib import Path

import sam_workflows.converters as converters
from sam_workflows.cloud import blobstore, blobstore2
from sam_workflows.utils import fileio


async def generate_sam_access_files(
    csv_in: Path,
    csv_out: Path,
    no_watermark: bool = False,
    local: bool = False,
    overwrite: bool = False,
    dryrun: bool = False,
) -> None:
    """Generates, uploads and copies access-copies of the files in the
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
        raise Exception(
            "You are not using an administrative PC. Only dryruns are possible"
        )

    if not MASTER_PATH.exists():
        raise Exception("Path to Masterfiles does not exist.")

    # If 'access' and 'temp' paths does not exist, create them
    ACCESS_PATH.mkdir(parents=True, exist_ok=True)
    TEMP_PATH: Path = Path.home() / env["APP_DIR"] / "temp"
    TEMP_PATH.mkdir(parents=True, exist_ok=True)

    # get configvars through the environment
    ACCESS_LARGE_SIZE = int(env["SAM_ACCESS_LARGE_SIZE"])
    ACCESS_MEDIUM_SIZE = int(env["SAM_ACCESS_MEDIUM_SIZE"])
    ACCESS_SMALL_SIZE = int(env["SAM_ACCESS_SMALL_SIZE"])
    IMAGE_FORMATS = env["SAM_IMAGE_FORMATS"].split(" ")
    VIDEO_FORMATS = env["SAM_VIDEO_FORMATS"].split(" ")

    ##########################
    # Load csv-file from SAM #
    ##########################
    files: List[Dict] = fileio.load_csv_from_sam(csv_in)
    files_count: int = len(files)
    convert_errors: int = 0
    upload_errors: int = 0
    convert_skipped: int = 0
    upload_skipped: int = 0
    output: List[Dict] = []
    print(f"Csv-file loaded. {files_count} files to process.", flush=True)

    # Generate access-files
    for idx, row in enumerate(files, start=1):
        # vars
        file_id: str = row["uniqueID"]
        data = json.loads(row["oasDataJsonEncoded"])
        legal_status: str = data.get("other_restrictions", "4")
        constractual_status: str = data.get("contractual_status", "1")
        filename: str = data["filename"]
        out_dir = ACCESS_PATH / file_id
        Path(ACCESS_PATH / file_id).mkdir(exist_ok=True)
        filedata: Dict[str, Union[str, Path]] = {"oasid": file_id}

        print(f"Processing {idx} of {files_count}: {filename}", flush=True)

        # Check rights
        if int(legal_status.split(";")[0]) > 1:
            print(f"Skipping {filename} due to legal restrictions", flush=True)
            convert_skipped += 1
            continue
        if int(constractual_status.split(";")[0]) < 3:
            print(
                f"Skipping {filename} due to contractual restrictions",
                flush=True,
            )
            convert_skipped += 1
            continue

        # validate filepath
        filepath = MASTER_PATH / filename
        if not filepath.exists():
            print(f"No file found at: {filepath}", flush=True)
            convert_errors += 1
            continue
        if not filepath.is_file():
            print(f"Filepath refers to a directory: {filepath}", flush=True)
            convert_errors += 1
            continue

        # convert according to file extension
        if filepath.suffix == ".pdf":
            try:
                # copy master-pdf to relevant sub-access-dir
                shutil.copy2(filepath, out_dir / f"{file_id}_c.pdf")
                # thumbnails
                thumbs: List[Path] = converters.pdf_thumbnails(
                    filepath,
                    out_dir,
                    no_watermark=no_watermark,
                    overwrite=overwrite,
                )
            except FileExistsError:
                print(
                    f"Skipping convertion as {filename} already exists",
                    flush=True,
                )
                convert_skipped += 1
                continue
            except converters.ConvertError as e:
                print(f"ConvertError when converting pdf: {e}", flush=True)
                convert_errors += 1
                continue
            except Exception as e:
                print(f"Unknown error when converting pdf: {e}", flush=True)
                convert_errors += 1
                continue

            filedata.update(
                {
                    "record_type": "web_document",
                    "thumbnail": thumbs[0],
                    "record_image": thumbs[1],
                    "web_document_url": out_dir / f"{file_id}_c.pdf",
                }
            )

        elif filepath.suffix in VIDEO_FORMATS:
            # generate thumbnails
            try:
                print("Generating thumbs from video...", flush=True)
                thumbs: List[Path] = converters.video_thumbnails(
                    filepath,
                    out_dir,
                    no_watermark=no_watermark,
                    overwrite=overwrite,
                )
            except FileExistsError:
                print(
                    f"Skipping thumb generation as {filename} already exists",
                    flush=True,
                )
                convert_skipped += 1
                continue
            except converters.ConvertError as e:
                print(
                    f"ConvertError generating thumbnails from video: {e}",
                    flush=True,
                )
                convert_errors += 1
                continue
            except Exception as e:
                print(
                    f"Unknown error generating thumbnails from video: {e}",
                    flush=True,
                )
                convert_errors += 1
                continue

            # Generate access copy
            try:
                print(
                    f"Generating access copy of video "
                    f"({time.strftime('%H:%M:%S', time.localtime())})...",
                    flush=True,
                )
                record_file = out_dir / f"{file_id}.mp4"
                converters.video_convert(
                    filepath, record_file, timeout=300, overwrite=overwrite
                )
            except FileExistsError:
                print(
                    f"Skipping conversion as {filename} already exists",
                    flush=True,
                )
                convert_skipped += 1
                continue
            except converters.ConvertError as e:
                print(f"ConvertError converting video: {e}", flush=True)
                convert_errors += 1
                continue
            except Exception as e:
                print(f"Unknown error converting video: {e}", flush=True)
                convert_errors += 1
                continue

            # Update filedata if all went well
            filedata.update(
                {
                    "record_type": "video",
                    "thumbnail": thumbs[0],
                    "record_image": thumbs[1],
                    "record_file": record_file,
                }
            )

        elif filepath.suffix in IMAGE_FORMATS:
            try:
                thumbs: List[Path] = converters.image_thumbnails(
                    filepath,
                    out_dir,
                    thumbnails=[
                        {"size": ACCESS_SMALL_SIZE, "suffix": "_s"},
                        {"size": ACCESS_MEDIUM_SIZE, "suffix": "_m"},
                        {"size": ACCESS_LARGE_SIZE, "suffix": "_l"},
                    ],
                    no_watermark=no_watermark,
                    overwrite=overwrite,
                )
            except FileExistsError:
                print(
                    f"Skipping convertion as {filename} already exists",
                    flush=True,
                )
                convert_skipped += 1
                continue
            except converters.ConvertError as e:
                print(f"ConvertError converting image: {e}", flush=True)
                convert_errors += 1
                continue
            except Exception as e:
                print(
                    f"Exception raised when converting image: {e}", flush=True
                )
                convert_errors += 1
                continue

            filedata.update(
                {
                    "record_type": "image",
                    "thumbnail": thumbs[0],
                    "record_image": thumbs[1],
                    "large_image": thumbs[2],
                }
            )

        else:
            print(f"Unable to handle fileformat: {filename}", flush=True)
            convert_errors += 1
            continue

        # Upload access-files if "local" option not checked
        if not local:
            # if dryrun, upload to "test"-folder
            # dest_dir = Path(env["ACASTORAGE_ROOT"])
            # if dryrun:
            #     dest_dir = dest_dir / "test" / file_id
            # else:
            #     dest_dir = dest_dir / env["ACASTORAGE_CONTAINER"] / file_id

            container: str = "sam-access"
            if dryrun:
                container = "test"

            keys: List = []
            if filedata["record_type"] == "web_document":
                keys = ["thumbnail", "record_image", "web_document_url"]
            elif filedata["record_type"] == "video":
                keys = ["thumbnail", "record_image", "record_file"]
            else:
                keys = ["thumbnail", "record_image", "large_image"]

            paths: List[Dict] = []
            for k, v in filedata.items():
                if k in keys:
                    paths.append({"filepath": v})
            print(str(paths[0]), flush=True)
            try:
                # await blobstore.upload_files(paths, overwrite=overwrite)
                await blobstore2.upload_files(
                    paths, container, subpath=file_id, overwrite=overwrite
                )
            except blobstore.UploadError as e:
                if not overwrite and "BlobAlreadyExists" in str(e):
                    print(
                        f"Skipping upload.{filename} already exists",
                        flush=True,
                    )
                    upload_skipped += 1
                else:
                    print(f"Failed to upload {filename}: {e}", flush=True)
                    upload_errors += 1
            except Exception as e:
                print(f"Failed to upload {filename}: {e}", flush=True)
                upload_errors += 1
            else:
                print(f"Uploaded files for {filename}", flush=True)
                # update filedata with online paths
                # no urlencode necessary due to int-based filenames
                for k in keys:
                    name: str = Path(filedata[k]).name
                    filedata[
                        k
                    ] = f"""{env['ACASTORAGE_ROOT']}/
                        {env['ACASTORAGE_CONTAINER']}/{file_id}/{name}"""

                    # if type(filedata.get(k)) == "Path":
                    #     filedata[k] = dest_dir / Path(filedata[k]).name

        output.append(filedata)

    ########################
    # save to SAM csv-file #
    ########################
    if output:
        print(f"Finished processing {files_count} files", flush=True)
        print(f"{convert_skipped} files were skipped", flush=True)
        print(f"{convert_errors} files failed processing", flush=True)
        print(f"{upload_skipped} files skipped upload", flush=True)
        print(f"{upload_errors} files failed upload", flush=True)
        try:
            fileio.save_csv_to_sam(output, csv_out)
        except Exception as e:
            print(f"Error trying to generate csv-file: {e}", flush=True)

    else:
        print("No new accessfiles have been generated", flush=True)

    # Remove temp-folder
    if TEMP_PATH.exists():
        shutil.rmtree(TEMP_PATH)
