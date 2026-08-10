"""Running the LaTeX toolchain and reading back its results."""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from . import WsgError

# Between the name of the file and the page count there is nothing else, so a
# generous upper bound keeps the search from running away on a broken log.
PAGE_COUNT = re.compile(r"Output written on .{0,300}?\((\d+) pages?[,)]")
FILE_LINE_ERROR = re.compile(r"^(?:\./)?[^\s:]+\.\w+:\d+: .+")
MAX_REPORTED_ERRORS = 12


@dataclass
class CompileResult:
    """Outcome of a single LaTeX run."""

    ok: bool
    pdf: Optional[Path]
    log: Path
    pages: Optional[int] = None
    errors: List[str] = field(default_factory=list)


def find_engine() -> List[str]:
    """Return the command used for compilation, preferring latexmk."""
    if shutil.which("latexmk"):
        return ["latexmk"]
    if shutil.which("pdflatex"):
        return ["pdflatex"]
    raise WsgError(
        "neither latexmk nor pdflatex was found in PATH -- install a TeX "
        "distribution (TeX Live, MiKTeX) or add it to PATH"
    )


def compile_tex(tex_file: Path, working_dir: Path, out_dir: Path, verbose: bool = False) -> CompileResult:
    """Compile ``tex_file`` with the working directory set to ``working_dir``.

    The file itself as well as every auxiliary file lives in ``out_dir`` so
    that the worksheet folder stays clean. Relative paths used inside the
    document (images, the tasks file) are resolved against ``working_dir``.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    source = tex_file.relative_to(working_dir).as_posix()
    output = out_dir.relative_to(working_dir).as_posix()
    engine = find_engine()

    if engine[0] == "latexmk":
        commands = [
            engine
            + [
                "-pdf",
                "-interaction=nonstopmode",
                "-file-line-error",
                "-halt-on-error",
                f"-outdir={output}",
                source,
            ]
        ]
    else:
        # Without latexmk the document is compiled three times: the point
        # total and the page references need one extra pass each.
        single = engine + [
            "-interaction=nonstopmode",
            "-file-line-error",
            "-halt-on-error",
            f"-output-directory={output}",
            source,
        ]
        commands = [single, single, single]

    log = out_dir / (tex_file.stem + ".log")
    pdf = out_dir / (tex_file.stem + ".pdf")
    ok = True
    for command in commands:
        completed = subprocess.run(
            command,
            cwd=str(working_dir),
            stdout=None if verbose else subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if completed.returncode != 0:
            ok = False
            break

    if ok and not pdf.is_file():
        ok = False
    errors = [] if ok else read_errors(log)
    if not ok and not errors:
        errors = [f"the LaTeX run failed, see {log}"]

    return CompileResult(
        ok=ok,
        pdf=pdf if pdf.is_file() else None,
        log=log,
        pages=read_page_count(log),
        errors=errors,
    )


def read_page_count(log: Path) -> Optional[int]:
    """Read the number of produced pages out of the LaTeX log.

    TeX breaks the lines of the log at a fixed width (79 characters by
    default) without caring where it cuts. With a long file name the message
    ``Output written on ... (7 pages, 302742 bytes).`` therefore ends up split
    across two lines, so the message is looked for a second time in a copy of
    the log with the line breaks removed.
    """
    if not log.is_file():
        return None
    text = log.read_text(encoding="utf-8", errors="replace")
    matches = PAGE_COUNT.findall(text)
    if not matches:
        matches = PAGE_COUNT.findall(text.replace("\r", "").replace("\n", ""))
    return int(matches[-1]) if matches else None


def read_errors(log: Path) -> List[str]:
    """Collect the interesting lines of a failed LaTeX run."""
    if not log.is_file():
        return []

    collected: List[str] = []
    lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    for index, line in enumerate(lines):
        if line.startswith("!") or FILE_LINE_ERROR.match(line):
            collected.append(line.rstrip())
            for follow in lines[index + 1 : index + 3]:
                stripped = follow.rstrip()
                if stripped and not stripped.startswith("!"):
                    collected.append("    " + stripped)
        if len(collected) >= MAX_REPORTED_ERRORS:
            collected.append("    ...")
            break
    return collected
