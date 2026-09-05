"""Tests for catalog_metadata.py (SP08)."""
from __future__ import annotations

import sys
from pathlib import Path

WB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WB / "07_scripts"))

import catalog_metadata as cm  # noqa: E402


class TestParseVersion:
    def test_plain_semver(self):
        v = cm.parse_version("SST_Quantum_Galileo_Action_Gauge_Closure_Falsifier_v0.1.0")
        assert v.version == "v0.1.0"
        assert v.revision is None
        assert v.config is None
        assert v.blind is None

    def test_four_part_becomes_version_plus_revision(self):
        """v0.2.2.8 is v0.2.2 revision 8, not a fourth version component."""
        v = cm.parse_version("SST_Intrinsic_Modal_Swirl_Clock_Blind_Falsifier_v0.2.2.8")
        assert v.version == "v0.2.2"
        assert v.revision == 8

    def test_config_carried_in_the_directory_name(self):
        v = cm.parse_version(
            "SST_MultiTopology_Knot_Link_TBK_RPO_Falsifier_v0.4.8_Adaptive_Spectral_DD32_compact"
        )
        assert v.version == "v0.4.8"
        assert v.config == "adaptive-spectral-dd32-compact"
        assert v.blind is None

    def test_blinding_is_not_a_config(self):
        """Blind and revealed must stay distinguishable, never merged into config."""
        for name, expected in (
            ("Pack_v0.1.1_BLIND_SOURCE", "blind"),
            ("Pack_v0.1.1_REVEAL_KEY", "reveal_key"),
            ("Pack_v0.2.0_UNBLIND_KEY", "reveal_key"),
            ("Pack_v0.3.0_REVEALED", "revealed"),
        ):
            v = cm.parse_version(name)
            assert v.blind == expected, name
            assert v.config is None, name

    def test_closed_historical_series_is_left_alone(self):
        """Track B ids like v16B0 carry meaning; they are recorded, not normalised."""
        v = cm.parse_version("sst_chi_phase_package_v16B0")
        assert v.version == "v16B0"
        assert v.revision is None

    def test_underscore_version_style(self):
        v = cm.parse_version("SST_contra_swirl_bridge_research_v0_6")
        assert v.version == "v0_6"

    def test_catalog_prefixed_short_name(self):
        v = cm.parse_version("A042-v0.1.1")
        assert v.version == "v0.1.1"
        assert v.revision is None
        assert v.config is None

    def test_revision_suffix_on_short_name_is_not_config(self):
        v = cm.parse_version("A032-v0.2.2-r8")
        assert v.version == "v0.2.2"
        assert v.revision == 8
        assert v.config is None

    def test_directory_without_version_token(self):
        v = cm.parse_version("sst_horn_dirichlet_package")
        assert v.version == "sst_horn_dirichlet_package"
        assert v.revision is None


class TestOutputPrefix:
    def test_common_stem_across_versions(self):
        versions = [
            cm.parse_version("SST_Wien_Planck_Falsifier_v0.1.0"),
            cm.parse_version("SST_Wien_Planck_Falsifier_v0.2.0"),
        ]
        assert cm.output_prefix_for(versions) == "SST_Wien_Planck_Falsifier"

    def test_no_prefix_when_names_do_not_share_a_stem(self):
        versions = [
            cm.parse_version("alpha_v0.1.0"),
            cm.parse_version("beta_v0.2.0"),
        ]
        assert cm.output_prefix_for(versions) == ""

    def test_prefix_is_empty_without_version_tokens(self):
        assert cm.output_prefix_for([cm.parse_version("plain_directory")]) == ""


class TestSortKey:
    def test_versions_order_numerically_not_lexically(self):
        names = ["Pack_v0.2.0", "Pack_v0.10.0", "Pack_v0.1.0"]
        versions = sorted((cm.parse_version(n) for n in names), key=cm.sort_key)
        assert [v.version for v in versions] == ["v0.1.0", "v0.2.0", "v0.10.0"]

    def test_revision_orders_after_its_base_version(self):
        versions = sorted(
            (cm.parse_version(n) for n in ["Pack_v0.2.2.8", "Pack_v0.2.2", "Pack_v0.2.2.5"]),
            key=cm.sort_key,
        )
        assert [(v.version, v.revision) for v in versions] == [
            ("v0.2.2", None), ("v0.2.2", 5), ("v0.2.2", 8),
        ]


class TestShortDirectoryName:
    def test_plain_semver(self):
        v = cm.parse_version("SST_Quantum_Galileo_Action_Gauge_Closure_Falsifier_v0.1.1")
        assert cm.short_directory_name("A042", v) == "A042-v0.1.1"

    def test_revision(self):
        v = cm.parse_version("SST_Intrinsic_Modal_Swirl_Clock_Blind_Falsifier_v0.2.2.8")
        assert cm.short_directory_name("A035", v) == "A035-v0.2.2-r8"

    def test_config_is_omitted_when_unique(self):
        v = cm.parse_version(
            "SST_MultiTopology_Knot_Link_TBK_RPO_Falsifier_v0.4.8_Adaptive_Spectral_DD32_compact"
        )
        assert cm.short_directory_name("A023", v) == "A023-v0.4.8"

    def test_closed_historical_series(self):
        v = cm.parse_version("sst_chi_phase_package_v16B0")
        assert cm.short_directory_name("C001", v) == "C001-v16B0"

    def test_live_families_have_unique_short_names(self):
        collisions = []
        for fam in cm.discover():
            if not fam.versions:
                continue
            mapping = cm.short_names_for_family(fam)
            assert len(mapping) == len(fam.versions)
            if len(set(mapping.values())) != len(mapping):
                collisions.append(fam.catalog_id)
        assert collisions == []


class TestGeneratedDocuments:
    def _family(self) -> cm.Family:
        fam = cm.Family(
            catalog_id="A042", slug="quantum_galileo", domain="01_research",
            letter="A_falsifiers", path=WB, name='SST Quantum "Galileo" Falsifier',
        )
        fam.versions = [cm.parse_version("SST_Quantum_Galileo_Falsifier_v0.1.0")]
        fam.output_prefix = "SST_Quantum_Galileo_Falsifier"
        return fam

    def test_family_yaml_quotes_embedded_quotes(self):
        text = cm.family_yaml(self._family())
        assert r'\"Galileo\"' in text

    def test_family_yaml_records_output_prefix(self):
        """SP09 renames directories; the output name must come from here instead."""
        text = cm.family_yaml(self._family())
        assert 'output_prefix: "SST_Quantum_Galileo_Falsifier"' in text

    def test_project_json_keeps_the_legacy_directory_name(self):
        import json

        fam = self._family()
        payload = json.loads(cm.project_json(fam, fam.versions[0]))
        assert payload["legacy_dir"] == "SST_Quantum_Galileo_Falsifier_v0.1.0"
        assert payload["catalog_id"] == "A042"
        assert payload["version"] == "v0.1.0"

    def test_empty_collections_render_as_flow_lists(self):
        text = cm.family_yaml(self._family())
        assert "variants: []" in text
        assert "legacy_paths: []" in text
        assert "intermediate_paths: []" in text


class TestLegacyByDomain:
    #: Catalog ids legitimately reused across domains (design, not a bug).
    SHARED_IDS = ("A001", "A002", "A003", "A004", "B001", "C001", "D001")

    def test_legacy_keyed_on_domain_and_catalog_id(self):
        hist = cm.legacy_by_id()
        assert isinstance(next(iter(hist)), tuple)
        assert all(len(k) == 2 for k in hist)

    def test_shared_ids_keep_disjoint_histories(self):
        """A003 in research must not inherit apps A003's vortexring-lab paths."""
        hist = cm.legacy_by_id()
        for cid in self.SHARED_IDS:
            keys = [k for k in hist if k[1] == cid]
            if len(keys) < 2:
                continue
            path_sets = []
            for key in keys:
                paths = set(hist[key]["legacy_paths"]) | set(hist[key]["intermediate_paths"])
                path_sets.append((key, paths))
            for i, (ka, pa) in enumerate(path_sets):
                for kb, pb in path_sets[i + 1 :]:
                    overlap = pa & pb
                    assert overlap == set(), (
                        f"{ka} and {kb} share legacy/intermediate paths: {sorted(overlap)[:5]}"
                    )

    def test_discovered_families_do_not_carry_foreign_legacy_paths(self):
        """Every legacy/intermediate path on a family must match its (domain, id) rows."""
        hist = cm.legacy_by_id()
        bad = []
        for fam in cm.discover():
            expected = hist.get((fam.domain, fam.catalog_id), {
                "legacy_paths": [], "intermediate_paths": [],
            })
            if fam.legacy_paths != expected["legacy_paths"]:
                bad.append((fam.domain, fam.catalog_id, "legacy_paths"))
            if fam.intermediate_paths != expected["intermediate_paths"]:
                bad.append((fam.domain, fam.catalog_id, "intermediate_paths"))
        assert bad == [], f"family history mismatch: {bad[:10]}"

    def test_no_family_inherits_another_domains_history_for_shared_id(self):
        """The seven reused ids must not merge path_map rows across domains."""
        cases = [
            (("01_research", "A003"), "05_apps/A002_coil_gui/vortexring-lab"),
            (("01_research", "B001"), "Independent_FiniteCore_SpectralSelector"),
            (("01_research", "B001"), "Katlas_Source_Crawler_v0.2.2"),
            (("01_research", "C001"), "3D"),
            (("01_research", "D001"), "proof-scripts"),
        ]
        hist = cm.legacy_by_id()
        for key, foreign in cases:
            buckets = hist.get(key, {"legacy_paths": [], "intermediate_paths": []})
            all_paths = set(buckets["legacy_paths"]) | set(buckets["intermediate_paths"])
            assert foreign not in all_paths, f"{key} still carries {foreign}"

    def test_intermediate_paths_are_catalog_domain_prefixed(self):
        for fam in cm.discover():
            for p in fam.intermediate_paths:
                assert cm.is_intermediate_path(p), p
            for p in fam.legacy_paths:
                assert not cm.is_intermediate_path(p), p

    def test_research_a003_does_not_claim_vortexring_lab(self):
        fams = {
            (f.domain, f.catalog_id): f
            for f in cm.discover()
            if f.catalog_id == "A003"
        }
        research = fams[("01_research", "A003")]
        apps = fams[("05_apps", "A003")]
        assert "05_apps/A002_coil_gui/vortexring-lab" not in research.legacy_paths
        assert "05_apps/A002_coil_gui/vortexring-lab" not in research.intermediate_paths
        assert "SST_dark_knot_rayleigh_research" in research.legacy_paths
        assert "05_apps/A002_coil_gui/vortexring-lab" in apps.intermediate_paths
