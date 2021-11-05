from os import environ as env
from pathlib import Path
from typing import List, Dict

import fitz
from PIL import Image

from sam_workflows.utils import add_watermark


class ConvertError(Exception):
    """Implements error to raise when pdf-conversion fails."""


def thumbnails(
    in_file: Path,
    out_dir: Path,
    thumbnails: List[Dict] = [
        {"size": 150, "suffix": "_s"},
        {"size": 640, "suffix": "_m"},
    ],
    watermark: bool = True,
    overwrite: bool = True,
    page: int = 0,
    extension: str = ".jpg",
) -> List[Path]:

    # setup
    if not (in_file.is_file()) or in_file.suffix != ".pdf":
        raise FileNotFoundError(f"Input-path not a pdf-file: {in_file}")

    # create if out_folder does not exist
    if not out_dir.exists():
        out_dir.mkdir(parents=True, exist_ok=True)

    try:
        doc = fitz.open(in_file)
    except Exception as e:
        raise ConvertError(f"Unable to open {in_file} as pdf-file: {e}")

    pix = doc.load_page(page).get_pixmap()
    # create and save a PIL image
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    response: List[Path] = []
    for thumb in thumbnails:
        # tests
        out_file: Path = (
            out_dir / f"{in_file.stem}{thumb.get('suffix')}{extension}"
        )
        if out_file.exists() and not overwrite:
            raise FileExistsError(f"File already exists: {out_file}")

        copy_img = img.copy()
        # thumbnail() doesn't enlarge smaller img and keeps aspect-ratio
        copy_img.thumbnail((thumb.get("size"), thumb.get("size")))

        # If larger than watermark-width, add watermark
        if watermark:
            if copy_img.width > int(env["SAM_WATERMARK_WIDTH"]):
                copy_img = add_watermark(copy_img)

        try:
            copy_img.save(out_file)
        except Exception as e:
            raise ConvertError(f"Error saving thumbnail from {in_file}: {e}")

        response.append(out_file)

    return response
