"""Tests for Knot_Library provenance layout (v0.2.1)."""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

import numpy as np

import sst_knotlib as sk
from sst_knotlib.formats import load_geometry
from sst_knotlib.inventory import classify_legacy_path, inventory_sources
from sst_knotlib.library_root import (
    find_knot_library_root,
    load_providers,
    load_source_json,
    resolve_path_provenance,
)

CORE = ["3_1", "4_1", "6_2", "7_4"]
EXPECTED_PROVIDERS = {
    "gilbert_ideal": "Ideal_Gilbert",
    "fremlin_fourier": "FourierSeries_Fremlin",
    "knotplot": "KnotPlot_Scharein",
    "ridgerunner": "Ridgerunner_Cantarella_Rawdon",
    "katlas": "KAtlas_BarNatan",
    "sst_generated": "SST_Generated",
}


class ProvenanceLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = find_knot_library_root()
        if cls.root is None:
            raise unittest.SkipTest("Knot_Library root not discoverable")

    def test_providers_json_ids(self):
        data = load_providers(self.root)
        self.assertEqual(data["schema"], "sst-knot-library-providers/1")
        for pid, directory in EXPECTED_PROVIDERS.items():
            self.assertIn(pid, data["providers"])
            self.assertEqual(data["providers"][pid]["directory"], directory)

    def test_source_json_schema(self):
        gilbert = load_source_json(self.root / "Sources" / "Ideal_Gilbert")
        fremlin = load_source_json(self.root / "Sources" / "FourierSeries_Fremlin")
        for src in (gilbert, fremlin):
            self.assertEqual(src["schema"], "sst-knot-library-source/1")
            for key in (
                "provider_id",
                "provider_name",
                "directory",
                "class",
                "construction_objective",
                "origin_paths",
                "copied",
                "moved",
            ):
                self.assertIn(key, src)
            self.assertFalse(src["moved"])
        self.assertEqual(gilbert["provider_id"], "gilbert_ideal")
        self.assertEqual(fremlin["provider_id"], "fremlin_fourier")
        self.assertNotEqual(
            gilbert["construction_objective"], fremlin["construction_objective"]
        )
        self.assertIn("SONO", gilbert["construction_objective"])
        self.assertIn("symmetric", fremlin["construction_objective"].lower())

    def test_library_root_discovery(self):
        self.assertTrue((self.root / "Sources").is_dir())
        self.assertTrue((self.root / "Registry" / "providers.json").is_file())
        env_key = "SST_KNOT_LIBRARY_ROOT"
        old = os.environ.get(env_key)
        try:
            os.environ[env_key] = str(self.root)
            self.assertEqual(find_knot_library_root(), self.root.resolve())
        finally:
            if old is None:
                os.environ.pop(env_key, None)
            else:
                os.environ[env_key] = old

    def test_record_uses_provider_id_not_path_heuristic(self):
        # Place a coordinate file under Ideal_Gilbert that looks like Fremlin fseries by name.
        with tempfile.TemporaryDirectory(dir=self.root / "Sources" / "Ideal_Gilbert") as td:
            path = Path(td) / "fake.fseries"
            # Use .txt so load_ascii works; still include fseries in path parts via parent name.
            d = Path(td) / "fseries_lookalike"
            d.mkdir()
            path = d / "coords.txt"
            np.savetxt(path, sk.classic_trefoil(32))
            a = load_geometry(path)
            self.assertEqual(a.provider_id, "gilbert_ideal")
            self.assertEqual(a.source_family, "gilbert_ideal")
            self.assertNotEqual(a.provider_id, "fremlin_fourier")

    def test_inventory_does_not_move(self):
        wb = self.root.parent
        with tempfile.TemporaryDirectory() as td:
            # Synthetic classification only (no write to Registry)
            ideal = classify_legacy_path(wb / "Ideal_Sources" / "Ideal.txt.gz", wb)
            self.assertEqual(ideal["provider_id"], "gilbert_ideal")
            fremlin = classify_legacy_path(
                wb / "Ideal_Fremlin_Fseries" / "fremlin" / "3_1" / "knot.3_1.fseries", wb
            )
            self.assertEqual(fremlin["provider_id"], "fremlin_fourier")
            finals = classify_legacy_path(
                wb / "KnotPlot" / "knots" / "final" / "knot_6.2_final.txt", wb
            )
            self.assertEqual(finals["provider_id"], "knotplot")
            self.assertEqual(finals["class"], "relaxed")
            self.assertIn("SST_Relaxation_Campaigns", finals["destination"])
            unknown = classify_legacy_path(Path(td) / "mystery_xyz.txt", wb)
            self.assertIsNone(unknown["provider_id"])
            self.assertEqual(unknown["destination"], "Quarantine/Unknown_Source")

            before = list((self.root / "Sources").rglob("*"))
            rep = inventory_sources(library_root=self.root, write=False)
            self.assertFalse(rep["moved"])
            self.assertEqual(rep["action"], "inventory_only")
            after = list((self.root / "Sources").rglob("*"))
            self.assertEqual(len(before), len(after))

    def test_copied_core_knots_present(self):
        for topo in CORE:
            g = self.root / "Sources" / "Ideal_Gilbert" / "extracted" / topo
            self.assertTrue(g.is_dir(), g)
            self.assertTrue(any(g.glob("*_AB.txt")), g)
            f = self.root / "Sources" / "FourierSeries_Fremlin" / "extracted" / topo
            self.assertTrue(f.is_dir(), f)
            self.assertTrue(any(f.iterdir()), f)

    def test_knotplot_finals_not_database_original(self):
        kp = load_source_json(self.root / "Sources" / "KnotPlot_Scharein")
        self.assertEqual(kp["provider_id"], "knotplot")
        campaigns = self.root / "Sources" / "KnotPlot_Scharein" / "SST_Relaxation_Campaigns"
        db = self.root / "Sources" / "KnotPlot_Scharein" / "Database_Original"
        self.assertTrue(any(campaigns.glob("*_final.txt")))
        # Database_Original must not hold the campaign finals
        self.assertFalse(any(db.glob("*_final.txt")))
        class_json = json.loads((campaigns / "CLASS.json").read_text(encoding="utf-8"))
        self.assertEqual(class_json["class"], "relaxed")
        sample = next(campaigns.glob("knot_*_final.txt"))
        prov = resolve_path_provenance(sample, self.root)
        self.assertEqual(prov["provider_id"], "knotplot")
        self.assertEqual(prov["class"], "relaxed")


if __name__ == "__main__":
    unittest.main(verbosity=2)
