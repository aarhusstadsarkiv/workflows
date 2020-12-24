from pathlib import Path
from typing import List, Any, Dict, Optional
from PIL import Image, ExifTags, UnidentifiedImageError
from natsort import natsorted

__version__ = "1.1.1"


class ImageConvertError(Exception):
    """Implements error to raise when conversion fails."""


def images2pdf(image_path: Path, out_file: Path) -> None:
    """Converts images from the input path to a PDF file.
    Parameters
    ----------
    image_path : pathlib.Path
        Directory where images for conversion reside.
    out_file: Path
        File to write images to.
    Raises
    ------
    ImageConvertError
        Raised when errors in conversion occur. Errors from PIL are caught
        and re-raised with this error. If no images are loaded, this error
        is raised as well.
    """

    out_pdf: Path = out_file.with_suffix(".pdf")
    images: List[Any] = []
    files_str: List[str] = [
        str(f) for f in image_path.rglob("*") if f.is_file()
    ]
    files: List[Path] = [Path(file) for file in natsorted(files_str)]

    for file in files:
        try:
            im: Any = Image.open(file)
        except UnidentifiedImageError:
            print(f"Failed to open {file} as an image.", flush=True)
        except Exception as e:
            raise ImageConvertError(e)
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
        raise ImageConvertError(
            "No images loaded! Please double check your path."
        )
    try:
        print(f"Writing images to {out_pdf}", flush=True)
        images[0].save(
            out_pdf,
            "PDF",
            resolution=100.0,
            save_all=True,
            append_images=images[1:],
        )
        print(
            f"Successfully wrote images to {out_pdf}! :)",
            flush=True,
        )
    except Exception as e:
        raise ImageConvertError(e)
