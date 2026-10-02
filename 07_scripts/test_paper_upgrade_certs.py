"""Tests for paper_upgrade_certs + SST-SCIENTIFIC-CERTIFICATE-1.0 (PC00)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

WB = Path(__file__).resolve().parents[1]
CERTS = WB / "07_scripts" / "paper_upgrade_certs.py"
A034_GATE = WB / "01_research/A_falsifiers/A034_qhp_stability_landscape/A034-v0.2.0/paper_upgrade/gate.py"
A037_GATE = WB / "01_research/A_falsifiers/A037_chirality_helicity_transport_polarity/A037-v0.3.0/paper_upgrade/gate.py"
A021_GATE = WB / "01_research/A_falsifiers/A021_trefoil_lobe_self_confinement/A021-v0.4.0/paper_upgrade/gate.py"
A038_GATE = WB / "01_research/A_falsifiers/A038_trefoil_dynamic_seed_qualification/A038-v0.4.0/paper_upgrade/gate.py"
A036_GATE = WB / "01_research/A_falsifiers/A036_scii_intrinsic_modal_phase_clock/A036-v0.1.1/paper_upgrade/gate.py"

sys.path.insert(0, str(WB / "07_scripts"))
import paper_upgrade_certs as puc  # noqa: E402
import paper_upgrade_certificate as pucc  # noqa: E402


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(CERTS), *args], capture_output=True, text=True)


def test_emit_a034_synthetic_not_promotable(tmp_path: Path):
    out = tmp_path / "basic"
    proc = _run("emit-a034-synthetic", "--out", str(out), "--gate", str(A034_GATE))
    assert proc.returncode == 0, proc.stderr
    cert = json.loads((out / "paper_upgrade" / "certificate.json").read_text(encoding="utf-8"))
    assert cert["schema"] == pucc.SCHEMA
    assert cert["certificate_kind"] == "SELFTEST"
    assert cert["scientific"] is False
    assert cert["status"] == "PIPELINE_PASS"
    assert cert["promotion_allowed"] is False
    assert cert["synthetic_inputs"] is True
    assert cert["payload_schema"] == "SST-ADMISSIBILITY-1.0"
    assert not pucc.promotable(cert)


def test_emit_a037_synthetic_not_promotable(tmp_path: Path):
    out = tmp_path / "basic"
    proc = _run("emit-a037-synthetic", "--out", str(out), "--gate", str(A037_GATE))
    assert proc.returncode == 0, proc.stderr
    cert = json.loads((out / "paper_upgrade" / "certificate.json").read_text(encoding="utf-8"))
    assert cert["certificate_kind"] == "SELFTEST"
    assert cert["promotion_allowed"] is False
    assert cert["synthetic_inputs"] is True


def test_consume_rejects_synthetic(tmp_path: Path):
    out = tmp_path / "a034"
    _run("emit-a034-synthetic", "--out", str(out), "--gate", str(A034_GATE))
    cert = out / "paper_upgrade" / "certificate.json"
    proc = _run("consume-a034", "--cert", str(cert), "--gate", str(A021_GATE))
    assert proc.returncode == 1
    assert json.loads(proc.stdout)["accepted"] is False


def test_consume_accepts_campaign(tmp_path: Path):
    cert = puc.campaign_fixture_cert(
        family="A034",
        payload_schema="SST-ADMISSIBILITY-1.0",
        classification="ENERGETICALLY_ADMISSIBLE",
        gate="constrained_admissibility",
    )
    path = puc.write_certificate(tmp_path / "a034", cert)
    written = json.loads(path.read_text(encoding="utf-8"))
    assert written["promotion_allowed"] is True
    assert pucc.promotable(written)
    proc = _run("consume-a034", "--cert", str(path), "--gate", str(A021_GATE))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert json.loads(proc.stdout)["accepted"] is True


def test_campaign_without_numerical_qualification_rejected(tmp_path: Path):
    cert = puc.campaign_fixture_cert(
        family="A034",
        payload_schema="SST-ADMISSIBILITY-1.0",
        classification="ENERGETICALLY_ADMISSIBLE",
    )
    cert["numerical_qualification"] = {"temporal": "NOT_RUN", "spatial": "PASS", "mesh": "PASS"}
    path = puc.write_certificate(tmp_path / "a034", cert)
    written = json.loads(path.read_text(encoding="utf-8"))
    assert written["promotion_allowed"] is False
    assert not pucc.promotable(written)
    proc = _run("consume-a034", "--cert", str(path), "--gate", str(A021_GATE))
    assert proc.returncode == 1


def test_upstream_rejects_synthetic(tmp_path: Path):
    a034 = tmp_path / "a034"
    a037 = tmp_path / "a037"
    _run("emit-a034-synthetic", "--out", str(a034), "--gate", str(A034_GATE))
    _run("emit-a037-synthetic", "--out", str(a037), "--gate", str(A037_GATE))
    c34 = json.loads((a034 / "paper_upgrade" / "certificate.json").read_text(encoding="utf-8"))
    c37 = json.loads((a037 / "paper_upgrade" / "certificate.json").read_text(encoding="utf-8"))
    certs = {
        "geometry": puc.campaign_fixture_cert(family="geometry", payload_schema="SST-GEOMETRY-1.0"),
        "mesh": puc.campaign_fixture_cert(family="mesh", payload_schema="SST-MESH-1.0"),
        "admissibility": c34,
        "symmetry": c37,
    }
    certs_path = tmp_path / "upstream.json"
    certs_path.write_text(json.dumps(certs), encoding="utf-8")
    proc = _run("upstream-a038", "--certs", str(certs_path), "--gate", str(A038_GATE))
    assert proc.returncode == 1
    data = json.loads(proc.stdout)
    assert data["downstream_authorized"] is False
    assert any("SELFTEST" in c for c in data["block_codes"])


def test_upstream_accepts_campaign(tmp_path: Path):
    certs = {
        "geometry": puc.campaign_fixture_cert(family="geometry", payload_schema="SST-GEOMETRY-1.0"),
        "mesh": puc.campaign_fixture_cert(family="mesh", payload_schema="SST-MESH-1.0"),
        "admissibility": puc.campaign_fixture_cert(
            family="A034",
            payload_schema="SST-ADMISSIBILITY-1.0",
            classification="ENERGETICALLY_ADMISSIBLE",
            gate="constrained_admissibility",
        ),
        "symmetry": puc.campaign_fixture_cert(
            family="A037",
            payload_schema="SST-SYMMETRY-SELECTION-1.0",
            gate="symmetry_selection",
        ),
    }
    for k, c in list(certs.items()):
        certs[k] = json.loads(puc.write_certificate(tmp_path / k, c).read_text(encoding="utf-8"))
    certs_path = tmp_path / "upstream.json"
    certs_path.write_text(json.dumps(certs), encoding="utf-8")
    proc = _run("upstream-a038", "--certs", str(certs_path), "--gate", str(A038_GATE))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert json.loads(proc.stdout)["downstream_authorized"] is True


def test_upstream_numerical_block_code(tmp_path: Path):
    certs = {
        "geometry": puc.campaign_fixture_cert(family="geometry", payload_schema="SST-GEOMETRY-1.0"),
        "mesh": puc.campaign_fixture_cert(family="mesh", payload_schema="SST-MESH-1.0"),
        "admissibility": puc.campaign_fixture_cert(
            family="A034",
            payload_schema="SST-ADMISSIBILITY-1.0",
            classification="ENERGETICALLY_ADMISSIBLE",
        ),
        "symmetry": puc.campaign_fixture_cert(
            family="A037",
            payload_schema="SST-SYMMETRY-SELECTION-1.0",
        ),
    }
    certs["symmetry"]["numerical_qualification"] = {
        "temporal": "FAIL",
        "spatial": "PASS",
        "mesh": "PASS",
    }
    for k, c in list(certs.items()):
        certs[k] = json.loads(puc.write_certificate(tmp_path / k, c).read_text(encoding="utf-8"))
    certs_path = tmp_path / "upstream.json"
    certs_path.write_text(json.dumps(certs), encoding="utf-8")
    proc = _run("upstream-a038", "--certs", str(certs_path), "--gate", str(A038_GATE))
    assert proc.returncode == 1
    data = json.loads(proc.stdout)
    assert data["primary_block"] == "BLOCKED_UPSTREAM_NUMERICAL_QUALIFICATION"


def test_guard_blocks_without_a030(tmp_path: Path):
    bad = {"family": "A030", "schema": "WRONG", "status": "PASS"}
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(bad), encoding="utf-8")
    proc = _run("guard-a030", "--cert", str(p), "--gate", str(A036_GATE))
    assert proc.returncode == 1
    assert json.loads(proc.stdout)["migration_authorized"] is False


def test_promotion_allowed_cannot_be_spoofed(tmp_path: Path):
    cert = {
        "family": "A034",
        "schema": pucc.SCHEMA,
        "status": "PASS",
        "classification": "ENERGETICALLY_ADMISSIBLE",
        "certificate_kind": "SELFTEST",
        "scientific": False,
        "synthetic_inputs": True,
        "promotion_allowed": True,
    }
    path = puc.write_certificate(tmp_path / "spoof", cert)
    written = json.loads(path.read_text(encoding="utf-8"))
    assert written["promotion_allowed"] is False
    assert not pucc.promotable(written)


def test_live_a034_a037_campaign_certs_promotable():
    a034 = WB / "01_research/A_falsifiers/A034_qhp_stability_landscape/A034-v0.2.1/outputs/basic/paper_upgrade/certificate.json"
    a037 = WB / "01_research/A_falsifiers/A037_chirality_helicity_transport_polarity/A037-v0.3.1/outputs/basic/paper_upgrade/certificate.json"
    assert a034.is_file() and a037.is_file()
    for path in (a034, a037):
        cert = json.loads(path.read_text(encoding="utf-8"))
        assert cert["certificate_kind"] == "CAMPAIGN"
        assert cert["synthetic_inputs"] is False
        assert cert["numerical_qualification"] == {
            "temporal": "PASS",
            "spatial": "PASS",
            "mesh": "PASS",
        }
        assert cert["promotion_allowed"] is True
        assert pucc.promotable(cert)


def test_emit_campaign_cli_rejects_missing_out(tmp_path: Path):
    proc = _run(
        "emit-a037-campaign",
        "--out",
        str(tmp_path / "missing"),
        "--gate",
        str(A037_GATE),
    )
    assert proc.returncode != 0
