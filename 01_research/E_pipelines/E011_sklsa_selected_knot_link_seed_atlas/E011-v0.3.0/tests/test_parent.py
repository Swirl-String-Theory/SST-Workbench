import json
import pytest
from sklsa.parent import locate_e010_output, validate_e010_release


def _contract():
    return {
        "allowed_release_versions": ["0.3.1"],
        "expected_topology_count": 2227,
        "required_release_true": [
            "a001_a008_coverage_gate_pass", "canonical_identity_admission_gate_pass",
            "identity_database_gate_pass", "source_contract_gate_pass",
            "topology_database_ingest_gate_pass", "trefoil_poc_gate_pass",
        ],
        "global_campaign_fields_are_advisory": ["full_campaign_gate_pass", "publication_ready_geometry_layer", "failed_topology_count"],
    }


def test_locates_v031_even_when_global_campaign_partial(synthetic_workbench):
    out = locate_e010_output(synthetic_workbench)
    assert out.name.endswith("v0.3.1-outputs")


def test_parent_structural_gate_accepts_partial_v031(synthetic_workbench):
    out = locate_e010_output(synthetic_workbench)
    result = validate_e010_release(out, _contract())
    assert result["release"]["e010_version"] == "0.3.1"
    assert result["warnings"]


def test_parent_gate_still_fails_closed_on_structural_failure(synthetic_workbench):
    out = locate_e010_output(synthetic_workbench)
    p = out / "RELEASE.json"
    release = json.loads(p.read_text())
    release["identity_database_gate_pass"] = False
    p.write_text(json.dumps(release), encoding="utf-8")
    with pytest.raises(RuntimeError):
        validate_e010_release(out, _contract())
