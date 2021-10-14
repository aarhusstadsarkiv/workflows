import csv
from typing import List, Dict
from pathlib import Path


class WrongFileExtensionError(Exception):
    """Raised when Path is not pointing to a csv-file"""


class MalformedHeadersError(Exception):
    """Raised when Path is not pointing to a csv-file"""


def load_csv_from_sam(input: Path) -> List[Dict]:

    if not input.is_file():
        raise FileNotFoundError("No csv-file at: " + str(input))
    if not input.suffix == ".csv":
        raise WrongFileExtensionError(
            "The input-path is not pointing to a csv-file"
        )

    with open(input, encoding="utf8") as ifile:
        reader = csv.DictReader(ifile)

        if reader.fieldnames != ["jobLabel", "uniqueID", "oasDataJsonEncoded"]:
            raise MalformedHeadersError(
                "Imported csv-file does not contain the right headers"
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
        "record_file",
    ]

    with open(path, "w", newline="") as ofile:
        writer = csv.DictWriter(ofile, fieldnames=sam_output_headers)
        writer.writeheader()
        writer.writerows(files)
