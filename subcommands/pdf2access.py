import json
from pathlib import Path
from typing import List, Any, Dict, Optional
from PIL import Image, UnidentifiedImageError

from helpers import load_csv

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class PDFConvertError(Exception):
    """Implements error to raise when conversion fails."""


# -----------------------------------------------------------------------------
# Functions
# -----------------------------------------------------------------------------


def pdf2access(csv_in: Path, csv_out: Path) -> None:
    """Generates thumbnail images from the input path.
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
    """
    try:
        files: List[Dict] = load_csv(csv_in)
    except Exception as e:
        raise e

    output: List[Dict] = []

    for file in files:
        id_ = file.get("uniqueID")
        data = json.loads(file.get("oasDataJsonEncoded"))
        legal_status = data.get("other_legal_restrictions", "4")
        constractual_status = data.get("contractual_status", "1")

        if int(legal_status.split(";")[0]) > 1:
            continue
        if int(constractual_status.split(";")[0]) < 3:
            continue

        try:
            im: Any = Image.open(file)
        except UnidentifiedImageError:
            print(f"Failed to open {file} as an image.", flush=True)
        except Exception as e:
            raise PDFConvertError(e)
        else:
            print(f"Loading {file}", flush=True)
            im.load()

            # Cannot save alpha channel to PDF
            if im.mode == "RGBA":
                im = im.convert("RGB")

            # JPG image might be rotated
            if hasattr(im, "_getexif"):  # only present in JPGs
                # Find the orientation exif tag.
                for tag, tag_value in ExifTags.TAGS.items():
                    if tag_value == "Orientation":
                        orientation_key: int = tag
                        break

                # If exif data is present, rotate image according to
                # orientation value.
                if im.getexif() is not None:
                    exif: Dict[Any, Any] = dict(im.getexif().items())
                    orientation: Optional[int] = exif.get(orientation_key)
                    if orientation == 3:
                        im = im.rotate(180)
                    elif orientation == 6:
                        im = im.rotate(270)
                    elif orientation == 8:
                        im = im.rotate(90)

            images.append(im)

    if not images:
        raise PDFConvertError(
            "No pdf-file loaded! Please double check your path."
        )
    try:
        print(f"Writing images to ...", flush=True)
        images[0].save(
            csv_out,
            "PDF",
            resolution=100.0,
            save_all=True,
            append_images=images[1:],
        )
    except Exception as e:
        raise PDFConvertError(e)
