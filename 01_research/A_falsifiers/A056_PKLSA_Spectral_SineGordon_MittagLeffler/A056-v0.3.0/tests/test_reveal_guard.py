from pathlib import Path
import json, sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from a056_science.reveal_guard import reveal_eligibility


def _write(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj), encoding="utf-8")


def _fixture(tmp_path: Path, g2="FAIL", g3="NOT_RUN_PREREQUISITE", unresolved=False):
    root = tmp_path / "instance"
    out = root / "out"
    out.mkdir(parents=True)
    _write(root / "blind_policy.json", {
        "reveal_allowed_after_modes": ["FULL", "CERTIFY"],
        "reveal_requires_gate": "G3",
        "reveal_requires_gate_status": ["PASS", "FAIL"],
        "block_reveal_on_unresolved": True,
    })
    _write(root / "preregistration" / "FROZEN_PROTOCOL.json", {"bundle_sha256": "abc"})
    _write(out / "RUN_SUMMARY.json", {"mode": "FULL", "protocol_bundle_sha256": "abc"})
    records = [
        {"gate_id": "G0", "status": "PASS"},
        {"gate_id": "G1", "status": "PASS"},
        {"gate_id": "G2", "status": g2},
        {"gate_id": "G3", "status": g3},
    ]
    if unresolved:
        records.append({"gate_id": "G5", "status": "UNRESOLVED"})
    _write(out / "GATE_LEDGER.json", {"ledger_sha256": "ledger", "records": records})
    return root, out


def test_reveal_withheld_when_discovery_not_run(tmp_path):
    root, out = _fixture(tmp_path)
    d = reveal_eligibility(root, out)
    assert d["eligible"] is False
    assert "G3 status=NOT_RUN_PREREQUISITE" in d["reason"]
    assert "G2=FAIL" in d["reason"]


def test_reveal_allowed_after_completed_negative_discovery(tmp_path):
    root, out = _fixture(tmp_path, g2="PASS", g3="FAIL")
    d = reveal_eligibility(root, out)
    assert d["eligible"] is True


def test_reveal_withheld_on_unresolved_gate(tmp_path):
    root, out = _fixture(tmp_path, g2="PASS", g3="PASS", unresolved=True)
    d = reveal_eligibility(root, out)
    assert d["eligible"] is False
    assert d["unresolved_gates"] == ["G5"]
