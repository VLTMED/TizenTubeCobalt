#!/usr/bin/env python3
# Generates embedded font CSS from the original, tracked Thmanyah OTF assets.

import argparse
import base64
from pathlib import Path
import sys

# Keep the TV bundle small and map only the weights used by the interface.
FONT_FACES = (
    ("thmanyahsans/otf/thmanyahsans-Regular.otf", "Thmanyah Sans", 400),
    ("thmanyahsans/otf/thmanyahsans-Medium.otf", "Thmanyah Sans", 500),
    ("thmanyahsans/otf/thmanyahsans-Bold.otf", "Thmanyah Sans", 700),
    ("thmanyahseriftext/otf/thmanyahseriftext-Regular.otf", "Thmanyah Serif Text", 400),
    ("thmanyahserifdisplay/otf/thmanyahserifdisplay-Bold.otf", "Thmanyah Serif Display", 700),
)


def build_css(font_root: Path) -> str:
    css = ["/* Embedded original OTF assets; see third_party/thmanyah-fonts/NOTICE.md. */"]
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

    # Preserve player controls and icon fonts; do not impose bidi, size, or layout.
    css.append(
        ':where(html, body, body *:not(svg):not(svg *):not(yt-icon)'
        ':not(yt-icon *):not(ytlr-icon):not(ytlr-icon *):not(.ytp-icon)'
        ':not(.ytp-icon *):not(.material-icons):not(.material-icons *)'
        ':not(.material-symbols-outlined):not(.material-symbols-outlined *)'
        ':not([class*="icon"]):not([class*="icon"] *)'
        ':not([class*="Icon"]):not([class*="Icon"] *)) {'
        'font-family: "Thmanyah Sans", Arial, sans-serif !important;'
        'font-feature-settings: "liga" 0;'
        "font-kerning: normal;"
        "font-synthesis: none;"
        "}"
    )
    css.append(
        'h1, h2, [role="heading"][aria-level="1"], ytlr-video-title,'
        '[class*="video-title"], [class*="videoTitle"] {'
        'font-family: "Thmanyah Serif Display", "Thmanyah Sans", Arial, sans-serif !important;'
        "font-weight: 700 !important;"
        'font-feature-settings: "liga" 0 !important;'
        "}"
    )
    css.append(
        '#description, .description, ytlr-description, [class~="description"] {'
        'font-family: "Thmanyah Serif Text", "Thmanyah Sans", Arial, sans-serif !important;'
        "font-weight: 400 !important;"
        'font-feature-settings: "liga" 0 !important;'
        "}"
    )
    css.append(
        '.ytp-caption-segment, .ytp-caption-window-container,'
        '.ytp-caption-window-container *, .caption-window, .captions-text,'
        'ytlr-caption, ytlr-caption *, video::cue {'
        'font-family: "Thmanyah Sans", Arial, sans-serif !important;'
        "font-weight: 500 !important;"
        # SS03 is named "fatha-ar 01" in the supplied Sans OTF metadata.
        # The guide reserves slanted-kashida styling for carefully edited text;
        # dynamic captions therefore keep that ligature feature off.
        'font-feature-settings: "liga" 0, "ss03" 1 !important;'
        "}"
    )
    css.append(
        # Arabic stylistic alternates remain opt-in; never decorate every word.
        '[data-thmanyah-alternates="true"] {'
        'font-feature-settings: "liga" 0, "salt" 1 !important;'
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
        "// Generated file. Do not check in; font asset notice is in third_party/thmanyah-fonts/NOTICE.md.\n"
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
    print(f"Generated embedded font header: {args.output} ({len(header)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
