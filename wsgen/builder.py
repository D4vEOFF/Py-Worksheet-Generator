"""Turning a worksheet folder into the final PDF files."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from . import WsgError
from .latex import compile_tex
from .project import Project, Worksheet, template_file
from .template import grading_table, render
from .util import info, read_text, relative_to_cwd, sanitise_latex, tex_path, warn, write_text

# Paper dependent settings of the template.
PAPER_SETUP = {
    "a4": {"PAPER": "a4", "FONTSIZE": "11pt", "MARGIN": "2.5cm"},
    "a5": {"PAPER": "a5", "FONTSIZE": "10pt", "MARGIN": "1.3cm"},
}


@dataclass
class BuildOptions:
    """Everything the build is parametrised with from the command line."""

    move: bool = False
    header: str = ""
    packages: str = ""
    macros: str = ""
    solutions: bool = True
    answer_space: bool = True
    results: bool = True
    number: bool = True
    a5: bool = False
    keep_aux: bool = False
    verbose: bool = False


def build_project(project: Project, numbers: Optional[set], options: BuildOptions) -> List[Path]:
    """Build every worksheet of the project, or only the selected numbers."""
    worksheets = project.worksheets()
    if not worksheets:
        raise WsgError(f"the project {project.root} contains no worksheets yet")

    if numbers:
        available = {sheet.number: sheet for sheet in worksheets}
        missing = sorted(set(numbers) - set(available))
        if missing:
            listed = ", ".join(str(number) for number in missing)
            known = ", ".join(str(number) for number in sorted(available))
            raise WsgError(f"worksheet number {listed} not found (available: {known})")
        worksheets = [available[number] for number in sorted(numbers)]

    produced: List[Path] = []
    for worksheet in worksheets:
        produced += build_worksheet(project, worksheet, options)
    return produced


def build_worksheet(project: Project, worksheet: Worksheet, options: BuildOptions) -> List[Path]:
    """Build the assignment sheet and, when requested, the solution sheet."""
    if not worksheet.tasks_path.is_file():
        raise WsgError(f"tasks file not found: {worksheet.tasks_path}")
    if " " in worksheet.tasks_path.name:
        warn(f"the name of the tasks file contains a space, LaTeX may fail: {worksheet.tasks_path.name}")

    header = project.header_path(worksheet, options.header)
    template = read_text(header)
    if "<<CONTENT>>" not in template:
        raise WsgError(f"the header template {header} does not contain the <<CONTENT>> placeholder")
    # A header copied into the project before the option existed would print
    # the number anyway -- say so instead of ignoring the request silently.
    if not _numbered(project, options) and "<<NUMBERED>>" not in template:
        warn(f"the header template {header} has no <<NUMBERED>> placeholder, the worksheet number is printed anyway")

    packages = project.file_path("packages", worksheet, options.packages)
    macros = project.file_path("macros", worksheet, options.macros)

    grading = grading_table(worksheet.grading_path, project.language)
    build_dir = worksheet.build_dir
    produced: List[Path] = []
    failed = False

    variants = [False]
    if worksheet.with_solution and options.solutions:
        variants.append(True)

    try:
        for solution in variants:
            base = worksheet.base_name + ("-solution" if solution else "")
            label = f"{base}.pdf"
            info(f"building {worksheet.directory.name} -> {base}{'-a5' if options.a5 else ''}.pdf")

            values = _placeholder_values(project, worksheet, solution, grading, options)
            # The package list and the macros are placeholder templates as well
            # -- the paper size and the language have to reach them. They are
            # written next to the generated document and pulled in with \input.
            for key, path in (("PACKAGES", packages), ("MACROS", macros)):
                target = build_dir / f"wsg-{key.lower()}.tex"
                write_text(target, render(read_text(path), values, path))
                values[key] = f"\\input{{{tex_path(target, worksheet.directory)}}}"

            source = build_dir / f"{base}.tex"
            write_text(source, render(template, values, header))

            result = compile_tex(source, worksheet.directory, build_dir, options.verbose)
            if not result.ok:
                raise WsgError(
                    f"compilation of {label} failed\n"
                    + "\n".join(f"       {line}" for line in result.errors)
                    + f"\n       log: {relative_to_cwd(result.log)}"
                )

            pdf = result.pdf
            assert pdf is not None
            if options.a5:
                pdf = _impose_a5(worksheet, pdf, result.pages, f"{base}-a5", options)

            target_dir = project.root if options.move else worksheet.directory
            target = target_dir / pdf.name
            target_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(pdf, target)
            produced.append(target)
    except BaseException:
        failed = True
        raise
    finally:
        if failed:
            if build_dir.is_dir():
                info(f"auxiliary files kept in {relative_to_cwd(build_dir)}")
        elif not options.keep_aux:
            shutil.rmtree(build_dir, ignore_errors=True)

    return produced


def _impose_a5(worksheet: Worksheet, source: Path, pages: Optional[int], base: str, options: BuildOptions) -> Path:
    """Place every A5 page twice next to each other on an A4 sheet."""
    if not pages:
        raise WsgError(
            f"could not determine the number of pages of {source.name}; "
            f"see {relative_to_cwd(source.with_suffix('.log'))}"
        )

    template = template_file("a5-imposition.tex")
    values = {
        "PAGES": ",".join(f"{page},{page}" for page in range(1, pages + 1)),
        "PDF": tex_path(source, worksheet.directory),
    }
    target = worksheet.build_dir / f"{base}.tex"
    write_text(target, render(read_text(template), values, template))

    result = compile_tex(target, worksheet.directory, worksheet.build_dir, options.verbose)
    if not result.ok:
        raise WsgError(
            f"A5 imposition of {source.name} failed\n"
            + "\n".join(f"       {line}" for line in result.errors)
            + f"\n       log: {relative_to_cwd(result.log)}"
        )
    assert result.pdf is not None
    return result.pdf


def _placeholder_values(
    project: Project,
    worksheet: Worksheet,
    solution: bool,
    grading: str,
    options: BuildOptions,
) -> Dict[str, str]:
    """Collect every value the header template may ask for."""
    values: Dict[str, str] = {
        "SUBJECT": sanitise_latex(project.subject),
        "TITLE": sanitise_latex(worksheet.title),
        "NUMBER": str(worksheet.number),
        "SCHOOL": sanitise_latex(project.value("school")),
        "CLASS": sanitise_latex(project.value("class")),
        "TEACHER": sanitise_latex(project.value("teacher")),
        "YEAR": sanitise_latex(project.value("year")),
        "LANGUAGE": project.language,
        "SOLUTIONS": "true" if solution else "false",
        "GRADED": "true" if worksheet.graded else "false",
        "CREDENTIALS": "true" if worksheet.credentials else "false",
        "ANSWER_SPACE": "true" if options.answer_space else "false",
        "RESULTS": "true" if options.results else "false",
        "NUMBERED": "true" if _numbered(project, options) else "false",
        "GRADING_TABLE": grading,
        # Filled in by build_worksheet once the two files have been written.
        "PACKAGES": "",
        "MACROS": "",
        "CONTENT": f"\\input{{{tex_path(worksheet.tasks_path, worksheet.directory)}}}",
    }
    values.update(PAPER_SETUP["a5" if options.a5 else "a4"])
    return values


def _numbered(project: Project, options: BuildOptions) -> bool:
    """Whether the "Worksheet no. N" line is printed above the title."""
    return project.numbered and options.number
