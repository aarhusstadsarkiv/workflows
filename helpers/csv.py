import csv
from typing import List, Dict
from pathlib import Path

__version__ = "0.1.0"


class WrongFileExtensionError(Exception):
    """Raised when Path is not pointing to a csv-file"""


class MalformedHeadersError(Exception):
    """Raised when Path is not pointing to a csv-file"""


def load_csv(input: Path) -> List[Dict]:
    if not input.is_file():
        raise IsADirectoryError
    if not input.suffix == ".csv":
        raise WrongFileExtensionError(
            "The input-path is not pointing to a csv-file"
        )

    output = []
    with open(input, encoding="utf8") as ifile:
        try:
            reader = csv.DictReader(ifile)
        except Exception as e:
            raise e
    if reader.fieldnames != ["jobLabel", "uniqueID", "oasDataJsonEncoded"]:
        raise MalformedHeadersError(
            "Csv-file does not contain the right headers"
        )

        return [output.append(d) for d in reader]


def save_csv(files: List[Dict]) -> None:
    pass