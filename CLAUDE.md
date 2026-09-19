# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`wsg` (WorkSheet Generator) is a CLI that turns folders of LaTeX tasks into printable worksheets. Every worksheet is typeset twice: as an assignment sheet for students and, optionally, as a solution sheet for the teacher.

Python 3.8+, **standard library only** — there is no `pip install`, no `requirements.txt`, no packaging metadata. Keep it that way; a new third-party import would break the install scripts, which only look for a Python interpreter.

There is **no test suite and no linter configured**. Verification is done by building a real project (see below).

## Running and verifying changes

The repo is not installed as a package. Run it straight from the checkout:

```bash
python wsg.py --help
```

Manual end-to-end check after touching the builder, the template or the header — requires `pdflatex` (`latexmk` is used when present):

```bash
python wsg.py new "Test" --dir /tmp/wsg-test && cd /tmp/wsg-test && python <repo>/wsg.py add "Sheet" && python <repo>/wsg.py build --keep-aux -v
```

`--keep-aux` leaves `wsg-build/` in place (it is normally deleted on success) and `-v` streams the LaTeX output. On a failed compile the auxiliary files are kept automatically and the log path is printed.

Installation (`install.ps1` / `install.sh`) only sets `WSG_HOME` to the repo folder and writes a `wsg` launcher that calls `python "$WSG_HOME/wsg.py"` — it does not copy the code, so an installed `wsg` runs the working tree directly.

## Architecture

Pipeline for one worksheet, `cli.py` → `project.py` → `builder.py` → `template.py` → `latex.py`:

1. **`project.py`** — the on-disk model. A *project* is a folder with `config.txt`; a *worksheet* is a subfolder named `<number>-<slug>` that also has a `config.txt`. `Project.find()` walks up from the cwd; `_looks_like_project()` disambiguates the two (a worksheet folder matches `NN-name` and contains no numbered children). `Project.file_path()` implements the override chain for `header`/`packages`/`macros`: CLI flag → worksheet config → project config → the copy in the installation root, searched against cwd, the worksheet folder, the project root, then `INSTALL_ROOT`.
2. **`builder.py`** — assembles the placeholder values and drives the two variants (assignment, solution). It writes the generated `.tex` into `<worksheet>/wsg-build/` but compiles **with the working directory set to the worksheet folder**, so relative paths inside tasks (images) resolve as the author expects and LaTeX errors point at the real `tasks.tex` line. `default-packages.tex` and `default-macros.tex` go through placeholder substitution too (they need `<<LANGUAGE>>` and `<<PAPER>>`) and are written into `wsg-build/` as `wsg-packages.tex` / `wsg-macros.tex`, then pulled in via `\input`.
3. **`template.py`** — `<<NAME>>` substitution (an unknown placeholder is a hard error, listing the known ones) plus conversion of `grading.txt` into a `\wsgGradingTable` call.
4. **`latex.py`** — prefers `latexmk -pdf`, otherwise runs `pdflatex` **three times**; the point total and the difficulty legend are written to the `.aux` file and only appear on a later pass. `read_page_count()` reads the log twice, the second time with newlines stripped, because TeX hard-wraps the `Output written on ...` line.

`WsgError` (defined in `wsgen/__init__.py`) is the one exception class turned into a `[wsg] error: ...` message and exit code 1 by `main()`; anything else propagates as a traceback. Raise it for every user-facing failure.

### Where behaviour lives

The Python side knows nothing about how a worksheet *looks*. `task`, `solution`, the `reminder` / `note` / `results` boxes, the answer-space commands, the page style and the localised labels are all defined in **`default-header.tex`**; the generator only fills placeholders. The results box turns every `enumerate` inside it into enumitem's inline `enumerate*`, which is why `default-packages.tex` loads enumitem with `inline`. Adding a task option (e.g. a new `answer=` mode) is a header change, not a Python change. Conversely, adding a new placeholder means adding it to `_placeholder_values()` in `builder.py` *and* to the header — a placeholder used in the header but missing from the dict raises at build time.

`default-macros.tex` deliberately holds only mathematical notation (mirroring the [AM-skripta](https://github.com/D4vEOFF/AM-skripta) macros so tasks can be pasted over unchanged); nothing about layout belongs there.

`templates/` holds the files copied into new projects (`project-config.txt`, `worksheet-config.txt`, `tasks.tex`, `grading.txt`) plus `a5-imposition.tex`, used by `--a5` to place each A5 page twice on an A4 sheet via `pdfpages`.

The three `default-*.tex` files in the repo root are the *installation* copies: `wsg new` copies them into the project, and from then on the project's own copies are what a build uses.

## Conventions

- Code, comments and docstrings are English; user-facing text in the README, the config templates and the sample `tasks.tex` is Czech. The generated worksheets support `czech` and `english` (`language` key in the project config) — both label sets live in `default-header.tex`.
- Config values reach LaTeX verbatim so authors can use markup in them; only `%`, `&` and `#` are escaped, by `util.sanitise_latex()`.
- `write_text()` always writes UTF-8 with `\n` newlines and `read_text()` reads `utf-8-sig` — keep going through them rather than `Path.read_text`/`write_text` so BOMs and CRLF stay handled.
- Booleans in config files accept Czech `ano`/`ne` alongside `yes`/`no` (`config.as_bool`).

## Note

An OpenAI Codex config was found at `~/.codex/config.toml`. Reply `/import` to scan it and list what is importable (MCP servers, slash commands, subagents, skills, instructions), then `/import --yes=<digest>` with the digest from the scan output to apply the user-level items. If `/import` is unavailable on this surface, run `claude import` from a terminal.
