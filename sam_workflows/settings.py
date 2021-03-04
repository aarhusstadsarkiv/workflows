from pathlib import Path

PACKAGE_PATH: Path = Path(__file__).parent.resolve()

ACASTORAGE_CONTAINER = "https://acastorage.blob.core.windows.net/test"

SAM_MASTER_PATH = PACKAGE_PATH / "data" / "files_from_sam"

SAM_ACCESS_PATH = PACKAGE_PATH / "data" / "files_to_upload"

SAM_ACCESS_LARGE_SIZE = 1920
SAM_ACCESS_MEDIUM_SIZE = 640
SAM_ACCESS_SMALL_SIZE = 150

# Watermark
WATERMARK_WIDTH = 160
SAM_WATERMARK_HEIGHT = 51
SAM_WATERMARK_WHITE = PACKAGE_PATH / "images" / "as_logo_white_160x51.png"
SAM_WATERMARK_BLACK = PACKAGE_PATH / "images" / "as_logo_black_160x51.png"

# Fileformats
SAM_IMAGE_FORMATS = [
    ".tif",
    ".tiff",
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".psd",
    ".xpm",
    ".gif",
    ".webp",
]
