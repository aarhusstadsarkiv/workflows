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
    img_out: Path,
    quality: int = 80,
    max_width: int = 4000,
    max_height: int = 4000,
    watermark: bool = True,
) -> str:

    error = ""
    try:
        im: Any = Image.open(img_in)
    except UnidentifiedImageError:
        error = f"Failed to open {img_in} as an image."
    except Exception as e:
        error = f"Error encountered while opening file {img_in}: {e}"
    else:
        im.load()
        # Resize max width/height is smaller than image width/height
        width, height = im.size
        scaling = 1
        if max_width and max_width / width < 1:
            scaling = max_width / width
        if max_height and max_height / height < 1:
            scaling = max_height / height
        if scaling != 1:
            new_size = (int(scaling * width), int(scaling * height))
            im = im.resize(new_size)

        # JPG image might be rotated
        if hasattr(im, "_getexif"):  # only present in JPGs
            # Find the orientation exif tag.
            orientation_key: Optional[int] = None
            for tag, tag_value in ExifTags.TAGS.items():
                if tag_value == "Orientation":
                    orientation_key = tag
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

        if watermark:
            im = add_watermark(im)

        try:
            im.save(img_out, "JPEG", quality=quality)
        except Exception as e:
            error = f"Error encountered while saving file {img_in}: {e}"
    return error


def access_files_from_pdf(pdf_file: Path) -> Dict:
    return {}


def access_files_from_image(image: Path) -> Dict:
    large_path = _convert_image_to_jpg(image)
    return {
        "oasid": image_file.name,
        "thumbnail": "tb_url",
        "record_image": "large_url",
        "record_type": "image",
        "large_image": "large_url",
        "web_document_url": "web_url",
    }


def make_sam_access_files(
    csv_in: Path, csv_out: Path, upload: bool = True, overwrite: bool = False
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
        # id_ = file.get("uniqueID")
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

        if filepath.suffix in SAM_IMAGE_FORMATS:
            lrg_path, med_path, sml_path = _generate_sam_jpgs(filepath)
            large_path = _generate_jpg(
                filepath,
                SAM_ACCESS_PATH / "large",
                max_width=1920,
                max_height=1920,
            )
        if filepath.suffix == ".pdf":


        medium_path = _generate_jpg(
            filepath, SAM_ACCESS_PATH / "medium", max_width=640, max_height=640
        )
        small_path = _generate_jpg(
            filepath, SAM_ACCESS_PATH / "small", max_width=150, max_height=150
        )

        output.append(
            {
                "oasid": image_file.name,
                "thumbnail": "tb_url",
                "record_image": "large_url",
                "record_type": "image",
                "large_image": "large_url",
                "web_document_url": "web_url",
            }
        )
        save_csv_to_sam(output)


            output.append(access_files_from_pdf(filepath))
        elif filepath.suffix in SAM_IMAGE_FORMATS:
            output.append(access_files_from_image(filepath))


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
        files: List[Dict] = load_csv_from_sam(csv_in)
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
