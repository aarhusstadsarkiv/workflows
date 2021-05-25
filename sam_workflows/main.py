import codecs
import sys
import asyncio
from pathlib import Path

from gooey import Gooey, GooeyParser

from sam_workflows.subcommands import generate_sam_access_files
from sam_workflows.helpers import load_config

# -----------------------------------------------------------------------------
# Setup
# -----------------------------------------------------------------------------
__version__ = "0.5.0"

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
    program_name=f"SAM Workflows, version {__version__}",
    program_description="Værktøj til at arbejde med SAM-registreringer",
    navigation="SIDEBAR",
    sidebar_title="Værktøjer",
    show_sidebar=True,
    default_size=(1000, 650),
    show_restart_button=False,
    show_failure_modal=False,
    show_success_modal=False,
)
async def main() -> None:

    # General parser
    cli = GooeyParser(description="Collections of workflows to run")
    subs = cli.add_subparsers(dest="subcommand")

    # -------------------------------------------------------------------------
    # SAMaccess-parser
    # -------------------------------------------------------------------------
    sam_access = subs.add_parser(
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
            "initial_value": str(Path(Path.home(), "Workflows", "job.csv")),
            "default_dir":  str(Path(Path.home(), "Workflows")),
            "full_width": True,
        }
    )
    sam_access.add_argument(
        "sam_access_output_csv",
        metavar="Output",
        help="Sti til csv-fil, der skal re-importeres til SAM",
        widget="FileSaver",
        type=Path,
        gooey_options={
            "initial_value": str(Path(Path.home(), "Workflows", "done.csv")),
            "default_dir":  str(Path(Path.home(), "Workflows")),
            "full_width": True,
        }
    )
    sam_access.add_argument(
        "-p",
        "--plain",
        metavar="Vandmærker",
        action="store_true",
        help="Undlad at påføre vandmærker",
    )
    sam_access.add_argument(
        "-l",
        "--local",
        metavar="Upload",
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

    args = cli.parse_args()
    try:
        load_config()
    except Exception as e:
        sys.exit(e)

    if args.subcommand == "accessfiles":
        try:
            await generate_sam_access_files(
                Path(args.sam_access_input_csv),
                Path(args.sam_access_output_csv),
                no_watermark=args.plain,
                no_upload=args.local,
                overwrite=args.overwrite,
                dryrun=args.dryrun,
            )
        except Exception as e:
            sys.exit(e)
    else:
        print("No subcommand chosen", flush=True)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
