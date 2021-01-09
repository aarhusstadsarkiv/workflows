from PIL import Image

from settings import *


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
    copy = img.copy()
    grayscale = copy.convert("L")

    anchor_x = copy.width - SAM_WATERMARK_WIDTH
    anchor_y = copy.height - SAM_WATERMARK_HEIGHT
    pixel_count = SAM_WATERMARK_WIDTH * SAM_WATERMARK_HEIGHT
    pixel_values = 0

    for x in range(anchor_x, anchor_x + SAM_WATERMARK_WIDTH):
        for y in range(anchor_y, anchor_y + SAM_WATERMARK_HEIGHT):
            pixel_values = pixel_values + grayscale.getpixel((x, y))

    if pixel_values / pixel_count < 128:
        logo = Image.open(SAM_WATERMARK_WHITE)
    else:
        logo = Image.open(SAM_WATERMARK_BLACK)

    copy.paste(logo, (anchor_x, anchor_y), logo)

    return copy
