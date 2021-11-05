import csv
from typing import List, Dict
from pathlib import Path

from sam_workflows.utils import load_oas_backup


async def filter_on_storage_id(record: Dict, value: List) -> bool:
    ids = record["storage_id"]
    if any(v for v in value if v in ids):
        return True
    return False


async def search_backup(
    backup_file: Path, id_file: Path, filters: List[Dict]
) -> None:
    print("Loading and parsing backup-file. It might take a while", flush=True)
    backup = load_oas_backup(backup_file)
    print("Filtering backup-file for matches...", flush=True)
    out: List = []

    for data in backup:
        for filter in filters:
            # Filer on storage_id
            if filter["key"] == "storage_id" and data.get("storage_id"):
                if await filter_on_storage_id(data, filter["value"]):
                    out.append(data.get("identifier"))

    if not out:
        print("No records matched your filter", flush=True)
    else:
        with open(id_file, mode="w", newline="", encoding="utf-8") as ofile:
            writer = csv.writer(ofile)
            writer.writerow(["id"])
            for row in out:
                writer.writerow([row])
        print(
            f"Found {len(out)} matching record(s). Id-list saved to {id_file}",
            flush=True,
        )
