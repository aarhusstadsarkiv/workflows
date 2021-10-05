from typing import Dict, List, Union
from pathlib import Path
from os import environ as env

from helpers import run_proc, ProcessError


CMD_PATH: Path.home() / env["APP_DIR"] / str("bin") / str("ffmpeg.exe")


async def convert(input_file: Path, output_dir, options: Dict = None) -> Dict:
    offset = 10
    thumbnail_sizes = [150, 640]
    if options and options.get("offset"):
        offset = options["offset"]
    if options and options.get("thumbnail_sizes"):
        offset = options["thumbnail_sizes"]

    return {}


async def _convert(args: List[Union[str, Path]]) -> Dict:
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


    cmd: List[str]


representations = {
  "representations": {
    "record_image": "https://i.vimeocdn.com/video/778956612_640",
    "record_type": "video",
    "vimeo_id": "333079975"
  },
  "representations": {
    "record_file": "https://acastorage.blob.core.windows.net/sam-access/000410093/000410093.mp4",
    "record_image": "https://acastorage.blob.core.windows.net/sam-access/000410093/000410093_m.jpg",
    "record_type": "video"
  }
}