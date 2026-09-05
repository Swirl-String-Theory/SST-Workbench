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
