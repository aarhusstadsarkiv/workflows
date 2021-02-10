from pathlib import Path

SAM_MASTER_PATH = Path(
    "/Users/cjk/github/sam-workflows/sam_workflows/data/export_files"
)

SAM_ACCESS_PATH = Path(
    "/Users/cjk/github/sam-workflows/sam_workflows/data/access_files"
)

SAM_ACCESS_LARGE_PATH = SAM_ACCESS_PATH / "large"
SAM_ACCESS_MEDIUM_PATH = SAM_ACCESS_PATH / "medium"
SAM_ACCESS_SMALL_PATH = SAM_ACCESS_PATH / "small"

# SAM_MASTER_PATH = Path("M:\\Borgerservice-Biblioteker\\Stadsarkivet" \
# "\\_DIGITALT ARKIV\\ark_binary_store")

# SAM_ACCESS_PATH = Path("M:\\Borgerservice-Biblioteker\\Stadsarkivet" \
# "\\_DIGITALT ARKIV\\ark_binary_access")

# SAM_ACCESS_LARGE_PATH = Path("M:\\Borgerservice-Biblioteker\\Stadsarkivet" \
# "\\_DIGITALT ARKIV\\ark_binary_access\large")

# SAM_ACCESS_MEDIUM_PATH = Path("M:\\Borgerservice-Biblioteker\\Stadsarkivet" \
# "\\_DIGITALT ARKIV\\ark_binary_access\medium")

# SAM_ACCESS_SMALL_PATH = Path("M:\\Borgerservice-Biblioteker\\Stadsarkivet" \
# "\\_DIGITALT ARKIV\\ark_binary_access\small")

SAM_ACCESS_LARGE_SIZE = 1920
SAM_ACCESS_MEDIUM_SIZE = 640
SAM_ACCESS_SMALL_SIZE = 150

# Watermark
SAM_WATERMARK_WIDTH = 160
SAM_WATERMARK_HEIGHT = 51
SAM_WATERMARK_WHITE = Path("./images/as_logo_white_160x51.png")
SAM_WATERMARK_BLACK = Path("./images/as_logo_black_160x51.png")

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
