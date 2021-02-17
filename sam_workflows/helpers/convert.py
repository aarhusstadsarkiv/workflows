from pathlib import Path
from typing import Any, Dict, Optional, Literal

import fitz
from PIL import Image, ExifTags

from .watermark import add_watermark

from ..settings import WATERMARK_WIDTH

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


def pdf_frontpage_to_image(pdf_in: Path, out_folder: Path) -> Path:
    if not pdf_in.is_file():
        raise FileNotFoundError(f"Input-path not a pdf-file: {pdf_in}")

    if not out_folder.is_dir():
        try:
            out_folder.mkdir(parents=True)
        except Exception as e:
            raise OSError(
                f"Unable to create out_folder: {out_folder}. Error: {e}"
            )

    try:
        doc = fitz.open(pdf_in)
        page = doc.loadPage(0)
        pix = page.getPixmap()
        out_file = str(out_folder / pdf_in.stem) + ".png"
        pix.writePNG(out_file)
        return Path(out_file)
    except Exception as e:
        raise PDFConvertError(e)


def generate_jpgs(
    img_in: Path,
    out_folder: Path,
    quality: int = 80,
    # sizes: List = [1920, 640, 150],
    sizes: Dict[int, str] = {1920: "_l", 640: "_m", 150: "_s"},
    affix: Literal["prefix", "postfix"] = "postfix",
    watermark: bool = False,
    overwrite: bool = False,
) -> Dict[int, Path]:

    if not img_in.is_file():
        raise FileNotFoundError(f"Input-path not a file: {img_in}")

    if not out_folder.is_dir():
        try:
            out_folder.mkdir(parents=True)
        except Exception as e:
            raise OSError(
                f"Unable to create out_folder: {out_folder}. Error: {e}"
            )
    try:
        img: Any = Image.open(img_in)
    except Exception as e:
        raise ImageConvertError(f"Error opening file {img_in.name}: {e}")
    else:
        # Key-value pairs of size, filepath
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

        for size, extension in sizes.items():
            copy_img = img.copy()
            # thumbnail() doesn't enlarge smaller img and keeps aspect-ratio
            copy_img.thumbnail((size, size))

            # If larger than watermark-width, add watermark
            if watermark and (copy_img.width > WATERMARK_WIDTH):
                copy_img = add_watermark(copy_img)

            # If not rbg, convert before saving as jpg
            if copy_img.mode != "RGB":
                copy_img = copy_img.convert("RGB")

            # size_extensions = {1920: "_l", 640: "_m", 150: "_s"}
            if affix == "postfix":
                new_filename = img_in.stem + extension + ".jpg"
            else:
                new_filename = extension + img_in.stem + ".jpg"
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
