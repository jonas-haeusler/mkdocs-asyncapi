#!/usr/bin/env python3
"""Converts rem units to px in the vendored AsyncAPI CSS.

Themes like mkdocs-material scale the document root's font-size (e.g. to 125-150%)
and only reset it back down inside their own typography scope. Since `rem` always
resolves against the true document root - regardless of shadow DOM boundaries -
that inflates every rem-based rule in the vendored CSS. Baking in Tailwind's default
1rem=16px assumption makes component sizing immune to whatever the host page does.
"""

import re
import sys
from pathlib import Path

REM_BASE_PX = 16
REM_PATTERN = re.compile(r"(-?)(\d*\.\d+|\d+)rem")


def convert(css: str) -> str:
    def replace(match: re.Match) -> str:
        sign, number = match.groups()
        px = float(number) * REM_BASE_PX
        if sign == "-":
            px = -px
        px_str = f"{px:.4f}".rstrip("0").rstrip(".")
        return f"{px_str}px"

    return REM_PATTERN.sub(replace, css)


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(f"usage: {Path(sys.argv[0]).name} <css-file>")
    path = Path(sys.argv[1])
    path.write_text(convert(path.read_text(encoding="utf-8")), encoding="utf-8")


if __name__ == "__main__":
    main()
