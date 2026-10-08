from pathlib import Path
import json
import pytest

from master_mass.pklsa import load_cross_manifest, EXPECTED_CROSS_SCHEMA

ROOT = Path(__file__).resolve().parents[1]


def valid_manifest():
    return {
        "schema": EXPECTED_CROSS_SCHEMA,
        "sklsa_release_id": "E011-v0.3.0",
        "legacy_falsifier_outputs_used_as_evidence": False,
        "carriers": [{
            "topology_id": "3_1",
            "static_seed_id": "SEED_TEST",
            "carrier_id": "CAR_TEST",
            "provider_group": "provider_a",
            "geometry_sha256": "a" * 64,
            "source_locator": {
                "source_path": "C:/fake/geometry.xyz",
                "representation": "xyz",
                "geometry_sha256": "a" * 64,
            },
        }],
    }


def write(tmp_path, obj):
    p = tmp_path / "manifest.json"
    p.write_text(json.dumps(obj), encoding="utf-8")
    return p


def test_cross_member_contract_is_e013_v2():
    c = json.loads((ROOT / "cross_falsifier_contract.json").read_text(encoding="utf-8"))
    assert c["schema"] == "SST-CROSS-FALSIFIER-MEMBER-2"
    assert c["input_geometry_source"] == "E013_COMMON_SKLSA_PROVIDER_ANCHORS"
    assert c["forbid_legacy_outputs"] is True
    assert c["accepted_sklsa_release_ids"] == ["E011-v0.3.0"]


def test_valid_cross_manifest(tmp_path):
    d = valid_manifest()
    assert load_cross_manifest(write(tmp_path, d))["carriers"][0]["static_seed_id"] == "SEED_TEST"


@pytest.mark.parametrize("mutation", ["schema", "release", "legacy", "join_key"])
def test_cross_manifest_fail_closed(tmp_path, mutation):
    d = valid_manifest()
    if mutation == "schema":
        d["schema"] = "OLD"
    elif mutation == "release":
        d["sklsa_release_id"] = "E011-v0.2.0"
    elif mutation == "legacy":
        d["legacy_falsifier_outputs_used_as_evidence"] = True
    else:
        d["carriers"][0].pop("static_seed_id")
    with pytest.raises((ValueError, FileNotFoundError)):
        load_cross_manifest(write(tmp_path, d))


def test_configs_require_e013_and_forbid_direct_discovery():
    for name in ("basic", "full", "certify"):
        c = json.loads((ROOT / "configs" / f"{name}.json").read_text())
        assert c["require_e013_manifest"] is True
        assert c["allow_direct_e010_fallback"] is False
