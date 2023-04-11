import sys
import asyncio
import locale

# from datetime import date
from pathlib import Path
from typing import List, Callable, Any
from functools import wraps
from importlib import metadata

from gooey import Gooey, GooeyParser

from workflows.commands import accessfiles, search
from workflows.config import config


def coro(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return asyncio.run(func(*args, **kwargs))

    return wrapper


__version__ = metadata.version("workflows")


@Gooey(
    program_name=f"ACA Workflows, version {__version__}",
    program_description="Værktøj til at arbejde med forskellige workflows",
    navigation="SIDEBAR",
    sidebar_title="Workflows",
    show_sidebar=True,
    default_size=(1000, 600),
    encoding=locale.getpreferredencoding(),
    show_restart_button=True,
    show_failure_modal=False,
    show_success_modal=False,
)
@coro
async def main() -> None:
    # Load config or exit
    try:
        config.load_json_configuration()
    except Exception:
        sys.exit()

    cli = GooeyParser(
        # usage="aca [-h] [--ignore-gooey] COMMAND [OPTIONS]",
        description="Collections of workflows to run"
    )
    cli.add_argument("--version", action="version", version=__version__)
    subs = cli.add_subparsers(
        title="commands",
        dest="command",
        # metavar="",  # mute default metavar-output {list of commands}
    )

    # -------------------------------------------------------------------------
    # SAMaccess-parser
    # -------------------------------------------------------------------------
    sam_access = subs.add_parser(
        "accessfiles",
        # dest="access-files",
        help="Lav accessfiler ud fra digitale registreringer i SAM",
    )
    # Arguments
    sam_access.add_argument(
        "sam_access_input_csv",
        metavar="Input",
        help="Sti til csv-fil, der er eksporteret fra SAM",
        widget="FileChooser",
        type=Path,
        gooey_options={
            "initial_value": str(Path.home() / "Workflows" / "job.csv"),
            "default_dir": str(Path.home() / "Workflows"),
            "full_width": True,
        },
    )
    sam_access.add_argument(
        "sam_access_output_csv",
        metavar="Output",
        help="Sti til csv-fil, der skal re-importeres til SAM",
        widget="FileSaver",
        type=Path,
        gooey_options={
            "initial_value": str(Path.home() / "Workflows" / "done.csv"),
            "default_dir": str(Path.home() / "Workflows"),
            "full_width": True,
        },
    )
    sam_access.add_argument(
        "--plain",
        metavar="Undlad vandmærker",
        action="store_true",
        help="Undlad at påføre vandmærker",
    )
    sam_access.add_argument(
        "--local",
        metavar="Undlad upload",
        action="store_true",
        help="Undlad at uploade filerne til vores online server",
    )
    sam_access.add_argument(
        "--overwrite",
        metavar="Overskriv",
        action="store_true",
        help="Overskriv tidligere accessfiler lokalt og online",
    )
    sam_access.add_argument(
        "--dryrun",
        metavar="Testkørsel",
        action="store_true",
        help=(
            "Accessfilerne lægges lokalt i 'Overførsler'-mappen og online i \
            'test'-containeren",
        ),
    )

    ###############
    # Search-parser
    ###############
    search_backup = subs.add_parser(
        "search",
        help="Generér id-liste til SAM ved at filtrere backup-filen",
    )
    # Arguments
    search_backup.add_argument(
        "backup_file",
        # metavar="Backup-fil",
        help="Sti til backup-filen",
        widget="FileChooser",
        type=Path,
        # dest="backupfile",
        gooey_options={
            "initial_value": str(Path.home() / "oas_backup_file.csv"),
            "default_dir": str(Path.home()),
            "full_width": True,
        },
    )
    search_backup.add_argument(
        "search_result",
        # metavar="Id-list",
        help="Sti til filen med søgereultatet",
        widget="FileSaver",
        type=Path,
        # dest="searchresult",
        gooey_options={
            "initial_value": str(Path.home() / "Workflows" / "id-list.csv"),
            "default_dir": str(Path.home() / "Workflows"),
            "full_width": True,
        },
    ),
    search_backup.add_argument(
        "--storage-id",
        # metavar="Storage-id",
        type=str,
        # dest="storage_id",
        help="Filtrér backup-filen efter storage-id(er) (adskilt med komma)",
    )
    args = cli.parse_args()

    if args.command == "accessfiles":
        try:
            await accessfiles.generate_sam_access_files(
                Path(args.sam_access_input_csv),
                Path(args.sam_access_output_csv),
                no_watermark=args.plain,
                local=args.local,
                overwrite=args.overwrite,
                dryrun=args.dryrun,
            )
        except Exception:
            sys.exit()

    elif args.command == "search":
        filters: List = []
        if args.storage_id:
            filters.append(
                {
                    "key": "storage_id",
                    "value": [
                        x.strip() for x in str(args.storage_id).split(",")
                    ],
                }
            )
        try:
            await search.search_backup(
                Path(args.backup_file),
                Path(args.search_result),
                filters=filters,
            )
        except Exception:
            sys.exit()

    else:
        print("No command chosen", flush=True)
    print("", flush=True)  # add line to output window


if __name__ == "__main__":
    main()
