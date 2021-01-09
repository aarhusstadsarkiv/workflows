import json
from pathlib import Path
from typing import List, Any, Dict, Optional, Tuple

import fitz
from PIL import Image, UnidentifiedImageError, ExifTags

from helpers import load_csv_from_sam, save_csv_to_sam, add_watermark
from settings import *

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
    # return pix.pillowData(format="JPEG", optimize=True)


def _generate_sam_jpgs(
    img_in: Path,
    quality: int = 80,
    sizes: List = [1920, 640, 150],
    watermark: bool = True,
) -> Dict:

    resp = {}
    try:
        filename = img_in.name
        img: Any = Image.open(img_in)
    except UnidentifiedImageError:
        resp["error"] = f"Failed to open {img_in} as an image."
    except Exception as e:
        resp["error"] = f"Error encountered while opening file {img_in}: {e}"
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
            # thumbnail-function doesn't enlarge if img is smaller
            # and it keeps the aspect-ratio
            copy_img = img.copy()
            copy_img.thumbnail((size, size))

            # If larger than thumbnail, add watermark
            if watermark and (copy_img.width > SAM_WATERMARK_WIDTH):
                print(f"Sending image to watermark...")
                copy_img = add_watermark(copy_img)

            # If not rbg, convert before saving as jpg
            if copy_img.mode != "RGB":
                copy_img = copy_img.convert("RGB")

            access_dirs = {
                SAM_ACCESS_LARGE_SIZE: SAM_ACCESS_LARGE_PATH,
                SAM_ACCESS_MEDIUM_SIZE: SAM_ACCESS_MEDIUM_PATH,
                SAM_ACCESS_SMALL_SIZE: SAM_ACCESS_SMALL_PATH,
            }

            out_dir = access_dirs.get(size) or SAM_ACCESS_PATH
            out_file = Path(out_dir, filename)
            try:
                copy_img.save(
                    out_file,
                    "JPEG",
                    quality=quality,
                )
                print(f"Image saved")
                resp[size] = out_file
            except Exception as e:
                print("Unable to save image")
                resp[
                    "error"
                ] = f"Error encountered while saving file {copy_img}: {e}"
    return resp


def make_sam_access_files(
    csv_in: Path,
    csv_out: Path,
    watermark: bool = True,
    upload: bool = True,
    overwrite: bool = False,
) -> None:
    """Generates thumbnail-images from the files in the csv-file from SAM.

    Parameters
    ----------
    csv_in : Path
        Csv-file from SAM csv-export
    csv_out: Path
        Csv-file to import into SAM
    watermark: bool
        Add watermark to access-files. Defaults to True
    upload: bool
        Upload the generated access-files to Azure. Defaults to True
    overwrite: bool
        Overwrite any previously uloaded access-files in Azure. Defaults to
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
    try:
        rows: List[Dict] = load_csv_from_sam(csv_in)
        print("Csv-file loaded...")
    except Exception as e:
        raise e

    output: List[Dict] = []

    for file in rows:
        data = json.loads(file.get("oasDataJsonEncoded"))
        legal_status = data.get("other_restrictions", "4")
        constractual_status = data.get("contractual_status", "1")
        filename = data["filename"]

        if int(legal_status.split(";")[0]) > 1:
            print(f"Skipping {filename} due to legal restrictions")
            continue
        if int(constractual_status.split(";")[0]) < 3:
            print(f"Skipping {filename} due to contractual restrictions")
            continue

        filepath = Path(SAM_MASTER_PATH, filename)
        if not filepath.exists():
            raise FileNotFoundError(f"No file found: {filepath}")
        if not filepath.is_file():
            raise IsADirectoryError(
                f"Filepath refers to a directory: {filepath}"
            )

        # Determine fileformat
        if filepath.suffix in SAM_IMAGE_FORMATS:
            sizes = [
                SAM_ACCESS_LARGE_SIZE,
                SAM_ACCESS_MEDIUM_SIZE,
                SAM_ACCESS_SMALL_SIZE,
            ]
            record_type = "image"
        elif filepath.suffix == ".pdf":
            sizes = [SAM_ACCESS_MEDIUM_SIZE, SAM_ACCESS_SMALL_SIZE]
            filepath = _convert_pdf_cover_to_image(
                filepath, Path("./images/temp")
            )
            record_type = "web_document"
        else:
            raise ImageConvertError(f"Unknown fileformat for {filepath.name}")

        # Generate access-files
        resp = _generate_sam_jpgs(filepath, sizes=sizes, watermark=watermark)

        if resp.get("error"):
            raise ImageConvertError(resp["error"])

        print(f"{filename} converted")
        output.append(
            {
                "oasid": filepath.stem,
                "thumbnail": resp.get(SAM_ACCESS_SMALL_SIZE),
                "record_image": resp.get(SAM_ACCESS_MEDIUM_SIZE),
                "record_type": record_type,
                "large_image": resp.get(SAM_ACCESS_LARGE_SIZE),
                "web_document_url": "web_url",
            }
        )

    save_csv_to_sam(output, csv_out)
