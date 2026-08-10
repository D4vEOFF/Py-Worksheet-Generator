#!/usr/bin/env python3
"""WorkSheet Generator -- entry point of the wsg command.

Usage: wsg <command> [options]   (run "wsg --help" for the list of commands)
"""

import sys
from pathlib import Path

if sys.version_info < (3, 8):  # pragma: no cover
    sys.exit("wsg needs Python 3.8 or newer")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from wsgen.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
