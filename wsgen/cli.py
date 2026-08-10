"""Command line interface of the WorkSheet Generator."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import List, Optional

from . import WsgError, __version__
from .builder import BuildOptions, build_project
from .project import CONFIG_NAME, GRADING_NAME, HEADER_NAME, Project
from .util import error, info, open_document, parse_selection, relative_to_cwd, slugify, warn

MAX_OPENED_FILES = 4

DESCRIPTION = """\
wsg -- WorkSheet Generator

Creates and compiles LaTeX worksheets. A project is a folder with config.txt
and one numbered folder per worksheet (01-name, 02-name, ...).
"""

EPILOG = """\
examples:
  wsg new "Programming in Python"     create a new project folder
  wsg add "Loops and conditions"      add the next worksheet to the project
  wsg build                           compile every worksheet of the project
  wsg build 3 5-7 --move              compile selected ones into the project root
  wsg build --a5                      two A5 copies of each sheet on one A4 page
"""


# ---------------------------------------------------------------------------
#  Commands
# ---------------------------------------------------------------------------
def command_new(args: argparse.Namespace) -> int:
    subject = args.subject or args.name
    folder = Path(args.dir) if args.dir else Path.cwd() / slugify(args.name)

    project = Project.create(
        directory=folder,
        subject=subject,
        school=args.school,
        school_class=getattr(args, "class"),
        teacher=args.teacher,
        year=args.year,
    )
    info(f"project created: {relative_to_cwd(project.root)}")
    info(f"subject: {subject}")
    info(f"edit {relative_to_cwd(project.root / CONFIG_NAME)} or {HEADER_NAME} to adjust it")
    return 0


def command_add(args: argparse.Namespace) -> int:
    project = _project(args)
    worksheet = project.add_worksheet(
        title=args.title,
        slug=slugify(args.dir) if args.dir else "",
        number=args.number,
        graded=not args.no_graded,
        solution=not args.no_solution,
        credentials=not args.no_credentials,
        grading=args.grading,
    )
    info(f"worksheet created: {relative_to_cwd(worksheet.directory)}")
    info(f"write the tasks into {relative_to_cwd(worksheet.tasks_path)}")
    return 0


def command_build(args: argparse.Namespace) -> int:
    project = _project(args)
    numbers = parse_selection(args.worksheets) if args.worksheets else None

    options = BuildOptions(
        move=args.move,
        header=args.header or "",
        packages=args.packages or "",
        macros=args.macros or "",
        solutions=not args.no_solution,
        a5=args.a5,
        keep_aux=args.keep_aux,
        verbose=args.verbose,
    )
    produced = build_project(project, numbers, options)

    info(f"done, {len(produced)} file(s) written:")
    for path in produced:
        print(f"       {relative_to_cwd(path)}")

    if args.open:
        if len(produced) > MAX_OPENED_FILES:
            warn(f"not opening {len(produced)} files, select a single worksheet to use --open")
        else:
            for path in produced:
                open_document(path)
    return 0


def command_list(args: argparse.Namespace) -> int:
    project = _project(args)
    worksheets = project.worksheets()
    print(f"project: {project.root}")
    print(f"subject: {project.subject or '-'}")
    if not worksheets:
        print("no worksheets yet -- create one with 'wsg add \"<title>\"'")
        return 0

    print()
    print(f"  {'no.':>4}  {'folder':<32} {'graded':<7} {'sol.':<5} {'grading':<8} title")
    for worksheet in worksheets:
        print(
            f"  {worksheet.number:>4}  {worksheet.directory.name:<32} "
            f"{'yes' if worksheet.graded else 'no':<7} "
            f"{'yes' if worksheet.with_solution else 'no':<5} "
            f"{'yes' if worksheet.grading_path.is_file() else 'no':<8} "
            f"{worksheet.title}"
        )
        if worksheet.number != worksheet.prefix:
            warn(
                f"{worksheet.directory.name}: number in {CONFIG_NAME} "
                f"({worksheet.number}) differs from the folder prefix ({worksheet.prefix})"
            )
    return 0


def command_clean(args: argparse.Namespace) -> int:
    project = _project(args)
    removed = 0

    for worksheet in project.worksheets():
        if worksheet.build_dir.is_dir():
            shutil.rmtree(worksheet.build_dir, ignore_errors=True)
            info(f"removed {relative_to_cwd(worksheet.build_dir)}")
            removed += 1
        if not args.pdf:
            continue
        for name in _generated_pdf_names(worksheet.base_name):
            for folder in (worksheet.directory, project.root):
                candidate = folder / name
                if candidate.is_file():
                    candidate.unlink()
                    info(f"removed {relative_to_cwd(candidate)}")
                    removed += 1

    info(f"nothing to clean" if removed == 0 else f"cleaned {removed} item(s)")
    return 0


def _generated_pdf_names(base: str) -> List[str]:
    return [
        f"{base}.pdf",
        f"{base}-a5.pdf",
        f"{base}-solution.pdf",
        f"{base}-solution-a5.pdf",
    ]


def _project(args: argparse.Namespace) -> Project:
    if args.project:
        return Project.load(Path(args.project))
    return Project.find(Path.cwd())


# ---------------------------------------------------------------------------
#  Argument parser
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wsg",
        description=DESCRIPTION,
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"wsg {__version__}")
    subparsers = parser.add_subparsers(dest="command", metavar="<command>")
    subparsers.required = True

    # -- new ----------------------------------------------------------------
    new = subparsers.add_parser(
        "new",
        help="create a new worksheet project",
        description="Create a new project folder together with its configuration and header template.",
    )
    new.add_argument("name", help="name of the subject; also used for the folder name")
    new.add_argument("--dir", help="folder to create (default: slug of the name in the current folder)")
    new.add_argument("--subject", help="subject printed into the worksheets (default: name)")
    new.add_argument("--school", default="", help="optional school name")
    new.add_argument("--class", default="", help="optional class, e.g. 3.A")
    new.add_argument("--teacher", default="", help="optional teacher name")
    new.add_argument("--year", default="", help="optional school year, e.g. 2025/2026")
    new.set_defaults(func=command_new)

    # -- add ----------------------------------------------------------------
    add = subparsers.add_parser(
        "add",
        help="add a new worksheet to a project",
        description="Create a numbered worksheet folder with its configuration and a tasks file.",
    )
    add.add_argument("title", help="title / topic of the worksheet")
    add.add_argument("-p", "--project", help="project folder (default: found from the current folder)")
    add.add_argument("--dir", help="folder name without the number (default: slug of the title)")
    add.add_argument("--number", type=int, help="number of the worksheet (default: next free one)")
    add.add_argument("--no-graded", action="store_true", help="the worksheet carries no points")
    add.add_argument("--no-solution", action="store_true", help="do not build a solution sheet")
    add.add_argument("--no-credentials", action="store_true", help="no line for the student name")
    add.add_argument("--grading", action="store_true", help=f"also create a sample {GRADING_NAME}")
    add.set_defaults(func=command_add)

    # -- build --------------------------------------------------------------
    build = subparsers.add_parser(
        "build",
        help="compile the worksheets of a project",
        description="Compile every worksheet of the project, or only the selected numbers.",
    )
    build.add_argument("worksheets", nargs="*", metavar="N", help="worksheet numbers, e.g. 3 or 5-7")
    build.add_argument("-p", "--project", help="project folder (default: found from the current folder)")
    build.add_argument("-m", "--move", action="store_true", help="put the PDF files into the project root")
    build.add_argument("--header", help="use a different header template for this run")
    build.add_argument("--packages", help="use a different package list for this run")
    build.add_argument("--macros", help="use a different macro file for this run")
    build.add_argument("--no-solution", action="store_true", help="build the assignment sheets only")
    build.add_argument("--a5", action="store_true", help="two A5 copies of every sheet on one A4 page")
    build.add_argument("--keep-aux", action="store_true", help="keep the auxiliary files of the LaTeX run")
    build.add_argument("-v", "--verbose", action="store_true", help="show the output of the LaTeX run")
    build.add_argument("--open", action="store_true", help="open the produced PDF files")
    build.set_defaults(func=command_build)

    # -- list ---------------------------------------------------------------
    listing = subparsers.add_parser("list", help="show the worksheets of a project")
    listing.add_argument("-p", "--project", help="project folder (default: found from the current folder)")
    listing.set_defaults(func=command_list)

    # -- clean --------------------------------------------------------------
    clean = subparsers.add_parser("clean", help="remove the files generated by the build")
    clean.add_argument("-p", "--project", help="project folder (default: found from the current folder)")
    clean.add_argument("--pdf", action="store_true", help="remove the generated PDF files as well")
    clean.set_defaults(func=command_clean)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except WsgError as exc:
        error(str(exc))
        return 1
    except KeyboardInterrupt:  # pragma: no cover
        error("interrupted")
        return 130
