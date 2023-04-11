from pathlib import Path

from workflows.utils import sp
from .exceptions import ConvertError


CMD_PATH = Path.home() / ".aca" / "workflows" / "bin" / "ffmpeg.exe"


def convert(
    in_file: Path,
    out_file: Path,
    timeout: int = 180,
    overwrite: bool = False,
) -> None:
    if not in_file.is_file():
        raise FileNotFoundError(f"Input-path not an audio file: {in_file}")

    if not out_file.parent.exists():
        out_file.parent.mkdir(parents=True, exist_ok=True)

    if out_file.exists():
        if not overwrite:
            raise FileExistsError(f"Output-file already exists: {out_file}")
        else:
            out_file.unlink()

    cmd = [
        CMD_PATH,
        "-loglevel",
        "error",
        "-i",
        in_file,
        out_file,
    ]
    try:
        sp.run(cmd, timeout)
    except sp.ProcessError as e:
        raise ConvertError(f"ProcessError: {e}")
    except sp.TimeoutError as e:
        raise ConvertError(f"TimeoutError: {e}")
    except Exception as e:
        raise ConvertError(f"Unspecified error: {e}")
