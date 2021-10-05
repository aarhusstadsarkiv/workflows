from typing import Dict, List
from pathlib import Path

from helpers import run_proc, ProcessError


async def convert(input_file: Path, output_dir, options: Dict = None) -> Dict:

    return {}


async def _convert(cmd: List) -> Dict:
    """Converts video files to thumbnails and web friendly videofile

    Parameters
    ----------
    cmd : List
        List of strs used for the ffmpeg cli command

    Raises
    ------
    FfmpegError
        If the ffmpeg CLI emits an error, a FfmpegError is raised.
    """


    cmd: List[str]
