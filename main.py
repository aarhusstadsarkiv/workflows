import codecs

# import os
import sys
from pathlib import Path

from gooey import Gooey, GooeyParser

from subcommands import make_sam_access_files, images2pdf


# -----------------------------------------------------------------------------
# Setup
# -----------------------------------------------------------------------------

utf8_codec = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
if sys.stdout.encoding != "UTF-8":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
if sys.stderr.encoding != "UTF-8":
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

# nonbuffered_stdout = os.fdopen(sys.stdout.fileno(), "w", 0)
# sys.stdout = nonbuffered_stdout

__version__ = "0.1.0"


@Gooey(
    program_name="SAM Workflows",
    program_description="Simple tool to work with SAM-workflows",
    navigation="SIDEBAR",
    default_size=(800, 550),
    show_restart_button=False,
    show_failure_modal=False,
    show_success_modal=False,
)
def main() -> None:

    # General parser
    cli = GooeyParser(description="Collections of workflows to run")
    subs = cli.add_subparsers(dest="subcommand")

    # -------------------------------------------------------------------------
    # PDF2access-parser
    # -------------------------------------------------------------------------
    sam_access = subs.add_parser(
        "sam_access", help="Generate access-files from master-files"
    )
    # Arguments
    sam_access.add_argument(
        "sam_access_input_file",
        metavar="Input",
        help="Path to csv-file exported from SAM",
        widget="FileChooser",
        type=Path,
    )
    sam_access.add_argument(
        "sam_access_output_file",
        metavar="Output",
        help="Path to csv-file to re-import into SAM",
        widget="FileSaver",
        type=Path,
    )
    sam_access.add_argument(
        "--no-watermark",
        metavar="No watermark",
        action="store_true",
        help="Do not watermark access-images",
    )
    sam_access.add_argument(
        "--no-upload",
        metavar="No upload",
        action="store_true",
        help="Do not upload access-images to Azure",
    )
    sam_access.add_argument(
        "--overwrite",
        metavar="Overwrite",
        action="store_true",
        help="Overwrite previously uploaded access-imagess in Azure",
    )

    # -------------------------------------------------------------------------
    # PDF2access-parser
    # -------------------------------------------------------------------------
    pdf2access = subs.add_parser(
        "pdf2access", help="Generate thumbnails from pdf-files"
    )
    # Arguments
    pdf2access.add_argument(
        "pdf2access_input_file",
        metavar="input file",
        help="csv-file with metadata about the pdf-files",
        widget="FileChooser",
        type=Path,
    )
    pdf2access.add_argument(
        "pdf2access_output_file",
        metavar="output file",
        help="Path to csv-file with output-data",
        widget="FileSaver",
        type=Path,
    )

    # -------------------------------------------------------------------------
    # Images2pdf-parser
    # -------------------------------------------------------------------------
    images2pdf = subs.add_parser(
        "images2pdf",
        help="Generate a single pdf-file from a directory with image-files",
    )
    # Arguments
    images2pdf.add_argument(
        "images2pdf_input_folder",
        metavar="Imagefolder",
        help="Path to folder containing images to combine to a pdf-file",
        widget="DirChooser",
        type=Path,
    )
    images2pdf.add_argument(
        "images2pdf_output_file",
        metavar="Output pdf-file",
        help="Path to resulting pdf-file",
        widget="FileSaver",
        type=Path,
    )

    args = cli.parse_args()

    if args.subcommand == "pdf2access":
        print(args.pdf2access_input_file, flush=True)

    elif args.subcommand == "sam_access":
        try:
            make_sam_access_files(
                Path(args.sam_access_input_file),
                Path(args.sam_access_output_file),
                no_watermark=args.no_watermark,
                no_upload=args.no_upload,
                overwrite=args.overwrite,
            )
        except Exception as e:
            sys.exit(e)

    elif args.subcommand == "images2pdf":
        try:
            images2pdf(
                Path(args.images2pdf_input_folder),
                Path(args.images2pdf_output_file),
            )
        except Exception as e:
            sys.exit(e)

    else:
        print("No subcommand chosen", flush=True)


if __name__ == "__main__":
    main()