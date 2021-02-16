import json
from pathlib import Path
from typing import List, Any, Dict, Optional

import fitz
from PIL import Image, ExifTags

from ..helpers import (
    load_csv_from_sam,
    save_csv_to_sam,
    add_watermark,
    upload_files,
)
from ..settings import (
    WATERMARK_WIDTH,
    SAM_ACCESS_LARGE_SIZE,
    SAM_ACCESS_MEDIUM_SIZE,
    SAM_ACCESS_SMALL_SIZE,
    SAM_MASTER_PATH,
    SAM_IMAGE_FORMATS,
    ACASTORAGE_CONTAINER,
    PAR_PATH,
)

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class PDFConvertError(Exception):
    """Implements error to raise when pdf-conversion fails."""


class ImageConvertError(Exception):
    """Implements error to raise when image-conversion fails."""


# -----------------------------------------------------------------------------
# Functions
# -----------------------------------------------------------------------------
def _convert_pdf_cover_to_image(pdf_in: Path, out_folder: Path) -> Path:
    doc = fitz.open(pdf_in)
    page = doc.loadPage(0)
    pix = page.getPixmap()
    out_file = str(out_folder / pdf_in.stem) + ".png"
    try:
        pix.writePNG(out_file)
        return Path(out_file)
    except Exception as e:
        raise PDFConvertError(e)


def _generate_jpgs(
    img_in: Path,
    out_folder: Path,
    quality: int = 80,
    sizes: List = [1920, 640, 150],
    watermark: bool = False,
    overwrite: bool = False,
) -> Dict[int, Path]:

    # Key-value pairs of filesize (int) and filepath (Path)
    resp: Dict[int, Path] = {}

    try:
        img: Any = Image.open(img_in)
    except Exception as e:
        raise ImageConvertError(f"Error opening file {img_in.name}: {e}")
    else:
        img.load()

        # JPG image might be rotated. Fix, if rotatet.
        if hasattr(img, "_getexif"):  # only present in JPGs
            # Find the orientation exif tag.
            orientation_key: Optional[int] = None
            for tag, tag_value in ExifTags.TAGS.items():
                if tag_value == "Orientation":
                    orientation_key = tag
                    break

            # If exif data is present, rotate image according to
            # orientation value.
            if img.getexif() is not None:
                exif: Dict[Any, Any] = dict(img.getexif().items())
                orientation: Optional[int] = exif.get(orientation_key)
                if orientation == 3:
                    img = img.rotate(180)
                elif orientation == 6:
                    img = img.rotate(270)
                elif orientation == 8:
                    img = img.rotate(90)

        for size in sizes:
            copy_img = img.copy()
            # thumbnail() doesn't enlarge smaller img and keeps aspect-ratio
            copy_img.thumbnail((size, size))

            # If larger than watermark-width, add watermark
            if watermark and (copy_img.width > WATERMARK_WIDTH):
                copy_img = add_watermark(copy_img)

            # If not rbg, convert before saving as jpg
            if copy_img.mode != "RGB":
                copy_img = copy_img.convert("RGB")

            size_extensions = {1920: "_l", 640: "_m", 150: "_s"}

            new_filename = img_in.stem + size_extensions[size] + ".jpg"
            out_file = out_folder / new_filename

            # Skip saving, if overwrite is False and file already exists
            if (not overwrite) and out_file.exists():
                raise FileExistsError(f"File already exists: {out_file}")
            else:
                try:
                    copy_img.save(
                        out_file,
                        "JPEG",
                        quality=quality,
                    )
                    resp[size] = out_file
                except Exception as e:
                    raise ImageConvertError(
                        f"Error saving file {img_in.name}: {e}"
                    )
    return resp


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
        Csv-file from SAM csv-export
    csv_out: Path
        Csv-file to import into SAM
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

        # Check filepath
        filepath = Path(SAM_MASTER_PATH, filename)
        if not filepath.exists():
            print(f"No file found at: {filepath}", flush=True)
            continue
        if not filepath.is_file():
            print(f"Filepath refers to a directory: {filepath}", flush=True)
            continue

        # Determine fileformat
        if filepath.suffix in SAM_IMAGE_FORMATS:
            filesizes = [
                SAM_ACCESS_LARGE_SIZE,
                SAM_ACCESS_MEDIUM_SIZE,
                SAM_ACCESS_SMALL_SIZE,
            ]
            record_type = "image"
        elif filepath.suffix == ".pdf":
            filesizes = [SAM_ACCESS_MEDIUM_SIZE, SAM_ACCESS_SMALL_SIZE]
            filepath = _convert_pdf_cover_to_image(
                filepath, PAR_PATH / "images" / "temp"
            )
            record_type = "web_document"
        else:
            print(f"Unknown fileformat for {filepath.name}", flush=True)
            continue

        # Generate access-files
        convert_resp, error = _generate_jpgs(
            filepath, sizes=filesizes, watermark=watermark
        )

        # Check response from convert-function
        if error:
            print(error, flush=True)
            continue

        print(f"Successfully converted {filename}", flush=True)

        small_path = convert_resp[SAM_ACCESS_SMALL_SIZE]
        medium_path = convert_resp[SAM_ACCESS_MEDIUM_SIZE]
        large_path = convert_resp[SAM_ACCESS_LARGE_SIZE]

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
