from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from sst_seed_falsifier.modal_dispatch import (
    BLOCKED_PROVENANCE,
    QUALIFIED,
    enforce_modal_dispatch,
    evaluate_certs,
    ModalDispatchBlocked,
)
from sst_seed_falsifier.provenance_lock import is_fixture_cert, is_placeholder_cert, provenance_issue


def _hash(seed: str) -> str:
    return hashlib.sha256(seed.encode()).hexdigest()


def _cert(*, gate="geometry", run="genuine-run", kind="CAMPAIGN", out=None, inn=None):
    return {
        "schema": "SST-SCIENTIFIC-CERTIFICATE-1.0",
        "certificate_kind": kind,
        "gate": gate,
        "source_run_id": run,
        "source_output_sha256": out or _hash(run + gate + "o"),
        "gate_input_sha256": inn or _hash(run + gate + "i"),
        "provenance_sha256": _hash(run + gate + "p"),
        "synthetic_inputs": False,
    }


def test_missing_certs_block():
    result = evaluate_certs({})
    assert result["dispatch_status"] == BLOCKED_PROVENANCE
    assert result["qualified_for_modal_analysis"] is False


def test_fixture_geometry_blocks_provenance():
    certs = {
        "geometry": _cert(gate="fixture", run="fixture-run", out="c" * 64, inn="d" * 64),
        "mesh": _cert(gate="mesh"),
        "admissibility": _cert(gate="constrained_admissibility"),
        "symmetry": _cert(gate="symmetry_selection"),
    }
    assert is_fixture_cert(certs["geometry"])
    assert is_placeholder_cert(certs["geometry"])
    result = evaluate_certs(certs)
    assert result["dispatch_status"] == BLOCKED_PROVENANCE


def test_selftest_is_not_scientific_qualify():
    certs = {k: _cert(gate=k, run="selftest", kind="SELFTEST") for k in ("geometry", "mesh", "admissibility", "symmetry")}
    result = evaluate_certs(certs)
    assert result["dispatch_status"] != QUALIFIED
    assert result["qualified_for_modal_analysis"] is False


def test_genuine_campaign_qualifies_and_a030_is_irrelevant(tmp_path: Path):
    certs = {
        "geometry": _cert(gate="geometry"),
        "mesh": _cert(gate="mesh"),
        "admissibility": _cert(gate="constrained_admissibility"),
        "symmetry": _cert(gate="symmetry_selection"),
        "A030": {"status": "FAIL"},
        "A035": {"status": "FAIL"},
    }
    dest = tmp_path / "paper_upgrade"
    dest.mkdir()
    (dest / "upstream_certs.json").write_text(json.dumps(certs), encoding="utf-8")
    result = enforce_modal_dispatch(tmp_path, {"run_kind": "blind_scientific"})
    assert result["dispatch_status"] == QUALIFIED
    assert result["dynamic_stability_claim"] is False


def test_scientific_run_raises_without_certs(tmp_path: Path):
    with pytest.raises(ModalDispatchBlocked):
        enforce_modal_dispatch(tmp_path, {"run_kind": "blind_scientific"})


def test_workflow_smoke_does_not_raise(tmp_path: Path):
    result = enforce_modal_dispatch(tmp_path, {"run_kind": "workflow_smoke"})
    assert result["dispatch_status"] == BLOCKED_PROVENANCE
