"""PC02 — A037-v0.3.3 qualification-before-observable helpers.

Do not measure χ_ij until temporal/spatial/mesh qualification PASSes.
Split mirror code-sanity from physical trajectory response.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

WB = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(WB / "07_scripts"))

import paper_upgrade_certificate as puc  # noqa: E402
import paper_upgrade_numerics as pun  # noqa: E402

LABEL_MIRROR = "DISCRETE_OPERATOR_MIRROR_COVARIANCE"
LABEL_PHYSICAL = "PHYSICAL_TRAJECTORY_SYMMETRY_RESPONSE"


def split_labels(*, mirror_pass: bool, numerically_qualified: bool) -> dict[str, str]:
    mirror = "PASS" if mirror_pass else "FAIL"
    if not numerically_qualified:
        physical = "INVALID_NUMERICS"
    else:
        physical = "PASS" if mirror_pass else "FAIL"
    return {LABEL_MIRROR: mirror, LABEL_PHYSICAL: physical}


def may_measure_chi_ij(nq: dict[str, Any]) -> bool:
    return (
        nq.get("temporal") == "PASS"
        and nq.get("spatial") == "PASS"
        and nq.get("mesh") == "PASS"
    )


def campaign_or_invalid(
    *,
    mirror_pass: bool,
    temporal_series: list[tuple[float, float]],
    spatial_series: list[tuple[int, float]],
    ds_cv: float,
    n_points: int,
) -> dict[str, Any]:
    t = pun.temporal_ladder_pass(temporal_series)
    s = pun.spatial_ladder_pass(spatial_series)
    m = pun.mesh_quality_pass(ds_cv=ds_cv, n_points=n_points)
    nq = {
        "temporal": t["status"],
        "spatial": s["status"],
        "mesh": m["status"],
    }
    qualified = may_measure_chi_ij(nq)
    labels = split_labels(mirror_pass=mirror_pass, numerically_qualified=qualified)
    status = "PASS" if qualified and mirror_pass else ("INVALID_NUMERICS" if not qualified else "FAIL")
    cert = puc.apply_certificate_envelope(
        {
            "family": "A037",
            "labels": labels,
            "chi_ij_measured": False if not qualified else True,
            "scientific_label": "INVALID_NUMERICS / NOT_YET_TESTED_2505" if not qualified else status,
            "provenance_sha256": "d" * 64,
        },
        certificate_kind="CAMPAIGN",
        producer="A037",
        gate="symmetry_selection",
        payload_schema="SST-SYMMETRY-SELECTION-1.0",
        scientific=True,
        gate_status=status,
        source_run_id="a037-pc02",
        source_output_sha256="e" * 64,
        gate_input_sha256="f" * 64,
        numerical_qualification=nq,
        synthetic_inputs=False,
    )
    return {
        "numerical_qualification": nq,
        "labels": labels,
        "chi_ij_allowed": qualified,
        "certificate": cert,
        "promotion_allowed": cert["promotion_allowed"],
    }


def selftest() -> dict[str, Any]:
    # Under-resolved: mirror may PASS, physical must be INVALID_NUMERICS, no χ_ij.
    bad = campaign_or_invalid(
        mirror_pass=True,
        temporal_series=[(1.0, 1.0), (0.5, 2.0), (0.25, 3.0)],  # large errors → FAIL
        spatial_series=[(72, 1.0), (144, 2.0), (288, 3.0)],
        ds_cv=0.5,
        n_points=72,
    )
    assert bad["labels"][LABEL_MIRROR] == "PASS"
    assert bad["labels"][LABEL_PHYSICAL] == "INVALID_NUMERICS"
    assert bad["chi_ij_allowed"] is False
    assert bad["promotion_allowed"] is False

    good = campaign_or_invalid(
        mirror_pass=True,
        temporal_series=[(1.0, 1.0), (0.5, 1.01), (0.25, 1.011)],
        spatial_series=[(72, 1.0), (144, 1.01), (288, 1.011)],
        ds_cv=0.1,
        n_points=72,
    )
    assert good["chi_ij_allowed"] is True
    assert good["labels"][LABEL_PHYSICAL] == "PASS"
    return {"status": "PASS", "bad_promotion": bad["promotion_allowed"], "good_chi_allowed": good["chi_ij_allowed"]}


if __name__ == "__main__":
    out = selftest()
    print(json.dumps(out, indent=2, sort_keys=True))
    raise SystemExit(0 if out["status"] == "PASS" else 1)
