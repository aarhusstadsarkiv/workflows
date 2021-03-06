from os import environ as env
from pathlib import Path
from PIL import Image


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
    WATERMARK_WHITE = Path.home() / env["SAM_WATERMARK_WHITE"]
    WATERMARK_BLACK = Path.home() / env["SAM_WATERMARK_BLACK"]

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
