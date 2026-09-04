"""Tests for falsifier_registry.py."""

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
    NUMERICS_STATUSES,
    PHYSICS_STATUSES,
    WB,
    discover_unregistered,
    load_entries,
    load_registry,
    parse_version,
    reset_pack_index,
    resolve_pack,
    validate_registry,
)

REGISTRY = WB / "falsifier_registry.yaml"


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


class TestValidateRegistry(unittest.TestCase):
    def test_live_registry_valid(self) -> None:
        errs = validate_registry(path=REGISTRY)
        self.assertEqual(errs, [], msg="\n".join(errs))

    def test_all_families_present(self) -> None:
        data = load_registry(REGISTRY)
        fams = {e["family"] for e in data["entries"]}
        self.assertEqual(fams, FAMILIES)

    def test_unique_ids(self) -> None:
        data = load_registry(REGISTRY)
        ids = [e["id"] for e in data["entries"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_physics_numerics_enums(self) -> None:
        data = load_registry(REGISTRY)
        for e in data["entries"]:
            self.assertIn(e["physics_status"], PHYSICS_STATUSES)
            self.assertIn(e["numerics_status"], NUMERICS_STATUSES)


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
        entries = load_entries(REGISTRY)
        self.assertGreaterEqual(len(entries), 40)

    def test_most_entries_resolve(self) -> None:
        entries = load_entries(REGISTRY)
        unresolved = [e.id for e in entries if e.resolved is None]
        self.assertLessEqual(len(unresolved), 2, msg=str(unresolved))


class TestDiscoverUnregistered(unittest.TestCase):
    def setUp(self) -> None:
        reset_pack_index()

    def test_discover_returns_list(self) -> None:
        entries = load_entries(REGISTRY, resolve=False)
        gaps = discover_unregistered(entries)
        self.assertIsInstance(gaps, list)


class TestRegistryEntryCount(unittest.TestCase):
    def test_entry_count_near_45(self) -> None:
        data = load_registry(REGISTRY)
        self.assertGreaterEqual(len(data["entries"]), 43)
        self.assertLessEqual(len(data["entries"]), 50)


if __name__ == "__main__":
    unittest.main()
