#!/usr/bin/env python3
# Generates a local-only font data header from original Thmanyah OTF files.
# Font files are deliberately not stored in this public repository.

import argparse
import base64
from pathlib import Path
import sys

FONT_FACES = (
    ("thmanyahsans/otf/thmanyahsans-Light.otf", "Thmanyah Sans", 300),
    ("thmanyahsans/otf/thmanyahsans-Regular.otf", "Thmanyah Sans", 400),
    ("thmanyahsans/otf/thmanyahsans-Medium.otf", "Thmanyah Sans", 500),
    ("thmanyahsans/otf/thmanyahsans-Bold.otf", "Thmanyah Sans", 700),
    ("thmanyahsans/otf/thmanyahsans-Black.otf", "Thmanyah Sans", 900),
    ("thmanyahseriftext/otf/thmanyahseriftext-Light.otf", "Thmanyah Serif Text", 300),
    ("thmanyahseriftext/otf/thmanyahseriftext-Regular.otf", "Thmanyah Serif Text", 400),
    ("thmanyahseriftext/otf/thmanyahseriftext-Medium.otf", "Thmanyah Serif Text", 500),
    ("thmanyahseriftext/otf/thmanyahseriftext-Bold.otf", "Thmanyah Serif Text", 700),
    ("thmanyahseriftext/otf/thmanyahseriftext-Black.otf", "Thmanyah Serif Text", 900),
    ("thmanyahserifdisplay/otf/thmanyahserifdisplay-Light.otf", "Thmanyah Serif Display", 300),
    ("thmanyahserifdisplay/otf/thmanyahserifdisplay-Regular.otf", "Thmanyah Serif Display", 400),
    ("thmanyahserifdisplay/otf/thmanyahserifdisplay-Medium.otf", "Thmanyah Serif Display", 500),
    ("thmanyahserifdisplay/otf/thmanyahserifdisplay-Bold.otf", "Thmanyah Serif Display", 700),
    ("thmanyahserifdisplay/otf/thmanyahserifdisplay-Black.otf", "Thmanyah Serif Display", 900),
)


def build_css(font_root: Path) -> str:
    css = ["/* Original OTF bytes; generated locally and never checked in. */"]
    for relative_path, family, weight in FONT_FACES:
        path = font_root / relative_path
        try:
            font_bytes = path.read_bytes()
        except OSError as error:
            raise ValueError(f"Required OTF is missing or unreadable: {path}") from error
        if not font_bytes.startswith(b"OTTO"):
            raise ValueError(f"Expected an original OpenType/CFF OTF file: {path}")
        encoded = base64.b64encode(font_bytes).decode("ascii")
        css.append(
            "@font-face {"
            f'font-family: "{family}";'
            "font-style: normal;"
            f"font-weight: {weight};"
            "font-display: swap;"
            f'src: url("data:font/otf;base64,{encoded}") format("opentype");'
            "}"
        )

    css.append(
        ':where(html, body, body *:not(svg):not(svg *):not(yt-icon)'
        ':not(yt-icon *):not(ytlr-icon):not(ytlr-icon *):not(.ytp-icon)'
        ':not(.ytp-icon *):not(.material-icons):not(.material-icons *)'
        ':not(.material-symbols-outlined):not(.material-symbols-outlined *)'
        ':not([class*="icon"]):not([class*="icon"] *)'
        ':not([class*="Icon"]):not([class*="Icon"] *)) {'
        'font-family: "Thmanyah Sans", Arial, sans-serif !important;'
        "font-kerning: normal;"
        "}"
    )
    css.append(
        'h1, h2, [role="heading"][aria-level="1"], ytlr-video-title,'
        '[class*="video-title"], [class*="videoTitle"] {'
        'font-family: "Thmanyah Serif Display", "Thmanyah Sans", Arial, sans-serif !important;'
        "font-weight: 700 !important;"
        "}"
    )
    css.append(
        '[class*="description"], [class*="Description"], #description, .description {'
        'font-family: "Thmanyah Serif Text", "Thmanyah Sans", Arial, sans-serif !important;'
        "font-weight: 400 !important;"
        "}"
    )
    css.append(
        '.ytp-caption-segment, .ytp-caption-window-container,'
        '.ytp-caption-window-container *, .caption-window, .captions-text,'
        'ytlr-caption, [class*="caption"], [class*="subtitle"],'
        '[class*="Caption"], [class*="Subtitle"] {'
        'font-family: "Thmanyah Sans", Arial, sans-serif !important;'
        "font-weight: 500 !important;"
        # The supplied Sans OTF names ss03 "fatha-ar 01".
        # liga enables the family's supported slanted-kashida ligatures.
        'font-feature-settings: "liga" 1, "ss03" 1 !important;'
        "}"
    )
    css.append(
        '[data-thmanyah-alternates="true"] {'
        'font-feature-settings: "salt" 1 !important;'
        "}"
    )
    return "\n".join(css)


def build_header(css: str) -> str:
    delimiter = "THMANYAH_CSS"
    if f"){delimiter}\"" in css:
        raise ValueError("Unexpected raw-string delimiter collision.")

    # Keep each physical C++ source line well below compiler translation
    # limits while adjacent raw string literals preserve the CSS byte-for-byte.
    literals = "\n".join(
        f'R"{delimiter}({css[offset:offset + 4096]}){delimiter}"'
        for offset in range(0, len(css), 4096)
    )
    return (
        "// Generated file. Do not check in or redistribute.\n"
        "#ifndef COBALT_RENDERER_THMANYAH_FONT_DATA_H_\n"
        "#define COBALT_RENDERER_THMANYAH_FONT_DATA_H_\n\n"
        "namespace cobalt {\n"
        "namespace thmanyah_font {\n"
        "inline constexpr char kCss[] =\n"
        f"{literals};\n"
        "}  // namespace thmanyah_font\n"
        "}  // namespace cobalt\n\n"
        "#endif  // COBALT_RENDERER_THMANYAH_FONT_DATA_H_\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--font-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        css = build_css(args.font_root)
        header = build_header(css)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(header, encoding="utf-8", newline="\n")
    print(f"Generated local font header: {args.output} ({len(header)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
