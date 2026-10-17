# Arabic TV typography: optional Thmanyah font integration

This change adds an **opt-in local build path** for testing the original Thmanyah
OTF family in TizenTube Cobalt. It does not add font binaries, converted WOFF2
files, or generated font data to this public repository. The feature is off by
default, so existing builds and UI behavior are unchanged unless explicitly enabled.

## Intended typography on a television

- **Thmanyah Sans** is the default for menus, buttons, navigation, metadata, and
  other interface text. Its low contrast and simple forms are the most suitable
  starting point for a TV viewed from a distance.
- **Thmanyah Serif Display** is reserved for primary headings and recognizable
  video-title treatments; it is not applied to every menu label.
- **Thmanyah Serif Text** is used for longer video descriptions, where its text
  design is more appropriate than the display face.
- **Embedded captions/subtitles** use Sans Medium (weight 500). The integration
  deliberately leaves player-managed font size, position, outline, background,
  line spacing, and shadow untouched. This preserves existing TV caption
  controls and contrast rather than hard-coding a one-size-fits-all subtitle.

The global typography rule excludes common icon-font classes and SVG content.
Arabic direction and bidi behavior are not forced, because the page/player is
responsible for mixed Arabic, Latin, and numeric runs.

## OpenType choices

- **liga** is enabled for captions to retain the family's standard ligature
  behavior, which includes the documented slanted-kashida treatment where the
  font's shaping rules call for it. Do not insert tatweel characters (ـ)
  into arbitrary words to imitate the feature.
- The supplied Sans OTF's GSUB metadata labels **ss03** as **fatha-ar 01**. The
  integration enables that stylistic set for captions only so vowel marks can
  use the corresponding drawing where present. It does not assume that subtitles
  contain full Arabic diacritics.
- **salt** (Stylistic Alternates / alternate letterforms) is **not enabled
  globally**. It is opt-in on elements marked **data-thmanyah-alternates="true"**,
  so it can be reserved for a small number of suitable headings instead of
  decorating every adjacent word.
- The font files are read as supplied OTF data. This generator does not convert,
  rename, or rewrite them. The supplied WOFF2 copies are intentionally ignored.

## Local setup

1. Obtain the font package from the official source and review its current
   license. Keep the original directory structure and file names.
2. Copy the original **thmanyah typeface** directory to
   **third_party/thmanyah-local-fonts/thmanyah typeface/**. This path is ignored
   by Git so the font files are not committed accidentally.
3. Before enabling embedding or distributing an APK, confirm that the current
   license permits embedding the fonts into this Android/TV app and distributing
   the resulting application. The official FAQ currently says the font is
   intended for Windows/macOS and does not support Android, and the license
   prohibits redistributing or hosting the font files. Do not upload the font,
   a generated header, or an APK containing it to public CI artifacts unless
   the rights holder has explicitly confirmed that this use is permitted.
4. Configure GN with **enable_thmanyah_fonts=true** only for an authorized local
   build. The GN action generates **thmanyah_font_data.h** under the build output
   directory from the local OTF files; it is not tracked in the source tree.

For reference, the rights holder's current terms and font-design guidance are
published at:

- https://ask.thmanyah.com/en/thmanyah-line-for-everyone
- https://font.thmanyah.com/

The default value for **enable_thmanyah_fonts** is **false**. The feature is
deliberately opt-in rather than downloading or bundling font files automatically.
