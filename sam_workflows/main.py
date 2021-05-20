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
__version__ = "0.3.0"

utf8_stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
utf8_stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")
if sys.stdout.encoding != "UTF-8":
    sys.stdout = utf8_stdout  # type: ignore
if sys.stderr.encoding != "UTF-8":
    sys.stderr = utf8_stderr  # type: ignore


@Gooey(
    program_name=f"SAM Workflows, version {__version__}",
    program_description="Simple tool to work with SAM-workflows",
    navigation="SIDEBAR",
    default_size=(800, 550),
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
        "sam_access", help="Generate access-files from master-files"
    )
    # Arguments
    sam_access.add_argument(
        "sam_access_input_csv",
        metavar="Input",
        help="Path to csv-file exported from SAM",
        widget="FileChooser",
        type=Path,
    )
    sam_access.add_argument(
        "sam_access_output_csv",
        metavar="Output",
        help="Path to csv-file to re-import into SAM",
        widget="FileSaver",
        type=Path,
    )
    sam_access.add_argument(
        "--watermark",
        metavar="Add watermark",
        action="store_true",
        default=False,
        help="Add watermark to access-images",
    )
    sam_access.add_argument(
        "--upload",
        metavar="Upload",
        action="store_true",
        default=False,
        help="Upload access-images to Azure",
    )
    sam_access.add_argument(
        "--overwrite",
        metavar="Overwrite",
        action="store_true",
        default=False,
        help="Overwrite previously uploaded access-imagess in Azure",
    )
    sam_access.add_argument(
        "--dryrun",
        metavar="Dryrun",
        action="store_true",
        default=False,
        help="Disable upload and work with files from 'tests'-folder",
    )

    args = cli.parse_args()
    try:
        load_config()
    except Exception as e:
        sys.exit(e)

    if args.subcommand == "sam_access":
        try:
            await generate_sam_access_files(
                Path(args.sam_access_input_csv),
                Path(args.sam_access_output_csv),
                watermark=args.watermark,
                upload=args.upload,
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
