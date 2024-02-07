import sys
import locale
from argparse import ArgumentParser
from pathlib import Path

from gooey import Gooey, GooeyParser

from workflows.commands import accessfiles, search
from workflows.config import config


@Gooey(
    program_name="ACA Workflows",
    program_description="Værktøj til at arbejde med forskellige workflows",
    # navigation="SIDEBAR",
    sidebar_title="Workflows",
    show_sidebar=True,
    default_size=(1000, 700),
    # https://github.com/chriskiehl/Gooey/issues/520#issuecomment-576155188
    # necessary for pyinstaller to work in --windowed mode (no console)
    encoding=locale.getpreferredencoding(),
    show_restart_button=True,
    show_failure_modal=False,
    show_success_modal=False,
    menu=[{'name': 'Hjælp', 'items': [{
        'type': 'Link',
        'menuTitle': 'Gå til hjælpesiden',
        'url': 'https://www.aarhusarkivet.dk'
    }]}],
)
def main() -> None:
    # Load config or exit
    try:
        config.load_json_configuration()
    except Exception:
        sys.exit()

    cli: GooeyParser = GooeyParser(description="Collections of workflows to run")

    # when using subparsers, Gooey does not support args/options outside each subparser!
    subs = cli.add_subparsers(
        title="commands",
        dest="command",
    )

    # -------------------------------------------------------------------------
    # SAMaccess-parser
    # -------------------------------------------------------------------------
    sam_access: ArgumentParser = subs.add_parser(
        "accessfiles",
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
        help="Overskriv tidligere accessfiler, både lokalt og online",
    )
    sam_access.add_argument(
        "--dryrun",
        metavar="Testkørsel",
        action="store_true",
        help="Filerne lægges lokalt i 'Overførsler'-mappen og online i en 'test'-mappe",
    )

    ###############
    # Search-parser
    ###############
    search_backup: ArgumentParser = subs.add_parser(
        "search",
        help="Generér id-liste til SAM ved at filtrere backup-filen",
    )
    # Arguments
    search_backup.add_argument(
        "backup_file",
        metavar="Backup-fil",
        help="Sti til oas backup-filen",
        widget="FileChooser",
        type=Path,
        gooey_options={
            "initial_value": str(Path.home() / "oas_backup_file.csv"),
            "default_dir": str(Path.home()),
            "full_width": True,
        },
    )
    search_backup.add_argument(
        "search_result",
        metavar="Id-list",
        help="Sti til filen med søgereultatet",
        widget="FileSaver",
        type=Path,
        gooey_options={
            "initial_value": str(Path.home() / "Workflows" / "id-list.csv"),
            "default_dir": str(Path.home() / "Workflows"),
            "full_width": True,
        },
    ),
    search_backup.add_argument(
        "--storage-id",
        metavar="Storage-id",
        type=str,
        help="Filtrér backup-filen efter storage-id(er) (adskilt med komma)",
    )


    args = cli.parse_args()
    if args.command == "accessfiles":
        try:
            accessfiles.generate_sam_access_files(
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
        filters: list = []
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
            search.search_backup(
                Path(args.backup_file),
                Path(args.search_result),
                filters=filters,
            )
        except Exception:
            sys.exit()

    else:
        print("No command chosen\n", flush=True)


if __name__ == "__main__":
    main()
