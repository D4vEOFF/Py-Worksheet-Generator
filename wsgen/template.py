"""Placeholder substitution and generation of the grading table."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict

from . import WsgError
from .config import read_config
from .util import sanitise_latex

PLACEHOLDER = re.compile(r"<<([A-Z0-9_]+)>>")

DEFAULT_COLUMNS = {
    "czech": ("Body", "Známka"),
    "english": ("Points", "Grade"),
}


def render(text: str, values: Dict[str, str], source: Path | None = None) -> str:
    """Replace every ``<<NAME>>`` placeholder by the matching value."""

    def replace(match: re.Match) -> str:
        name = match.group(1)
        if name not in values:
            known = ", ".join(sorted(values))
            where = f" in {source}" if source else ""
            raise WsgError(f"unknown placeholder <<{name}>>{where}; known placeholders: {known}")
        return values[name]

    return PLACEHOLDER.sub(replace, text)


def grading_table(path: Path, language: str) -> str:
    """Turn a grading file into a call of the \\wsgGradingTable macro.

    Every ``key = value`` pair becomes one row. The reserved key ``_header``
    holds the titles of both columns, separated by a semicolon.
    """
    if not path.is_file():
        return ""

    values = read_config(path, lower_keys=False)
    columns = DEFAULT_COLUMNS.get(language, DEFAULT_COLUMNS["english"])
    header = values.pop("_header", "")
    if header:
        parts = [part.strip() for part in header.split(";")]
        columns = (parts[0], parts[1] if len(parts) > 1 else "")

    rows = [
        f"\\wsgGradingRow{{{sanitise_latex(key)}}}{{{sanitise_latex(value)}}}"
        for key, value in values.items()
        if not key.startswith("_")
    ]
    if not rows:
        return ""

    return (
        f"\\wsgGradingTable{{{sanitise_latex(columns[0])}}}"
        f"{{{sanitise_latex(columns[1])}}}{{{''.join(rows)}}}"
    )
