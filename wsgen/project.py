"""Discovery and creation of worksheet projects."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from . import WsgError
from .config import as_bool, read_config
from .template import render
from .util import slugify, write_text

CONFIG_NAME = "config.txt"
HEADER_NAME = "default-header.tex"
PACKAGES_NAME = "default-packages.tex"
MACROS_NAME = "default-macros.tex"
TASKS_NAME = "tasks.tex"
GRADING_NAME = "grading.txt"
BUILD_DIR_NAME = "wsg-build"

# Files copied into a new project; the key is the configuration key which may
# point at a different file, the value is the name used in the installation.
PROJECT_FILES = {
    "header": HEADER_NAME,
    "packages": PACKAGES_NAME,
    "macros": MACROS_NAME,
}

DIR_PATTERN = re.compile(r"^(\d+)[-_](.*)$")

INSTALL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = INSTALL_ROOT / "templates"
DEFAULT_HEADER = INSTALL_ROOT / HEADER_NAME


def template_file(name: str) -> Path:
    path = TEMPLATES_DIR / name
    if not path.is_file():
        raise WsgError(f"template is missing from the installation: {path}")
    return path


@dataclass
class Worksheet:
    """A single worksheet, i.e. one numbered folder inside a project."""

    directory: Path
    prefix: int
    config: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, directory: Path) -> "Worksheet":
        match = DIR_PATTERN.match(directory.name)
        if not match:
            raise WsgError(f"folder name does not start with a number: {directory.name}")
        config = read_config(directory / CONFIG_NAME)
        return cls(directory=directory, prefix=int(match.group(1)), config=config)

    @property
    def number(self) -> int:
        raw = self.config.get("number", "").strip()
        if not raw:
            return self.prefix
        if not raw.isdigit():
            raise WsgError(f"{self.directory / CONFIG_NAME}: 'number' must be a whole number")
        return int(raw)

    @property
    def title(self) -> str:
        return self.config.get("title", "").strip()

    @property
    def base_name(self) -> str:
        """Name used for the generated files."""
        return self.directory.name

    @property
    def tasks_path(self) -> Path:
        return self.directory / self.config.get("tasks", TASKS_NAME).strip()

    @property
    def grading_path(self) -> Path:
        return self.directory / (self.config.get("grading", GRADING_NAME).strip() or GRADING_NAME)

    @property
    def graded(self) -> bool:
        return as_bool(self.config.get("graded", "yes"), True)

    @property
    def with_solution(self) -> bool:
        return as_bool(self.config.get("solution", "yes"), True)

    @property
    def credentials(self) -> bool:
        return as_bool(self.config.get("credentials", "yes"), True)

    @property
    def header_override(self) -> str:
        return self.config.get("header", "").strip()

    def file_override(self, key: str) -> str:
        """Value of ``header``, ``packages`` or ``macros`` of this worksheet."""
        return self.config.get(key, "").strip()

    @property
    def build_dir(self) -> Path:
        return self.directory / BUILD_DIR_NAME


@dataclass
class Project:
    """A folder holding the project configuration and the worksheet folders."""

    root: Path
    config: Dict[str, str] = field(default_factory=dict)

    # ------------------------------------------------------------------ load
    @classmethod
    def load(cls, root: Path) -> "Project":
        root = root.resolve()
        if not (root / CONFIG_NAME).is_file():
            raise WsgError(f"no {CONFIG_NAME} found in {root}")
        return cls(root=root, config=read_config(root / CONFIG_NAME))

    @classmethod
    def find(cls, start: Path) -> "Project":
        """Look for a project in the given folder and in all its parents."""
        current = start.resolve()
        for candidate in [current, *current.parents]:
            if (candidate / CONFIG_NAME).is_file() and cls._looks_like_project(candidate):
                return cls.load(candidate)
        raise WsgError(
            f"no worksheet project found in {start} or any parent folder "
            f"(a project folder contains {CONFIG_NAME})"
        )

    @staticmethod
    def _looks_like_project(path: Path) -> bool:
        """A worksheet folder also holds a config.txt -- tell them apart."""
        if not DIR_PATTERN.match(path.name):
            return True
        try:
            children = [child for child in path.iterdir() if child.is_dir()]
        except OSError:
            return False
        return any(
            DIR_PATTERN.match(child.name) and (child / CONFIG_NAME).is_file()
            for child in children
        )

    # ------------------------------------------------------------- properties
    @property
    def subject(self) -> str:
        return self.config.get("subject", "").strip()

    @property
    def language(self) -> str:
        return self.config.get("language", "czech").strip().lower() or "czech"

    def value(self, key: str) -> str:
        return self.config.get(key, "").strip()

    # ------------------------------------------------------------- worksheets
    def worksheets(self) -> List[Worksheet]:
        found = []
        for child in sorted(self.root.iterdir()):
            if not child.is_dir() or not DIR_PATTERN.match(child.name):
                continue
            if not (child / CONFIG_NAME).is_file():
                continue
            found.append(Worksheet.load(child))
        found.sort(key=lambda sheet: (sheet.prefix, sheet.directory.name))
        return found

    def next_number(self) -> int:
        numbers = [sheet.prefix for sheet in self.worksheets()]
        return max(numbers) + 1 if numbers else 1

    # ------------------------------------------------------- template files
    def file_path(
        self,
        key: str,
        worksheet: Optional[Worksheet] = None,
        override: str = "",
    ) -> Path:
        """Resolve one of the template files, honouring every level of override.

        ``key`` is ``header``, ``packages`` or ``macros``. The worksheet wins
        over the project, the project over the copy in the installation.
        """
        default = PROJECT_FILES[key]
        candidates: List[str] = []
        if override:
            candidates.append(override)
        if worksheet is not None and worksheet.file_override(key):
            candidates.append(worksheet.file_override(key))
        if self.value(key):
            candidates.append(self.value(key))
        candidates.append(default)

        bases = [Path.cwd()]
        if worksheet is not None:
            bases.append(worksheet.directory)
        bases += [self.root, INSTALL_ROOT]

        for candidate in candidates:
            path = Path(candidate)
            if path.is_absolute():
                if path.is_file():
                    return path
                continue
            for base in bases:
                resolved = base / path
                if resolved.is_file():
                    return resolved.resolve()

        raise WsgError(f"{key} file not found: {override or candidates[0]}")

    def header_path(self, worksheet: Optional[Worksheet] = None, override: str = "") -> Path:
        return self.file_path("header", worksheet, override)

    # --------------------------------------------------------------- creation
    @classmethod
    def create(
        cls,
        directory: Path,
        subject: str,
        school: str = "",
        school_class: str = "",
        teacher: str = "",
        year: str = "",
    ) -> "Project":
        if directory.exists() and any(directory.iterdir()):
            raise WsgError(f"folder already exists and is not empty: {directory}")

        directory.mkdir(parents=True, exist_ok=True)
        values = {
            "SUBJECT": subject,
            "SCHOOL": school,
            "CLASS": school_class,
            "TEACHER": teacher,
            "YEAR": year,
        }
        source = template_file("project-config.txt")
        write_text(directory / CONFIG_NAME, render(source.read_text(encoding="utf-8"), values, source))

        for name in PROJECT_FILES.values():
            installed = INSTALL_ROOT / name
            if not installed.is_file():
                raise WsgError(f"{name} is missing from the installation: {installed}")
            shutil.copy2(installed, directory / name)

        return cls.load(directory)

    def add_worksheet(
        self,
        title: str,
        slug: str = "",
        number: Optional[int] = None,
        graded: bool = True,
        solution: bool = True,
        credentials: bool = True,
        grading: bool = False,
    ) -> Worksheet:
        number = self.next_number() if number is None else number
        if number < 0:
            raise WsgError("worksheet number must not be negative")

        folder = self.root / f"{number:02d}-{slug or slugify(title)}"
        if folder.exists():
            raise WsgError(f"worksheet folder already exists: {folder}")
        for sheet in self.worksheets():
            if sheet.prefix == number:
                raise WsgError(f"worksheet number {number} is already used by {sheet.directory.name}")

        folder.mkdir(parents=True)
        values = {
            "NUMBER": str(number),
            "TITLE": title,
            "GRADED": "yes" if graded else "no",
            "SOLUTION": "yes" if solution else "no",
            "CREDENTIALS": "yes" if credentials else "no",
        }
        source = template_file("worksheet-config.txt")
        write_text(folder / CONFIG_NAME, render(source.read_text(encoding="utf-8"), values, source))

        source = template_file(TASKS_NAME)
        write_text(folder / TASKS_NAME, render(source.read_text(encoding="utf-8"), {"TITLE": title}, source))

        if grading:
            shutil.copy2(template_file(GRADING_NAME), folder / GRADING_NAME)

        return Worksheet.load(folder)
