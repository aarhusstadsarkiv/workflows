import json
from pathlib import Path
from typing import List, Any, Dict, Optional, Tuple

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
def _generate_sam_jpgs(
    img_in: Path,
    quality: int = 80,
    sizes: List = [1920, 640, 150],
    watermark: bool = True,
) -> Dict:

    resp = {}
    try:
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
            cur_img = img.thumbnail((size, size))
            if watermark and (cur_img.size[0] > SAM_WATERMARK_SIZE):
                cur_img = add_watermark(cur_img)

            access_dirs = {
                SAM_ACCESS_LARGE_SIZE: SAM_ACCESS_LARGE_PATH,
                SAM_ACCESS_MEDIUM_SIZE: SAM_ACCESS_MEDIUM_PATH,
                SAM_ACCESS_SMALL_SIZE: SAM_ACCESS_SMALL_PATH,
            }

            out_dir = access_dirs.get(size) or SAM_ACCESS_PATH
            try:
                cur_img.save(out_dir, "JPEG", quality=quality)
                resp[size] = access_dirs.get(size)
            except Exception as e:
                resp[
                    "error"
                ] = f"Error encountered while saving file {cur_img}: {e}"
    return resp


def make_sam_access_files(
    csv_in: Path,
    csv_out: Path,
    upload: bool = True,
    overwrite: bool = False,
    watermark: bool = True,
) -> None:
    """Generates thumbnail-images from the files in the csv-file from SAM.

    Parameters
    ----------
    csv_in : Path
        Csv-file from SAM csv-export
    csv_out: Path
        Csv-file to import into SAM

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
    except Exception as e:
        raise e

    output: List[Dict] = []

    for file in rows:
        data = json.loads(file.get("oasDataJsonEncoded"))
        legal_status = data.get("other_legal_restrictions", "4")
        constractual_status = data.get("contractual_status", "1")
        filename = data["filename"]

        if int(legal_status.split(";")[0]) > 1:
            continue
        if int(constractual_status.split(";")[0]) < 3:
            continue

        filepath = Path(SAM_MASTER_PATH, filename)
        if not filepath.exists():
            raise FileNotFoundError
        if not filepath.is_file():
            raise IsADirectoryError

        # Determine fileformat
        if filepath.suffix in SAM_IMAGE_FORMATS:
            sizes = [
                SAM_ACCESS_LARGE_SIZE,
                SAM_ACCESS_MEDIUM_SIZE,
                SAM_ACCESS_SMALL_SIZE,
            ]
        elif filepath.suffix == ".pdf":
            sizes = [SAM_ACCESS_MEDIUM_SIZE, SAM_ACCESS_SMALL_SIZE]
        else:
            raise ImageConvertError(f"Unknown fileformat for {filepath.name}")

        resp = _generate_sam_jpgs(filepath, sizes=sizes, watermark=watermark)

        if resp.get("error"):
            raise ImageConvertError(resp["error"])

        output.append(
            {
                "oasid": filepath.stem,
                "thumbnail": resp.get(SAM_ACCESS_SMALL_SIZE),
                "record_image": resp.get(SAM_ACCESS_MEDIUM_SIZE),
                "record_type": "web_document"
                if filepath.suffix == ".pdf"
                else "image",
                "large_image": resp.get(SAM_ACCESS_LARGE_SIZE),
                "web_document_url": "web_url",
            }
        )

    save_csv_to_sam(output, csv_out)
