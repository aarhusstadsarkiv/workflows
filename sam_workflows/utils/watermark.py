from os import environ as env
from pathlib import Path
from typing import Any
from PIL import Image


class ImageError(Exception):
    """Implements error to raise when conversion fails."""


def add_watermark_to_path(path: Path) -> None:

    try:
        img: Any = Image.open(path)
    except Exception as e:
        raise ImageError(f"Cannot open path as PIL.Image: {path}: {e}")
    try:
        image = add_watermark(img)
    except Exception as e:
        raise ImageError(f"Unable to add watermark to image: {e}")

    try:
        image.save(path)
    except Exception as e:
        raise ImageError(f"Unable to save watermarked image to {path}: {e}")


def add_watermark(img: Image) -> Image:
    """Adds a ACA-watermark in the bottom-right corner of the supplied image.

    Parameters
    ----------
    img : Image
        PIL Image-object

    Returns
    ------
    Image
    """

    WATERMARK_WIDTH = int(env["SAM_WATERMARK_WIDTH"])
    WATERMARK_HEIGHT = int(env["SAM_WATERMARK_HEIGHT"])
    WATERMARK_WHITE = Path.home() / env["APP_DIR"] / env["SAM_WATERMARK_WHITE"]
    WATERMARK_BLACK = Path.home() / env["APP_DIR"] / env["SAM_WATERMARK_BLACK"]

    copy = img.copy()
    grayscale = copy.convert("L")

    anchor_x = copy.width - WATERMARK_WIDTH
    anchor_y = copy.height - WATERMARK_HEIGHT
    pixel_count = WATERMARK_WIDTH * WATERMARK_HEIGHT
    pixel_values = 0

    for x in range(anchor_x, anchor_x + WATERMARK_WIDTH):
        for y in range(anchor_y, anchor_y + WATERMARK_HEIGHT):
            pixel_values = pixel_values + grayscale.getpixel((x, y))

    if pixel_values / pixel_count < 128:
        logo = Image.open(WATERMARK_WHITE)
    else:
        logo = Image.open(WATERMARK_BLACK)

    copy.paste(logo, (anchor_x, anchor_y), logo)

    return copy
