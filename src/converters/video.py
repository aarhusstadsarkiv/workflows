from pathlib import Path
from os import environ as env
from typing import List, Dict

from helpers import subprocess

CMD_PATH = Path.home() / env["APP_DIR"] / "bin" / "ffmpeg.exe"


class VideoConvertError(Exception):
    """Implements error to raise when video conversion fails."""


def thumbnails(
    in_file: Path,
    out_dir: Path,
    thumbnails: List[Dict] = [
        {"size": 150, "suffix": "_s"},
        {"size": 640, "suffix": "_m"},
    ],
    watermark: bool = True,
    overwrite: bool = True,
    extension: str = ".jpg",
    offset: int = 8,
) -> List[Path]:

    # validate
    if not in_file.is_file():
        raise FileNotFoundError(f"Input-path not a pdf-file: {in_file}")

    if in_file.suffix not in env["SAM_VIDEO_FORMATS"]:
        raise VideoConvertError(f"Unsupported fileformat: {in_file}")

    # setup
    if not out_dir.exists():
        out_dir.mkdir(parents=True, exist_ok=True)

    response: List[Path] = []
    for thumb in thumbnails:
        out_file: Path = (
            out_dir / f"{in_file.stem}{thumb.get('suffix')}{extension}"
        )

        if out_file.exists() and not overwrite:
            raise FileExistsError(f"File already exists: {out_file}")

        cmd = [
            CMD_PATH,
            "-ss",
            f"00:00:{offset:02}",
            "-i",
            in_file,
            "-vframes",
            "1",
            "-filter:v",
            f"scale='{thumb.get('size')}:-1'",
            out_file,
        ]
        subprocess.run_command(cmd)

        response.append(out_file)

    return response


def convert(
    in_file: Path, out_file: Path, timeout: int = 30, quality: int = 30
) -> None:

    cmd = [
        CMD_PATH,
        "-i",
        in_file,
        "-crf",
        f"{quality}",
        "-vcodec",
        "h264",
        "-acodec",
        "aac",
        out_file,
    ]

    subprocess.run_command(cmd, timeout)


representations = [
    {
        "record_image": "https://i.vimeocdn.com/video/778956612_640",
        "record_type": "video",
        "vimeo_id": "333079975",
    },
    {
        "record_file": "https://acastorage.blob.../000410093.mp4",
        "record_image": "https://acastorage.blob.../000410093_m.jpg",
        "record_type": "video",
    },
]
