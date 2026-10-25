#!/usr/bin/env python3
"""Unit tests for build_twist_knot_data.py."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_twist_knot_data import (  # noqa: E402
    build_entry,
    collect_inputs,
    entry_matches_filters,
    parse_a006_source_name,
    parse_xyz_components,
    resolve_name_metadata,
    write_javascript,
)

# ROOT = tools/catalog → Workbench root is parents[3]
A006_OUTPUT = (
    ROOT.parents[3]
    / "02_libraries"
    / "A_knot_libraries"
    / "A006_RoundFolded_Twist_Knot_Family"
    / "A006-v0.5.0"
    / "Output"
)
GEOMETRY = A006_OUTPUT / "v050" / "geometry"
SEEDS = A006_OUTPUT / "Seeds"
QUAL_XYZ = (
    A006_OUTPUT
    / "qualification_v050c"
    / "runs"
    / "AMECH_140_ELEC"
    / "i0000128.xyz"
)


class ParseA006NameTests(unittest.TestCase):
    def test_knot_stem(self):
        meta = parse_a006_source_name(Path("KNOT_3_1_N1024_ORIG.xyz"))
        self.assertEqual(meta["kind"], "KNOT")
        self.assertEqual(meta["topology"], "3_1")
        self.assertIsNone(meta["profile"])
        self.assertEqual(meta["resolutionN"], 1024)
        self.assertEqual(meta["chirality"], "ORIG")
        self.assertIsNone(meta["cpMode"])
        self.assertEqual(meta["canonical_id"], "KNOT_3_1_N1024_ORIG")

    def test_knot_11a_stem(self):
        meta = parse_a006_source_name(Path("KNOT_11a247_N0512_MIRROR.xyz"))
        self.assertEqual(meta["topology"], "11a247")
        self.assertEqual(meta["resolutionN"], 512)
        self.assertEqual(meta["chirality"], "MIRROR")

    def test_link_stem(self):
        meta = parse_a006_source_name(
            Path("LINK_5_5_6_BALANCED_N1024_ORIG_CPFIXED61.xyz")
        )
        self.assertEqual(meta["kind"], "LINK")
        self.assertEqual(meta["topology"], "5_5_6")
        self.assertEqual(meta["profile"], "BALANCED")
        self.assertEqual(meta["resolutionN"], 1024)
        self.assertEqual(meta["chirality"], "ORIG")
        self.assertEqual(meta["cpMode"], "CPFIXED61")

    def test_rejects_unknown(self):
        with self.assertRaises(ValueError):
            parse_a006_source_name(Path("Tlink_6_9_D1_040k.txt"))

    def test_seed_stem(self):
        meta = parse_a006_source_name(Path("3_1_N1024.xyz"))
        self.assertEqual(meta["kind"], "KNOT")
        self.assertEqual(meta["topology"], "3_1")
        self.assertEqual(meta["resolutionN"], 1024)
        self.assertEqual(meta["chirality"], "ORIG")
        self.assertIsNone(meta["profile"])
        self.assertIsNone(meta["cpMode"])
        self.assertEqual(meta["family"], "a006-seed")
        self.assertEqual(meta["canonical_id"], "3_1_N1024")
        self.assertEqual(meta["source_kind"], "seed")

    def test_seed_11a_stem(self):
        meta = parse_a006_source_name(Path("11a247_N2048.xyz"))
        self.assertEqual(meta["topology"], "11a247")
        self.assertEqual(meta["resolutionN"], 2048)
        self.assertEqual(meta["family"], "a006-seed")


class ResolveMetadataTests(unittest.TestCase):
    def test_override_unknown_stem(self):
        meta = resolve_name_metadata(
            Path("i0000128.xyz"),
            overrides={
                "kind": "LINK",
                "topology": "AMECH_140_ELEC",
                "chirality": "ORIG",
                "resolution_n": 1024,
            },
        )
        self.assertEqual(meta["kind"], "LINK")
        self.assertEqual(meta["topology"], "AMECH_140_ELEC")
        self.assertIsNone(meta["profile"])
        self.assertIsNone(meta["cpMode"])
        self.assertEqual(meta["resolutionN"], 1024)
        self.assertEqual(meta["family"], "a006-qualification")
        self.assertEqual(meta["source_kind"], "qualification")

    def test_override_requires_kind_topology(self):
        with self.assertRaises(ValueError):
            resolve_name_metadata(Path("i0000128.xyz"), overrides={"kind": "LINK"})


class ParseXyzComponentTests(unittest.TestCase):
    def test_component_header_split(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "qual.xyz"
            path.write_text(
                "\n".join(
                    [
                        "Component 0:",
                        "0 0 0",
                        "1 0 0",
                        "1 1 0",
                        "0 1 0",
                        "Component 1:",
                        "0 0 1",
                        "1 0 1",
                        "1 1 1",
                        "0 1 1",
                        "Component 2:",
                        "2 0 0",
                        "3 0 0",
                        "3 1 0",
                        "2 1 0",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            components = parse_xyz_components(path)
            self.assertEqual(len(components), 3)
            self.assertEqual(len(components[0]), 4)
            self.assertEqual(len(components[1]), 4)
            self.assertEqual(len(components[2]), 4)


class CollectInputsTests(unittest.TestCase):
    def test_multi_scan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = root / "a"
            b = root / "b"
            a.mkdir()
            b.mkdir()
            (a / "KNOT_3_1_N1024_ORIG.xyz").write_text("0 0 0\n", encoding="utf-8")
            (b / "3_1_N1024.xyz").write_text("0 0 0\n", encoding="utf-8")
            inputs = collect_inputs([], [a, b], "*.xyz")
            self.assertEqual(len(inputs), 2)


class FilterPredicateTests(unittest.TestCase):
    def setUp(self):
        self.knot = {
            "kind": "KNOT",
            "topology": "3_1",
            "profile": None,
            "resolutionN": 1024,
            "chirality": "ORIG",
            "cpMode": None,
        }
        self.link = {
            "kind": "LINK",
            "topology": "5_5_6",
            "profile": "BALANCED",
            "resolutionN": 1024,
            "chirality": "ORIG",
            "cpMode": "CPFIXED61",
        }
        self.seed = {
            "kind": "KNOT",
            "topology": "3_1",
            "profile": None,
            "resolutionN": 1024,
            "chirality": "ORIG",
            "cpMode": None,
        }
        self.qual = {
            "kind": "LINK",
            "topology": "AMECH_140_ELEC",
            "profile": None,
            "resolutionN": 1024,
            "chirality": "ORIG",
            "cpMode": None,
        }

    def test_default_knot_filters(self):
        self.assertTrue(
            entry_matches_filters(
                self.knot,
                kind="KNOT",
                profile="BALANCED",
                chirality="ORIG",
                resolution_n=1024,
                cp_mode="CPFIXED61",
            )
        )

    def test_chirality_reject(self):
        self.assertFalse(
            entry_matches_filters(self.knot, kind="KNOT", chirality="MIRROR", resolution_n=1024)
        )

    def test_link_profile_and_cp(self):
        self.assertTrue(
            entry_matches_filters(
                self.link,
                kind="LINK",
                profile="BALANCED",
                chirality="ORIG",
                resolution_n=1024,
                cp_mode="CPFIXED61",
            )
        )
        self.assertFalse(
            entry_matches_filters(
                self.link,
                kind="LINK",
                profile="TIGHT",
                chirality="ORIG",
                resolution_n=1024,
                cp_mode="CPFIXED61",
            )
        )
        self.assertFalse(
            entry_matches_filters(
                self.link,
                kind="LINK",
                profile="BALANCED",
                chirality="ORIG",
                resolution_n=1024,
                cp_mode="CPCENTER",
            )
        )

    def test_seed_matches_knot_filters(self):
        self.assertTrue(
            entry_matches_filters(
                self.seed,
                kind="KNOT",
                profile="BALANCED",
                chirality="ORIG",
                resolution_n=1024,
                cp_mode="CPFIXED61",
            )
        )

    def test_qual_requires_all_profile_and_cp(self):
        self.assertTrue(
            entry_matches_filters(
                self.qual,
                kind="LINK",
                profile="ALL",
                chirality="ORIG",
                resolution_n=1024,
                cp_mode="ALL",
            )
        )
        self.assertFalse(
            entry_matches_filters(
                self.qual,
                kind="LINK",
                profile="BALANCED",
                chirality="ORIG",
                resolution_n=1024,
                cp_mode="ALL",
            )
        )
        self.assertFalse(
            entry_matches_filters(
                self.qual,
                kind="LINK",
                profile="ALL",
                chirality="ORIG",
                resolution_n=1024,
                cp_mode="CPFIXED61",
            )
        )


@unittest.skipUnless(GEOMETRY.is_dir(), "A006 geometry directory not present")
class GeometryIntegrationTests(unittest.TestCase):
    def test_parse_and_build_n256_knot(self):
        path = GEOMETRY / "KNOT_3_1_N0256_ORIG.xyz"
        components = parse_xyz_components(path)
        self.assertEqual(len(components), 1)
        self.assertEqual(len(components[0]), 256)
        catalog_id, entry = build_entry(path, max_harmonic=None, linking_subdivisions=4)
        self.assertEqual(catalog_id, "KNOT_3_1_N0256_ORIG")
        self.assertEqual(entry["kind"], "KNOT")
        self.assertEqual(entry["resolutionN"], 256)
        self.assertIn("A006 RoundFolded Twist Knot Family", entry["source"])
        self.assertEqual(entry["sourceRole"], "a006-native-N256")
        self.assertIsNone(entry["D"])
        err = entry["diagnostics"]["fourier"]["maxNodeReconstructionError"]
        self.assertLess(err, 1e-9)
        coeffs = entry["components"][0]["coeffs"]
        self.assertEqual(coeffs[0]["I"], 0)
        self.assertEqual(len(coeffs[0]["A"]), 3)

    def test_js_emit_pretty_by_default_markers(self):
        path = GEOMETRY / "KNOT_3_1_N0256_ORIG.xyz"
        catalog_id, entry = build_entry(path, max_harmonic=8, linking_subdivisions=1)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "twist_knot_data.js"
            write_javascript(out, {catalog_id: entry}, compact=False)
            text = out.read_text(encoding="utf-8")
            self.assertIn("const TWIST_KNOT_IDS = ", text)
            self.assertIn("const TWIST_KNOT_DB = ", text)
            self.assertIn("window.TWIST_KNOT_DB", text)
            self.assertIn('\n  "' + catalog_id + '"', text)
            self.assertIn("\n  \"" + catalog_id + "\": {", text)
            marker = "const TWIST_KNOT_DB = "
            payload = text[text.find(marker) + len(marker) :]
            database, _ = json.JSONDecoder().raw_decode(payload.lstrip())
            self.assertIn(catalog_id, database)
            self.assertEqual(database[catalog_id]["sourceRole"], "a006-native-N256")


@unittest.skipUnless(SEEDS.is_dir(), "A006 Seeds directory not present")
class SeedsIntegrationTests(unittest.TestCase):
    def test_build_seed_entry(self):
        path = SEEDS / "3_1_N1024.xyz"
        catalog_id, entry = build_entry(path, max_harmonic=8, linking_subdivisions=1)
        self.assertEqual(catalog_id, "3_1_N1024")
        self.assertEqual(entry["kind"], "KNOT")
        self.assertEqual(entry["family"], "a006-seed")
        self.assertEqual(entry["chirality"], "ORIG")
        self.assertEqual(entry["sourceRole"], "a006-seed-N1024")
        self.assertIn("Seeds", entry["source"])


@unittest.skipUnless(QUAL_XYZ.is_file(), "A006 qualification XYZ not present")
class QualificationIntegrationTests(unittest.TestCase):
    def test_build_qual_entry(self):
        components = parse_xyz_components(QUAL_XYZ)
        self.assertEqual(len(components), 3)
        catalog_id, entry = build_entry(
            QUAL_XYZ,
            max_harmonic=8,
            linking_subdivisions=1,
            id_override="QUAL_AMECH_140_ELEC_i0000128",
            overrides={
                "kind": "LINK",
                "topology": "AMECH_140_ELEC",
                "chirality": "ORIG",
            },
        )
        self.assertEqual(catalog_id, "QUAL_AMECH_140_ELEC_i0000128")
        self.assertEqual(entry["kind"], "LINK")
        self.assertEqual(entry["componentCount"], 3)
        self.assertIsNone(entry["profile"])
        self.assertIsNone(entry["cpMode"])
        self.assertEqual(entry["resolutionN"], min(len(c) for c in components))
        self.assertEqual(entry["family"], "a006-qualification")
        self.assertIn("qualification", entry["sourceRole"])


if __name__ == "__main__":
    unittest.main()
