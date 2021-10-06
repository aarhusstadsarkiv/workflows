from pathlib import Path
from os import environ as env

from helpers import subprocess

CMD_PATH = Path.home() / env["APP_DIR"] / "bin" / "ffmpeg.exe"


def thumbnail(
    in_file: Path, out_file: Path, size: int = 150, offset: int = 8
) -> None:

    cmd = [
        CMD_PATH,
        "-ss",
        f"00:00:{offset:02}",
        "-i",
        in_file,
        "-vframes",
        "1",
        "-filter:v",
        f"scale='{size}:-1'",
        out_file,
    ]

    subprocess.run_command(cmd)


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
