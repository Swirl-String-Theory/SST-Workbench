#!/usr/bin/env python3
"""Verify the sealed blind result, reveal candidate identities, and compare only pre-defined observables."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

from blind_utils import (
    code_digest,
    json_dump,
    json_load,
    sha256_file,
    tree_digest,
)

ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, default=Path("blind_config.json"))
    p.add_argument("--sealed-root", type=Path, default=Path("results/blind"))
    p.add_argument("--candidate-key", type=Path, default=Path("private_reveal/DO_NOT_OPEN_candidate_key.json"))
    p.add_argument("--reveal", type=Path, default=Path("sst_reveal.json"))
    p.add_argument("--output", type=Path, default=Path("results/reveal"))
    return p.parse_args()


def classify_abs(error: float, standard: float, certified: float) -> str:
    if error <= certified:
        return "CERTIFIED_MATCH"
    if error <= standard:
        return "MATCH"
    return "NO_MATCH"


def main() -> int:
    args = parse_args()
    sealed_path = args.sealed_root / "SEALED_MANIFEST.json"
    if not sealed_path.exists():
        raise FileNotFoundError("Blind results are not sealed. Run SEAL_BLIND_RESULTS.cmd first.")
    if not args.reveal.exists():
        raise FileNotFoundError("No sst_reveal.json. Copy sst_reveal.template.json and fill it AFTER sealing.")

    sealed = json_load(sealed_path)
    cfg = json_load(args.config)
    key = json_load(args.candidate_key)
    reveal = json_load(args.reveal)

    current_result_sha, _ = tree_digest(
        args.sealed_root,
        exclude_names={"SEALED_MANIFEST.json", "BLIND_RESULT_SHA256.txt"},
        exclude_dirs={"reveal"},
    )
    if current_result_sha != sealed["result_tree_sha256"]:
        raise RuntimeError("Blind result tree changed after seal; reveal comparison is invalid.")

    current_code_sha, _ = code_digest(ROOT)
    code_unchanged = current_code_sha == sealed["code_sha256"]

    if sha256_file(args.candidate_key) != sealed["private_key_commitment_sha256"]:
        raise RuntimeError("Candidate reveal key does not match the pre-seal commitment.")

    obs = json_load(args.sealed_root / "blind_observables.json")
    candidates = json_load(args.sealed_root / "candidates/blind_candidate_observables.json")
    candidate_by_label = {r["candidate"]: r for r in candidates["records"]}
    mapping = {r["knot_type_claim"]: r for r in key["records"]}

    std = float(cfg["comparison_thresholds"]["standard_abs"])
    cert = float(cfg["comparison_thresholds"]["certified_abs"])
    hyp = reveal.get("hypotheses", {})
    comparisons = {}

    knot_type = hyp.get("carrier_knot_type")
    if knot_type is None:
        comparisons["carrier_knot_type"] = {"status": "NOT_SPECIFIED"}
    elif str(knot_type) not in mapping:
        comparisons["carrier_knot_type"] = {
            "status": "NO_MATCH",
            "reason": "Revealed knot type is not present in the pre-generated blind catalog.",
        }
    else:
        info = mapping[str(knot_type)]
        label = info["label"]
        comparisons["carrier_knot_type"] = {
            "status": "CATALOG_IDENTIFICATION_ONLY",
            "anonymous_candidate": label,
            "catalog_claim": str(knot_type),
            "independently_certified": bool(info.get("independently_certified", False)),
            "blind_observables": candidate_by_label.get(label),
            "reason": "The catalog identity was hidden during the blind run, but the generator claim is not an independent knot certificate.",
        }

    expected_q = hyp.get("expected_hopf_charge")
    q_spin = obs["blind_evidence"]["H0_H4"]["H1_spinor"]["q_hopf"]
    q_dir = obs["blind_evidence"]["H0_H4"]["H1_director"]["q_hopf"]
    if expected_q is None:
        comparisons["hopf_charge"] = {"status": "NOT_SPECIFIED"}
    else:
        e_spin = abs(float(q_spin) - float(expected_q))
        e_dir = abs(float(q_dir) - float(expected_q))
        c_spin = classify_abs(e_spin, std, cert)
        c_dir = classify_abs(e_dir, std, cert)
        if c_spin == "CERTIFIED_MATCH" and c_dir == "CERTIFIED_MATCH":
            joint = "CERTIFIED_MATCH"
        elif c_spin != "NO_MATCH" and c_dir != "NO_MATCH":
            joint = "MATCH"
        elif c_spin != "NO_MATCH" or c_dir != "NO_MATCH":
            joint = "PARTIAL_MATCH"
        else:
            joint = "NO_MATCH"
        comparisons["hopf_charge"] = {
            "status": joint,
            "expected": expected_q,
            "spinor": {"value": q_spin, "abs_error": e_spin, "classification": c_spin},
            "director": {"value": q_dir, "abs_error": e_dir, "classification": c_dir},
            "thresholds_pre_registered": {"standard_abs": std, "certified_abs": cert},
        }

    expected_sl = hyp.get("expected_self_link_proxy")
    if expected_sl is None:
        comparisons["self_link_proxy"] = {"status": "NOT_SPECIFIED"}
    elif knot_type is None or str(knot_type) not in mapping:
        comparisons["self_link_proxy"] = {"status": "NOT_IDENTIFIABLE", "reason": "No revealed catalog candidate."}
    else:
        label = mapping[str(knot_type)]["label"]
        value = candidate_by_label[label]["self_link_proxy"]
        err = abs(float(value) - float(expected_sl))
        comparisons["self_link_proxy"] = {
            "status": classify_abs(err, std, cert),
            "anonymous_candidate": label,
            "value": value,
            "expected": expected_sl,
            "abs_error": err,
            "thresholds_pre_registered": {"standard_abs": std, "certified_abs": cert},
        }

    expected_h = hyp.get("expected_helicity_ratio")
    comparisons["helicity_ratio"] = (
        {"status": "NOT_SPECIFIED"} if expected_h is None else {
            "status": "NOT_IDENTIFIABLE_FROM_BLIND_PHYSICAL_DATA",
            "expected": expected_h,
            "reason": "Blind H5 is deliberately only a constructed identity self-test; no independent SST velocity/vorticity fields were allowed.",
        }
    )

    spin_k = hyp.get("spin_sector_k")
    comparisons["spin_sector_k"] = (
        {"status": "NOT_SPECIFIED"} if spin_k is None else {
            "status": "NOT_IDENTIFIABLE_FROM_BLIND_DATA",
            "expected": spin_k,
            "reason": "H6-H8 were intentionally excluded from the blind physical evidence because they require an independently derived action and sector rule.",
        }
    )

    req4 = hyp.get("requires_4pi_spinor_kinematics")
    h9 = obs.get("self_tests_excluded_from_blind_physical_evidence", {}).get("H9_double_cover", {})
    if req4 is None:
        comparisons["four_pi"] = {"status": "NOT_SPECIFIED"}
    elif bool(req4):
        algebraic = bool(h9.get("residuals", {}).get("algebraic_double_cover_pass", False))
        comparisons["four_pi"] = {
            "status": "KINEMATIC_MATCH_ONLY" if algebraic else "NO_MATCH",
            "reason": "This compares SU(2) double-cover kinematics only; it does not certify the physical SST configuration-space topology.",
        }
    else:
        comparisons["four_pi"] = {"status": "NOT_APPLICABLE"}

    args.output.mkdir(parents=True, exist_ok=True)
    payload = {
        "campaign_id": sealed["campaign_id"],
        "model_name": reveal.get("model_name", "unspecified"),
        "revealed_utc": datetime.now(timezone.utc).isoformat(),
        "seal_verified": True,
        "blind_result_tree_sha256": sealed["result_tree_sha256"],
        "candidate_key_commitment_verified": True,
        "code_unchanged_since_seal": code_unchanged,
        "reveal_input_sha256": sha256_file(args.reveal),
        "comparisons": comparisons,
        "physical_inputs_recorded_post_seal": reveal.get("physical_inputs", {}),
        "hypothesis_provenance": reveal.get("hypothesis_provenance", {}),
        "comparison_semantics": {
            "hopf_charge": "Compatibility with a mathematical Hopf benchmark; not an SST physical derivation.",
            "candidate_geometry": "Blind geometric comparison; catalog generator claims are not independent knot certificates.",
            "H5": "Identity self-test excluded from physical evidence.",
            "H9": "SU(2) kinematic self-test only.",
        },
    }
    json_dump(args.output / "comparison.json", payload)

    lines = [
        "# Blind → Reveal comparison",
        "",
        f"- Campaign: `{sealed['campaign_id']}`",
        f"- Model: `{payload['model_name']}`",
        f"- Seal verified: **yes**",
        f"- Candidate-key commitment verified: **yes**",
        f"- Code unchanged since seal: **{'yes' if code_unchanged else 'no'}**",
        "",
        "## Comparison statuses",
        "",
    ]
    for name, result in comparisons.items():
        lines.append(f"- **{name}**: `{result.get('status')}`")
    lines += [
        "",
        "## Epistemic guard",
        "",
        "A catalog identity is not an independent knot certificate. H5 identity self-tests and H9 SU(2) kinematic self-tests are not promoted to physical SST evidence. H6-H8 remain unidentifiable unless independent post-blind physical inputs are supplied in a separate, explicitly non-blind stage.",
        "",
    ]
    (args.output / "CONCLUSIONS.md").write_text("\n".join(lines), encoding="utf-8")

    print("REVEAL COMPARISON COMPLETE")
    for name, result in comparisons.items():
        print(f"{name}: {result.get('status')}")
    print(args.output.resolve())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
