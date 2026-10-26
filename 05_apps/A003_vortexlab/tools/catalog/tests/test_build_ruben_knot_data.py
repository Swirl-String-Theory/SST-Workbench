#!/usr/bin/env python3
"""Unit tests for build_ruben_knot_data.py."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_ruben_knot_data import (  # noqa: E402
    DEFAULT_E010,
    b0_from_token,
    build_entry,
    entry_matches_filters,
    parse_ruben_stem,
    write_javascript,
)

E010 = DEFAULT_E010
SAMPLE_XYZ = E010 / "seeds" / "T_2_3" / "T_2_3_B0800_N512.xyz"
SAMPLE_EPS = E010 / "seeds_perturbed" / "T_2_3" / "T_2_3_B0800_N512_eps01.xyz"
FAMILY_INDEX = E010 / "FAMILY_INDEX.json"


class ParseStemTests(unittest.TestCase):
    def test_baseline_stem(self):
        meta = parse_ruben_stem("T_2_3_B0800_N512")
        self.assertEqual(meta["canonical_id"], "RUBEN_T_2_3_B0800_N512")
        self.assertEqual(meta["parametricEmbedding"], "T_2_3")
        self.assertEqual(meta["variant"], "baseline")
        self.assertEqual(meta["resolutionN"], 512)
        self.assertAlmostEqual(meta["B0"], 0.08)

    def test_perturbed_stem(self):
        meta = parse_ruben_stem("T_5_4_B2000_N512_eps01")
        self.assertEqual(meta["canonical_id"], "RUBEN_T_5_4_B2000_N512_eps01")
        self.assertEqual(meta["variant"], "perturbed")
        self.assertAlmostEqual(meta["B0"], 0.2)

    def test_rejects_unknown(self):
        with self.assertRaises(ValueError):
            parse_ruben_stem("KNOT_3_1_N1024_ORIG")

    def test_b0_token(self):
        self.assertAlmostEqual(b0_from_token("0800"), 0.08)
        self.assertAlmostEqual(b0_from_token("1000"), 0.1)
        self.assertAlmostEqual(b0_from_token("2000"), 0.2)


class FilterTests(unittest.TestCase):
    def setUp(self):
        self.entry = {
            "parametricEmbedding": "T_2_3",
            "B0": 0.08,
            "variant": "baseline",
        }

    def test_default_match(self):
        self.assertTrue(
            entry_matches_filters(
                self.entry, embedding="T_2_3", b0=0.08, variant="baseline"
            )
        )

    def test_variant_reject(self):
        self.assertFalse(
            entry_matches_filters(self.entry, variant="perturbed")
        )

    def test_embedding_all(self):
        self.assertTrue(entry_matches_filters(self.entry, embedding="ALL"))


@unittest.skipUnless(SAMPLE_XYZ.is_file(), "E010 sample XYZ not present")
class BuildIntegrationTests(unittest.TestCase):
    def test_build_baseline(self):
        family = {}
        if FAMILY_INDEX.is_file():
            from build_ruben_knot_data import load_family_index

            family = load_family_index(FAMILY_INDEX)
        catalog_id, entry = build_entry(
            SAMPLE_XYZ,
            max_harmonic=8,
            linking_subdivisions=1,
            family_by_seed=family,
            outputs_root=E010,
        )
        self.assertEqual(catalog_id, "RUBEN_T_2_3_B0800_N512")
        self.assertEqual(entry["kind"], "KNOT")
        self.assertEqual(entry["family"], "ruban-torus")
        self.assertEqual(entry["variant"], "baseline")
        self.assertEqual(entry["resolutionN"], 512)
        self.assertEqual(entry["parametricEmbedding"], "T_2_3")
        self.assertEqual(entry["topology"], "3_1")
        self.assertFalse(entry["ideal"])
        self.assertEqual(entry["componentCount"], 1)
        err = entry["diagnostics"]["fourier"]["maxNodeReconstructionError"]
        self.assertLess(err, 1e-9)

    @unittest.skipUnless(SAMPLE_EPS.is_file(), "E010 perturbed XYZ not present")
    def test_build_perturbed(self):
        catalog_id, entry = build_entry(
            SAMPLE_EPS,
            max_harmonic=8,
            linking_subdivisions=1,
            outputs_root=E010,
        )
        self.assertEqual(catalog_id, "RUBEN_T_2_3_B0800_N512_eps01")
        self.assertEqual(entry["variant"], "perturbed")

    def test_js_emit(self):
        catalog_id, entry = build_entry(
            SAMPLE_XYZ, max_harmonic=4, linking_subdivisions=1
        )
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "ruben_knot_data.js"
            write_javascript(out, {catalog_id: entry}, compact=False)
            text = out.read_text(encoding="utf-8")
            self.assertIn("const RUBEN_KNOT_IDS = ", text)
            self.assertIn("const RUBEN_KNOT_DB = ", text)
            self.assertIn("window.RUBEN_KNOT_DB", text)
            marker = "const RUBEN_KNOT_DB = "
            payload = text[text.find(marker) + len(marker) :]
            database, _ = json.JSONDecoder().raw_decode(payload.lstrip())
            self.assertIn(catalog_id, database)


if __name__ == "__main__":
    unittest.main()
