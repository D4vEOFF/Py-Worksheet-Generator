"""Reading of the plain ``key = value`` configuration files."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from . import WsgError
from .util import read_text

_TRUE = {"yes", "true", "1", "on", "y", "ano"}
_FALSE = {"no", "false", "0", "off", "n", "ne", ""}

_COMMENT_PREFIXES = ("#", ";")


def read_config(path: Path, lower_keys: bool = True) -> Dict[str, str]:
    """Parse a configuration file into an ordered dictionary."""
    if not path.is_file():
        raise WsgError(f"configuration file not found: {path}")

    values: Dict[str, str] = {}
    for number, raw in enumerate(read_text(path).splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith(_COMMENT_PREFIXES):
            continue
        if "=" not in line:
            raise WsgError(f"{path}:{number}: expected 'key = value', found: {raw.strip()}")
        key, _, value = line.partition("=")
        key = key.strip()
        if lower_keys:
            key = key.lower()
        if not key:
            raise WsgError(f"{path}:{number}: empty key")
        values[key] = value.strip()
    return values


def as_bool(value: str, default: bool = False) -> bool:
    """Interpret a configuration value as a boolean."""
    text = (value or "").strip().lower()
    if text in _TRUE:
        return True
    if text in _FALSE:
        return default if text == "" else False
    raise WsgError(f"expected yes/no, found: {value!r}")


def bool_text(value: bool) -> str:
    return "yes" if value else "no"
