import csv
from typing import List, Dict
from pathlib import Path


__version__ = "0.1.0"


class WrongFileExtensionError(Exception):
    """Raised when Path is not pointing to a csv-file"""


class MalformedHeadersError(Exception):
    """Raised when Path is not pointing to a csv-file"""


def load_csv_from_sam(input: Path) -> List[Dict]:
    # Tests
    if not input.is_file():
        raise IsADirectoryError("No csv-file at: " + str(input))
    if not input.suffix == ".csv":
        raise WrongFileExtensionError(
            "The input-path is not pointing to a csv-file"
        )
    with open(input, encoding="utf8") as ifile:
        try:
            reader = csv.DictReader(ifile)
        except Exception as e:
            raise e

        if reader.fieldnames != ["jobLabel", "uniqueID", "oasDataJsonEncoded"]:
            raise MalformedHeadersError(
                "Csv-file does not contain the right headers"
            )

        return [d for d in reader]


def save_csv_to_sam(files: List[Dict], path: Path) -> None:
    sam_output_headers = [
        "oasid",
        "thumbnail",
        "record_image",
        "record_type",
        "large_image",
        "web_document_url",
    ]

    with open(path, "w") as ofile:
        writer = csv.DictWriter(ofile, fieldnames=sam_output_headers)
        writer.writeheader()
        writer.writerows(files)
