"""SP08 done-criteria: metadata, registry and index agree with the tree."""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

WB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WB / "07_scripts"))

import build_catalog_index as bci  # noqa: E402
import catalog_metadata as cm  # noqa: E402

REGISTRY = WB / "falsifier_registry.yaml"
INDEX = WB / "10_docs" / "registry" / "catalog_index.json"


def _families():
    return cm.discover()


class TestFamilyYaml:
    def test_every_family_has_one(self):
        missing = [f.catalog_id for f in _families() if not (f.path / "FAMILY.yaml").is_file()]
        assert missing == [], f"families without FAMILY.yaml: {missing}"

    def test_catalog_id_is_unique_within_its_domain(self):
        """A bare id must identify one family, or FAMILY.yaml encodes a false identity."""
        per_domain: dict[str, Counter] = {}
        for f in _families():
            per_domain.setdefault(f.domain, Counter())[f.catalog_id] += 1
        clashes = {
            domain: [cid for cid, n in counts.items() if n > 1]
            for domain, counts in per_domain.items()
        }
        clashes = {d: c for d, c in clashes.items() if c}
        assert clashes == {}, f"duplicate ids: {clashes}"

    def test_unversioned_families_declare_themselves(self):
        """A family laid out by topic has no versions, and must say so.

        B001_derive_constants holds audits/, code/, figures/ and Manuscripts/. Recording
        those as versions would make SP09 rename them, so the distinction has to be
        explicit rather than inferred later.
        """
        for f in _families():
            text = (f.path / "FAMILY.yaml").read_text(encoding="utf-8")
            declared = "unversioned: true" in text
            assert declared == f.unversioned, f"{f.catalog_id} mismatch"
            if declared:
                assert "versions: []" in text, f"{f.catalog_id} claims unversioned but lists versions"

    def test_latest_names_a_version_that_exists(self):
        bad = []
        for f in _families():
            if not f.versions:
                continue
            text = (f.path / "FAMILY.yaml").read_text(encoding="utf-8")
            m = re.search(r"^latest: (\S+)$", text, re.M)
            if not m:
                bad.append((f.catalog_id, "no latest"))
                continue
            if m.group(1) not in {v.version for v in f.versions}:
                bad.append((f.catalog_id, m.group(1)))
        assert bad == [], f"latest does not match a version: {bad}"

    def test_families_with_versions_record_an_output_prefix(self):
        """SP09 renames directories, so the output name must come from metadata."""
        missing = []
        for f in _families():
            if f.unversioned or len(f.versions) < 2:
                continue  # a single version has no common stem to derive
            text = (f.path / "FAMILY.yaml").read_text(encoding="utf-8")
            if "output_prefix:" in text:
                continue
            # No shared stem is a legitimate state, but it must be declared so SP09
            # does not silently invent an output name.
            if "heterogeneous: true" not in text:
                missing.append(f.catalog_id)
        assert missing == [], (
            f"multi-version families with neither output_prefix nor a heterogeneous "
            f"flag: {missing}"
        )

    def test_blinding_is_recorded_separately_from_config(self):
        """Blind and revealed must never collapse into one another."""
        seen = 0
        for f in _families():
            text = (f.path / "FAMILY.yaml").read_text(encoding="utf-8")
            for line in text.splitlines():
                if line.strip().startswith("blind:"):
                    seen += 1
                    assert line.split(":", 1)[1].strip() in {"blind", "reveal_key", "revealed"}
        assert seen > 0, "no blinded version found; the field is probably not being written"


class TestProjectJson:
    def test_every_version_has_one_and_it_matches_its_family(self):
        bad = []
        for f in _families():
            for v in f.versions:
                path = f.path / v.directory / "project.json"
                if not path.is_file():
                    bad.append((f.catalog_id, v.directory, "missing"))
                    continue
                data = json.loads(path.read_text(encoding="utf-8"))
                if data.get("catalog_id") != f.catalog_id:
                    bad.append((f.catalog_id, v.directory, "wrong catalog_id"))
                elif data.get("version") != v.version:
                    bad.append((f.catalog_id, v.directory, "wrong version"))
        assert bad == [], f"project.json problems: {bad[:10]}"

    def test_legacy_dir_preserves_the_pre_rename_name(self):
        """After SP09 renames directories this is the only record of the old name."""
        for f in _families():
            for v in f.versions:
                path = f.path / v.directory / "project.json"
                data = json.loads(path.read_text(encoding="utf-8"))
                assert data["legacy_dir"]
                if re.match(rf"^{f.catalog_id}-v", v.directory):
                    assert data["legacy_dir"] != v.directory
                else:
                    assert data["legacy_dir"] == v.directory


class TestRegistrySync:
    def test_every_entry_has_a_catalog_id(self):
        text = REGISTRY.read_text(encoding="utf-8")
        globs = len(re.findall(r"^\s*pack_glob:", text, re.M))
        ids = len(re.findall(r"^\s*catalog_id:\s*\S", text, re.M))
        assert ids == globs, f"{globs} pack_glob entries but {ids} catalog_id values"

    def test_registry_ids_exist_in_the_catalog(self):
        text = REGISTRY.read_text(encoding="utf-8")
        used = set(re.findall(r"^\s*catalog_id:\s*([A-F]\d{3})", text, re.M))
        known = {f.catalog_id for f in _families()}
        # A005 is reserved and archive-only: it has no directory by design.
        unknown = used - known - {"A005"}
        assert unknown == set(), f"registry references unknown ids: {sorted(unknown)}"

    def test_pack_glob_is_kept_for_archive_lookup(self):
        """Zip filenames in 09_archive/restore keep the historical naming forever."""
        text = REGISTRY.read_text(encoding="utf-8")
        assert "pack_glob:" in text


class TestCatalogIndex:
    def test_index_matches_a_fresh_walk(self):
        on_disk = bci.build()
        stored = json.loads(INDEX.read_text(encoding="utf-8"))
        assert stored["families"] == on_disk["families"]
        assert stored["versions"] == on_disk["versions"]

    def test_legacy_lookup_resolves_a_known_old_path(self):
        stored = json.loads(INDEX.read_text(encoding="utf-8"))
        lookup = stored["legacy_lookup"]
        assert lookup, "legacy lookup is empty; old paths would be unresolvable"
        assert any(old.startswith("SST_") for old in lookup)
