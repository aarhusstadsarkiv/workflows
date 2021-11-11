from os import environ as env
from pathlib import Path
from typing import Any, List, Dict, Optional

import numpy as np
from PIL import Image, ExifTags

from sam_workflows.utils import watermark
from .exceptions import ConvertError


def thumbnails(
    in_file: Path,
    out_dir: Path,
    thumbnails: List[Dict] = [
        {"size": 150, "suffix": "_s"},
        {"size": 640, "suffix": "_m"},
    ],
    no_watermark: bool = False,
    overwrite: bool = False,
    extension: str = ".jpg",
) -> List[Path]:

    # validate
    if not in_file.is_file():
        raise FileNotFoundError(f"Input-path not a file: {in_file}")

    if in_file.suffix not in env["SAM_IMAGE_FORMATS"]:
        raise ConvertError(f"Unsupported fileformat: {in_file}")

    # setup
    if not out_dir.exists():
        out_dir.mkdir(parents=True, exist_ok=True)

    try:
        img: Any = Image.open(in_file)
    except Exception as e:
        raise ConvertError(f"Error opening file {in_file}: {e}")

    # Image might be rotated. Fix, if rotatet.
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

    # Tiff-challenges
    if "16" in img.mode:
        # https://github.com/openvinotoolkit/cvat/pull/342/commits/ \
        # 1520641ce65c4d3d90cb1011f83603a70943f479
        im_data = np.array(img)
        img = Image.fromarray(im_data // (im_data.max() // 2 ** 8))

    # If not rbg, convert before doing more
    if img.mode != "RGB":
        img = img.convert("RGB")

    response: List[Path] = []
    # Generate thumbnails
    for thumb in thumbnails:
        out_file: Path = (
            out_dir / f"{in_file.stem}{thumb.get('suffix')}{extension}"
        )

        if out_file.exists() and not overwrite:
            raise FileExistsError(f"File already exists: {out_file}")

        copy_img = img.copy()
        # thumbnail() doesn't enlarge smaller img and keeps aspect-ratio
        copy_img.thumbnail((thumb.get("size"), thumb.get("size")))

        # If larger than watermark-width, add watermark
        if not no_watermark:
            if copy_img.width > int(env["SAM_WATERMARK_WIDTH"]):
                copy_img = watermark.add_watermark_to_image(copy_img)

        try:
            copy_img.save(out_file)
        except Exception as e:
            raise ConvertError(f"Error saving thumbnail from {in_file}: {e}")

        response.append(out_file)

    return response
