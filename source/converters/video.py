from typing import Dict, List, Union
from pathlib import Path
from os import environ as env

from helpers import subprocess

CMD_PATH = Path.home() / env["APP_DIR"] / "bin" / "ffmpeg.exe"


def convert(file: Path, out_dir: Path, options: Dict = None) -> Dict:
    offset = 10
    thumbnail_sizes: List[Dict] = [
        {"size": 150, "suffix": "_s"},
        {"size": 640, "suffix": "_m"},
    ]
    output: Dict = {}

    if options and options.get("offset"):
        offset = options["offset"]
    if options and options.get("thumbnail_sizes"):
        thumbnail_sizes = options["thumbnail_sizes"]

    for img in thumbnail_sizes:
        cmd = [
            CMD_PATH,
            "-ss",
            f"00:00:{offset}",
            "-i",
            file,
            "-vframes",
            "1",
            "-filter:v",
            f"scale='{img['size']}:-1'",
            file.stem + f"_{img['suffix']}" + file.suffix,
        ]

        run_command(cmd)

        # ffmpeg -ss 00:00:02 -i 000410095.mp4 -vframes 1 -filter:v scale="640:-1" 000410095_m.jpg
        # ffmpeg -ss 00:00:02 -i 000410095.mp4 -vframes 1 -filter:v scale="150:-1" 000410095_s.jpg
        # ffmpeg -i 000410095.mp4 -acodec aac -crf 30 000410095_acc.mp4

        return {}

    def run_command(args: List[Union[str, Path]]) -> Dict:
        """Converts video files to thumbnails and web friendly videofile

        Parameters
        ----------
        args : List
            List of strs used with the ffmpeg cli command

        Raises
        ------
        FfmpegError
            If the ffmpeg CLI emits an error, a FfmpegError is raised.
        """
        cmd = [CMD_PATH].extend(args)
        subprocess.run_command(cmd)
        return {}


representations = {
    "representations": {
        "record_image": "https://i.vimeocdn.com/video/778956612_640",
        "record_type": "video",
        "vimeo_id": "333079975",
    },
    "representations": {
        "record_file": "https://acastorage.blob.core.windows.net/sam-access/000410093/000410093.mp4",
        "record_image": "https://acastorage.blob.core.windows.net/sam-access/000410093/000410093_m.jpg",
        "record_type": "video",
    },
}
