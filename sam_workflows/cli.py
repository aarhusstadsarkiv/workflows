import codecs
import sys
import asyncio
from pathlib import Path
from gooey import Gooey, GooeyParser

from sam_workflows.commands import generate_sam_access_files, search_backup
from config import load_json_config, load_toml_config

# -----------------------------------------------------------------------------
# Setup
# -----------------------------------------------------------------------------
__version__ = "0.6.0"

utf8_stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
utf8_stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")
if sys.stdout.encoding != "UTF-8":
    sys.stdout = utf8_stdout  # type: ignore
if sys.stderr.encoding != "UTF-8":
    sys.stderr = utf8_stderr  # type: ignore

# https://chriskiehl.com/article/packaging-gooey-with-pyinstaller
# nonbuffered_stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
# sys.stdout = nonbuffered_stdout


@Gooey(
    program_name=f"ACA Workflows, version {__version__}",
    program_description="Værktøj til at arbejde med forskellige workflows",
    navigation="SIDEBAR",
    sidebar_title="Værktøjer",
    show_sidebar=True,
    default_size=(1000, 650),
    show_restart_button=False,
    show_failure_modal=False,
    show_success_modal=False,
)
async def main() -> None:
    # Load config or exit
    try:
        load_json_config()
    except Exception as e:
        sys.exit(e)

    config = load_toml_config()
    cli = GooeyParser(
        # usage="aca [-h] [--ignore-gooey] COMMAND [OPTIONS]",
        description="Collections of workflows to run"
    )
    subs = cli.add_subparsers(
        title="commands",
        dest="command",
        metavar="",  # mute default metavar-output {list of commands}
    )

    # -------------------------------------------------------------------------
    # SAMaccess-parser
    # -------------------------------------------------------------------------
    sam_access = subs.add_parser(
        "accessfiles",
        # title="accfiles",
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
            "initial_value": str(Path(Path.home(), "Workflows", "job.csv")),
            "default_dir": str(Path(Path.home(), "Workflows")),
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
            "initial_value": str(Path(Path.home(), "Workflows", "done.csv")),
            "default_dir": str(Path(Path.home(), "Workflows")),
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
        help="Accessfilerne lægges kun i din 'Overførsler'-mappe",
    )

    ###############
    # Search-parser
    ###############
    search = subs.add_parser(
        "search",
        help="Generér id-liste til SAM ved at filtrere backup-filen",
    )
    # Arguments
    search.add_argument(
        "backup_file",
        metavar="Backup-fil",
        help="Sti til backup-filen",
        widget="FileChooser",
        type=Path,
        # dest="backupfile",
        gooey_options={
            "initial_value": str(Path(config["sam_backup_path"], "oas_backup_file.csv")),
            "default_dir": config["sam_backup_path"],
            "full_width": True,
        },
    )
    search.add_argument(
        "search_result",
        metavar="Id-list",
        help="Sti til filen med søgereultatet",
        widget="FileSaver",
        type=Path,
        # dest="searchresult",
        gooey_options={
            "initial_value": str(
                Path(Path.home(), "Workflows", "id-list.csv")
            ),
            "default_dir": str(Path(Path.home(), "Workflows")),
            "full_width": True,
        },
    ),
    search.add_argument(
        "--storage-id",
        # metavar="Storage-id",
        type=str,
        # dest="storage_id",
        help="Filtrér backup-filen efter et bestemt storage-id",
    )
    args = cli.parse_args()

    if args.command == "accessfiles":
        try:
            await generate_sam_access_files(
                Path(args.sam_access_input_csv),
                Path(args.sam_access_output_csv),
                no_watermark=args.plain,
                local=args.local,
                overwrite=args.overwrite,
                dryrun=args.dryrun,
            )
        except Exception as e:
            sys.exit(e)

    elif args.command == "search":
        try:
            await search_backup(
                Path(args.backup_file),
                Path(args.search_result),
                filters=[{"key": "storage_id", "value": args.storage_id}],
            )
        except Exception as e:
            sys.exit(e)

    else:
        print("No command chosen", flush=True)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
