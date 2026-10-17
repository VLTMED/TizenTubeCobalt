#!/usr/bin/env python3
"""Small regression tests for the local Thmanyah font-header generator."""

import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("generate_thmanyah_font_header.py")
SPEC = importlib.util.spec_from_file_location("thmanyah_generator", SCRIPT)
GENERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GENERATOR)


class FontGeneratorTest(unittest.TestCase):
    def test_rejects_missing_otf(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ValueError):
                GENERATOR.build_css(Path(temp_dir))

    def test_rejects_non_otf_payload(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for relative_path, _, _ in GENERATOR.FONT_FACES:
                path = root / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"not an OTF")
            with self.assertRaises(ValueError):
                GENERATOR.build_css(root)

    def test_generated_header_splits_long_literals(self):
        css = "x" * 10000
        header = GENERATOR.build_header(css)
        self.assertLess(max(len(line) for line in header.splitlines()), 5000)
        self.assertEqual(header.count('R"THMANYAH_CSS('), (len(css) + 4095) // 4096)

    def test_css_maps_caption_and_open_type_features(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for relative_path, _, _ in GENERATOR.FONT_FACES:
                path = root / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"OTTOtest-font-data")
            css = GENERATOR.build_css(root)
            self.assertIn('"Thmanyah Sans"', css)
            self.assertIn('"Thmanyah Serif Text"', css)
            self.assertIn('"Thmanyah Serif Display"', css)
            self.assertIn('"liga" 1, "ss03" 1', css)
            self.assertIn('data-thmanyah-alternates="true"', css)
            self.assertEqual(css.count("@font-face"), len(GENERATOR.FONT_FACES))


if __name__ == "__main__":
    unittest.main()
