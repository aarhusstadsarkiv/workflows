from os import environ as env
from pathlib import Path
from typing import Any, List, Dict, Optional

import numpy as np
import fitz
from PIL import Image, ExifTags

from source.helpers.watermark import add_watermark

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class PDFConvertError(Exception):
    """Implements error to raise when pdf-conversion fails."""


class ImageConvertError(Exception):
    """Implements error to raise when image-conversion fails."""


class VideoConvertError(Exception):
    """Implements error to raise when video-conversion fails."""


# -----------------------------------------------------------------------------
# Functions
# -----------------------------------------------------------------------------


def pdf_frontpage_to_image(pdf_in: Path, out_folder: Path) -> Path:
    if not pdf_in.is_file():
        raise FileNotFoundError(f"Input-path not a pdf-file: {pdf_in}")

    # create if out_folder does not exist
    out_folder.mkdir(parents=True, exist_ok=True)

    try:
        doc = fitz.open(pdf_in)
    except Exception as e:
        raise PDFConvertError(f"Unable to open {pdf_in} as pdf-file: {e}")

    page = doc.loadPage(0)
    pix = page.getPixmap()
    out_file = str(out_folder / pdf_in.stem) + ".png"

    try:
        pix.writePNG(out_file)
    except Exception as e:
        raise PDFConvertError(f"Unable to save {pdf_in} as png-file: {e}")

    return Path(out_file)


def generate_jpgs(
    img_in: Path,
    out_folder: Path,
    out_files: List[Dict[str, Any]] = [
        {
            "size": 1920,
            "filename": "large.jpg",
        },
        {
            "size": 640,
            "filename": "medium.jpg",
        },
        {
            "size": 150,
            "filename": "small.jpg",
        },
    ],
    quality: int = 80,
    no_watermark: bool = False,
    overwrite: bool = False,
) -> Dict[int, Path]:

    out_folder.mkdir(parents=True, exist_ok=True)

    try:
        img: Any = Image.open(img_in)
    except Exception as e:
        raise ImageConvertError(f"Error opening file {img_in.name}: {e}")

    # Key-value pairs of the size and path of each accessfile
    resp: Dict[int, Path] = {}
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

    # for size, extension in sizes.items():
    for el in out_files:
        size: int = el.get("size", "")
        copy_img = img.copy()

        if "16" in copy_img.mode:
            # https://github.com/openvinotoolkit/cvat/pull/342/commits/ \
            # 1520641ce65c4d3d90cb1011f83603a70943f479
            im_data = np.array(copy_img)
            copy_img = Image.fromarray(im_data // (im_data.max() // 2 ** 8))

            # https://github.com/python-pillow/Pillow/issues/2574
            # c_img = ImageMath.eval('im/256', {'im': c_img}).convert('RGB')

        # If not rbg, convert before doing more
        if copy_img.mode != "RGB":
            copy_img = copy_img.convert("RGB")

        # thumbnail() doesn't enlarge smaller img and keeps aspect-ratio
        copy_img.thumbnail((size, size))

        # If larger than watermark-width, add watermark
        if not no_watermark:
            if copy_img.width > int(env["SAM_WATERMARK_WIDTH"]):
                copy_img = add_watermark(copy_img)

        out_path: Path = out_folder / el["filename"]

        # Skip saving, if overwrite is False and file already exists
        if out_path.exists() and not overwrite:
            raise FileExistsError(f"File already exists: {out_path}")

        try:
            copy_img.save(
                out_path,
                quality=quality,
            )
            resp[size] = out_path
        except Exception as e:
            raise ImageConvertError(f"Error saving file {img_in.name}: {e}")
    return resp
