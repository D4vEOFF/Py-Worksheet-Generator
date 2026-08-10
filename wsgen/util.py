"""Small helpers shared by the rest of the package."""

from __future__ import annotations

import os
import re
import subprocess
import sys
import unicodedata
import webbrowser
from pathlib import Path
from typing import Iterable, Set

from . import WsgError

_SLUG_STRIP = re.compile(r"[^a-z0-9]+")
_SELECTION = re.compile(r"^(\d+)(?:\s*-\s*(\d+))?$")

# A per cent sign that is not escaped yet would comment out the rest of the
# line; the same holds for a bare & and #. Everything else is left untouched
# so that plain LaTeX may be used in the configuration values.
_UNESCAPED = re.compile(r"(?<!\\)([%&#])")


def slugify(text: str) -> str:
    """Turn a human readable name into a lowercase ASCII folder name."""
    normalised = unicodedata.normalize("NFKD", text)
    stripped = "".join(ch for ch in normalised if not unicodedata.combining(ch))
    slug = _SLUG_STRIP.sub("-", stripped.lower()).strip("-")
    return slug or "worksheet"


def sanitise_latex(value: str) -> str:
    """Escape the characters that would silently break the document."""
    return _UNESCAPED.sub(r"\\\1", value)


def parse_selection(items: Iterable[str]) -> Set[int]:
    """Turn arguments such as ``3`` or ``2-5`` into a set of worksheet numbers."""
    numbers: Set[int] = set()
    for item in items:
        match = _SELECTION.match(item.strip())
        if not match:
            raise WsgError(f"invalid worksheet selection: {item!r} (expected N or N-M)")
        start = int(match.group(1))
        end = int(match.group(2)) if match.group(2) else start
        if end < start:
            start, end = end, start
        numbers.update(range(start, end + 1))
    return numbers


def read_text(path: Path) -> str:
    """Read a UTF-8 text file and report a readable error on failure."""
    try:
        return path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        raise WsgError(f"file not found: {path}")
    except UnicodeDecodeError:
        raise WsgError(f"file is not valid UTF-8: {path}")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def open_document(path: Path) -> None:
    """Open a file in the default viewer of the current platform."""
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except Exception:  # pragma: no cover - viewer problems are not fatal
        webbrowser.open(path.as_uri())


def relative_to_cwd(path: Path) -> str:
    """Path for log messages -- relative when possible, absolute otherwise."""
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


def tex_path(path: Path, base: Path) -> str:
    """Path usable inside a TeX file (relative, forward slashes)."""
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.as_posix()


def info(message: str) -> None:
    print(f"[wsg] {message}", flush=True)


def warn(message: str) -> None:
    sys.stdout.flush()
    print(f"[wsg] warning: {message}", file=sys.stderr, flush=True)


def error(message: str) -> None:
    sys.stdout.flush()
    print(f"[wsg] error: {message}", file=sys.stderr, flush=True)
