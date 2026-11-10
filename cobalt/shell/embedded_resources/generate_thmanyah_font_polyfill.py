#!/usr/bin/env python3
"""Generate a JavaScript polyfill with an embedded WOFF2 data URI."""

import base64
from pathlib import Path
import sys


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit(
            "usage: generate_thmanyah_font_polyfill.py "
            "<template.js> <font.woff2> <output.js>"
        )

    template_path, font_path, output_path = map(Path, sys.argv[1:])
    template = template_path.read_text(encoding="utf-8")
    font = font_path.read_bytes()
    marker = "__THMANYAH_FONT_BASE64__"

    if font[:4] != b"wOF2":
        raise SystemExit(f"{font_path} does not have a valid WOFF2 signature")
    if template.count(marker) != 1:
        raise SystemExit(f"{template_path} must contain exactly one {marker}")

    encoded = base64.b64encode(font).decode("ascii")
    output = template.replace(marker, encoded)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as output_file:
        output_file.write(output)


if __name__ == "__main__":
    main()
