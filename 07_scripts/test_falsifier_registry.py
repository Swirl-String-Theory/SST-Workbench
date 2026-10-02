"""Tests for falsifier_registry.py (schema v1 legacy + schema v2 root)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from falsifier_registry import (  # noqa: E402
    FAMILIES,
    LEGACY_REGISTRY,
    NUMERICS_STATUSES,
    PHYSICS_STATUSES,
    WB,
    discover_unregistered,
    entries_source_path,
    is_registry_v2,
    load_entries,
    load_registry,
    parse_version,
    reset_pack_index,
    resolve_pack,
    validate_registry,
)

REGISTRY = WB / "falsifier_registry.yaml"
A_FALSIFIERS = WB / "01_research" / "A_falsifiers"


class TestParseVersion(unittest.TestCase):
    def test_semver(self) -> None:
        self.assertEqual(parse_version("SST_Phase_Feedback_v0.2.1"), (0, 2, 1))

    def test_underscore_routeb(self) -> None:
        self.assertEqual(parse_version("SST_routeB_RT_bem_research_v3_1"), (3, 1))

    def test_alpha_suffix(self) -> None:
        self.assertEqual(
            parse_version("SST_ideal_links_comprehensive_test_suite_v0.4.0-alpha.1"),
            (0, 4, 0),
        )


class TestValidateRegistryV2(unittest.TestCase):
    def test_live_registry_valid(self) -> None:
        errs = validate_registry(path=REGISTRY)
        self.assertEqual(errs, [], msg="\n".join(errs))

    def test_root_is_schema_v2(self) -> None:
        data = load_registry(REGISTRY)
        self.assertTrue(is_registry_v2(data))
        self.assertEqual(str(data.get("schema_version")), "2.0")

    def test_unique_catalog_ids(self) -> None:
        data = load_registry(REGISTRY)
        ids = [e["catalog_id"] for e in data["families"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_physical_ids_match_registry(self) -> None:
        data = load_registry(REGISTRY)
        reg_ids = sorted(e["catalog_id"] for e in data["families"])
        physical = sorted(
            p.name.split("_", 1)[0]
            for p in A_FALSIFIERS.iterdir()
            if p.is_dir() and p.name.startswith("A") and (p / "FAMILY.yaml").is_file()
        )
        self.assertEqual(reg_ids, physical)

    def test_no_stars_or_emoji_as_canonical_evidence(self) -> None:
        data = load_registry(REGISTRY)
        for fam in data["families"]:
            self.assertNotIn("stars", fam)
            self.assertNotIn("physics_emoji", fam)

    def test_repro_gate_pass_is_not_physics_pass(self) -> None:
        data = load_registry(REGISTRY)
        for fam in data["families"]:
            rg = fam.get("repro_gate") or {}
            sci = fam.get("scientific") or {}
            if str(rg.get("status", "")).lower() != "pass":
                continue
            overall = str(sci.get("overall") or "").upper()
            self.assertNotEqual(
                overall,
                "PASS",
                msg=f"{fam.get('catalog_id')}: repro_gate pass must not imply scientific PASS",
            )


class TestLegacyEntries(unittest.TestCase):
    """v1 pack_glob / physics_status rows live in the archived legacy registry."""

    @classmethod
    def setUpClass(cls) -> None:
        if not LEGACY_REGISTRY.is_file():
            raise unittest.SkipTest(f"legacy archive missing: {LEGACY_REGISTRY}")

    def test_entries_source_redirects_to_legacy(self) -> None:
        self.assertEqual(entries_source_path(REGISTRY), LEGACY_REGISTRY)

    def test_legacy_valid(self) -> None:
        errs = validate_registry(path=LEGACY_REGISTRY)
        self.assertEqual(errs, [], msg="\n".join(errs))

    def test_all_families_present(self) -> None:
        data = load_registry(LEGACY_REGISTRY)
        fams = {e["family"] for e in data["entries"]}
        self.assertEqual(fams, FAMILIES)

    def test_unique_ids(self) -> None:
        data = load_registry(LEGACY_REGISTRY)
        ids = [e["id"] for e in data["entries"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_physics_numerics_enums(self) -> None:
        data = load_registry(LEGACY_REGISTRY)
        for e in data["entries"]:
            self.assertIn(e["physics_status"], PHYSICS_STATUSES)
            self.assertIn(e["numerics_status"], NUMERICS_STATUSES)

    def test_entry_count_near_45(self) -> None:
        data = load_registry(LEGACY_REGISTRY)
        self.assertGreaterEqual(len(data["entries"]), 43)
        self.assertLessEqual(len(data["entries"]), 50)


class TestResolvePack(unittest.TestCase):
    def setUp(self) -> None:
        reset_pack_index()

    def test_phase_feedback_resolves_v021_or_latest(self) -> None:
        reset_pack_index()
        resolved = resolve_pack("SST_Phase_Feedback_Delay*")
        self.assertIsNotNone(resolved)
        assert resolved is not None
        self.assertGreaterEqual(resolved.version, (0, 2, 0))

    def test_physics_and_numerics_independent_fields(self) -> None:
        if not LEGACY_REGISTRY.is_file():
            self.skipTest("legacy archive missing")
        entries = load_entries(REGISTRY)
        for e in entries:
            if e.numerics_status == "PASS" and e.physics_status == "PASS":
                continue
            if e.numerics_status == "PASS":
                self.assertIn(
                    e.physics_status,
                    {"INDETERMINATE", "UNTESTED", "FAIL", "REFERENCE_ONLY"},
                    msg=e.id,
                )

    def test_at_least_40_entries(self) -> None:
        if not LEGACY_REGISTRY.is_file():
            self.skipTest("legacy archive missing")
        entries = load_entries(REGISTRY)
        self.assertGreaterEqual(len(entries), 40)

    def test_most_entries_resolve(self) -> None:
        if not LEGACY_REGISTRY.is_file():
            self.skipTest("legacy archive missing")
        entries = load_entries(REGISTRY)
        unresolved = [e.id for e in entries if e.resolved is None]
        self.assertLessEqual(len(unresolved), 2, msg=str(unresolved))

    def test_legacy_glob_matches_short_version_directory(self) -> None:
        resolved = resolve_pack("SST_routeB_RT_bem_research_v3")
        self.assertIsNotNone(resolved)
        assert resolved is not None
        self.assertIn("B004", resolved.working_tree or "")


class TestDiscoverUnregistered(unittest.TestCase):
    def setUp(self) -> None:
        reset_pack_index()

    def test_discover_returns_list(self) -> None:
        if not LEGACY_REGISTRY.is_file():
            self.skipTest("legacy archive missing")
        entries = load_entries(REGISTRY, resolve=False)
        gaps = discover_unregistered(entries)
        self.assertIsInstance(gaps, list)


class TestJunctionPruning(unittest.TestCase):
    """Pack discovery must not descend into SP02 compatibility junctions.

    ~50 junctions sit at the repo root, each pointing back into the catalog. A walk
    that follows them re-scans the whole tree once per junction; discovery went from
    under a second to ten minutes before this was pruned.
    """

    def test_walk_pruned_skips_junctions(self):
        import os
        import subprocess

        from falsifier_registry import _is_reparse_point, _walk_pruned

        if os.name != "nt":
            self.skipTest("junctions are Windows-only")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            real = root / "real"
            (real / "deep").mkdir(parents=True)
            (real / "deep" / "marker.txt").write_text("x", encoding="utf-8")
            link = root / "loop"
            subprocess.run(
                ["cmd", "/d", "/c", "mklink", "/J", str(link), str(real)],
                check=True, capture_output=True,
            )
            self.assertTrue(_is_reparse_point(link))
            walked = [d for d, _dn, _fn in _walk_pruned(root)]
            self.assertNotIn(link, walked, "walk descended into the junction")
            self.assertIn(real / "deep", walked, "walk missed the real tree")


if __name__ == "__main__":
    unittest.main()
