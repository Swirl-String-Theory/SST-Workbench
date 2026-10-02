"""Run P2.6 bridge qualification on D_bridge only. Do not score M0-M3."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .bridge import qualify_p
from .kelvin import make_ring
from .mode_recon import wr_convergence_gate, reconstruct_mode, write_certificate as write_recon
from .paths import load_thresholds, pack_root, sha256_obj
from .raw_capture import write_raw_modal_timeseries
from .tube_validity import evaluate_bridge_tubes, write_certificate as write_tube

QUALIFIED = "BRIDGE_QUALIFIED"
REJECTED = "BRIDGE_REJECTED"
NO_PRODUCER = "INDETERMINATE_NO_VALID_PRODUCER"


def forbid_a029_scoring() -> None:
    raise RuntimeError("C006-v0.2.1 must not feed A029-v0.4.0 M0-M3; D_score is empty")


def run_qualification(out_dir: Path | None = None, thresholds: dict[str, Any] | None = None) -> dict[str, Any]:
    thr = thresholds or load_thresholds()
    if thr.get("holdout_scoring_enabled"):
        forbid_a029_scoring()
    if thr.get("prediction_inputs_consumed"):
        raise ValueError("prediction_inputs_consumed must stay empty")
    out = Path(out_dir or (pack_root() / "exports" / "p26_bridge"))
    out.mkdir(parents=True, exist_ok=True)

    sealed = reconstruct_mode(thresholds=thr)
    recon = write_recon(sealed, out / "MODE_RECONSTRUCTION_CERTIFICATE.json")
    ring = make_ring(int(thr["ring"]["N"]), float(thr["ring"]["R"]))
    carrier_pts = sealed["candidate"].components[0] if sealed.get("candidate") is not None else ring
    a_carrier = float(sealed["record"].get("core_fraction") or 0.05)
    tube = evaluate_bridge_tubes(ring, carrier_pts, a_carrier=a_carrier, thresholds=thr)
    write_tube(tube, out / "TUBE_VALIDITY_CERTIFICATE.json")

    status = QUALIFIED
    reason = "qualified"
    p_tests = None
    wr = None
    if recon.get("status") != "RECONSTRUCTED_SAME_BRANCH" or sealed.get("q") is None:
        status = "INDETERMINATE_MODE_RECONSTRUCTION"
        reason = "mode reconstruction is not RECONSTRUCTED_SAME_BRANCH"
    elif abs(int(recon.get("m", 0))) != 1:
        status = "INDETERMINATE_INSUFFICIENT_STATE"
        reason = "centerline leading order is m=1 only"
    elif tube["status"] != "TUBE_VALID":
        status = "INDETERMINATE_TUBE_CHART_INVALID"
        reason = "Bishop tube chart is invalid; r_max was not reduced"
    else:
        wr = wr_convergence_gate(sealed, thr)
        p_tests = qualify_p(sealed, thr)
        if not wr.get("ok"):
            status = "INDETERMINATE_INSUFFICIENT_STATE"
            reason = "W_r radial-ladder gate failed"
        elif not p_tests.get("ok"):
            status = REJECTED
            reason = "P_BS qualification tests failed"

    d_bridge = ["ring", str(thr["bridge_qualification_carrier_id"])]
    cert = {
        "schema": "SST_STATE_SPACE_BRIDGE-1.0",
        "schema_version": "1.0",
        "record_type": "state_space_bridge",
        "status": status,
        "reason": reason,
        "prediction_inputs_consumed": [],
        "scientific_amplitude": "left_eigenvector_Wr_B",
        "d_bridge": d_bridge,
        "d_score": [],
        "holdout_scoring_enabled": False,
        "bridge_rejected_falsifies_a029_clock": False,
        "mode_recon_sha256": recon.get("certificate_sha256"),
        "tube_cert_sha256": tube.get("certificate_sha256"),
        "thresholds_sha256": sha256_obj(thr),
        "mode_recon_status": recon.get("status"),
        "tube_status": tube.get("status"),
        "p_tests": p_tests,
        "wr_convergence": wr,
        "a029_scored": False,
    }
    cert["certificate_sha256"] = sha256_obj({k: cert[k] for k in cert if k != "certificate_sha256"})
    (out / "BRIDGE_CERTIFICATE.json").write_text(json.dumps(cert, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if status == QUALIFIED and sealed.get("q") is not None:
        t = [0.0, 0.01, 0.02]
        a = [0.0, 0.0, 0.0]
        write_raw_modal_timeseries(
            out / "raw_timeseries" / "d_bridge_qualification_provenance.json",
            t=t,
            a=a,
            source_id="C006-v0.2.1-D_bridge",
            spatial_basis=sealed["q"],
            scientific=True,
            extra={
                "bridge_status": QUALIFIED,
                "mode_recon_status": "RECONSTRUCTED_SAME_BRANCH",
                "tube_status": "TUBE_VALID",
                "prediction_inputs_consumed": [],
                "d_set": "D_bridge",
                "scored": False,
            },
        )
    return cert
