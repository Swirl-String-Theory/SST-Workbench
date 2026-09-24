#!/usr/bin/env python3
"""
Upgrade an SST independent-calibration plan to a harness-ready v2 design.

Two-stage workflow
------------------
1. Generate a draft design and a results CSV template.
2. Fill the CSV with independent microscopic response residuals and uncertainties.
3. Merge and finalize to a calibration JSON accepted by
   sst_minimal_falsification.py.

No alpha-derived quantity is allowed in the calibration evidence. The final
alpha comparison remains in the falsification harness only.

Dependencies
------------
Python >= 3.10
numpy >= 1.24
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np


FORBIDDEN_EVIDENCE_TOKENS = (
    "alpha",
    "fine-structure",
    "fine structure",
    "137.035999",
    "elementary charge",
    "electron charge",
    "e^2",
    "e²",
    "1.09384563e6",
    "1.09384563×10^6",
)


def fail(message: str) -> "NoReturn":
    raise RuntimeError(message)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        doc = json.load(f)
    if not isinstance(doc, dict):
        fail(f"{path}: expected a JSON object")
    return doc


def find_campaign(plan: dict[str, Any], campaign_id: str) -> dict[str, Any]:
    for campaign in plan.get("campaigns", []):
        if campaign.get("id") == campaign_id:
            return campaign
    fail(f"Plan does not contain campaign {campaign_id}")


def list_parameter(campaign: dict[str, Any], name: str) -> list[float]:
    value = campaign.get("parameters", {}).get(name)
    if not isinstance(value, list) or not value:
        fail(f"{campaign.get('id')}: expected nonempty list parameter {name}")
    return [float(x) for x in value]


def scalar_parameter(campaign: dict[str, Any], name: str) -> float:
    value = campaign.get("parameters", {}).get(name)
    if value is None or isinstance(value, list):
        fail(f"{campaign.get('id')}: expected scalar parameter {name}")
    return float(value)


def circular_ring_features(R_over_D: float, omega_hat: float = 0.0) -> dict[str, float]:
    if R_over_D <= 0:
        fail("R_over_D must be positive")
    L_D = 2.0 * math.pi * R_over_D
    bend = 2.0 * math.pi / R_over_D
    twist = (omega_hat * omega_hat) * L_D
    return {
        "L_D": L_D,
        "bend": bend,
        "twist": twist,
        "contact": 0.0,
    }


def straight_periodic_twist_features(
    period_length_over_D: float,
    omega_hat: float,
) -> dict[str, float]:
    if period_length_over_D <= 0:
        fail("period_length_over_D must be positive")
    return {
        "L_D": period_length_over_D,
        "bend": 0.0,
        "twist": omega_hat * omega_hat * period_length_over_D,
        "contact": 0.0,
    }


def core_overlap_factor(profile: str, gaussian_width: float) -> float:
    if profile == "unit":
        return 1.0
    if profile == "gaussian":
        if gaussian_width <= 0:
            fail("gaussian_width must be positive")
        return math.exp(-1.0 / (4.0 * gaussian_width * gaussian_width))
    if profile == "tophat":
        # Exactly tangent compact-support disks have zero volumetric overlap.
        return 0.0
    fail(f"Unknown core profile: {profile}")


def antiparallel_periodic_contact_proxy(
    separation_over_D: float,
    period_length_over_D: float,
    shell_sigma: float,
    orth_tol: float,
    profile: str,
    gaussian_width: float,
    quadrature_points: int,
) -> float:
    """
    Cross-component version of the contact-shell proxy used by the harness.

    For two antiparallel periodic straight tubes, parameterized by u and v,
    the pair separation depends on w = |u-v|:

        R(w) = sqrt(d^2 + w^2).

    The feature is the one-count cross-pair integral

        C = 2 integral_0^L (L-w) K(w,d) dw,

    with the same radial shell and tangent/chord orthogonality weights used by
    the centerline extractor.
    """
    d = float(separation_over_D)
    length = float(period_length_over_D)
    if d <= 0 or length <= 0:
        fail("Contact separation and period length must be positive")
    if shell_sigma <= 0 or orth_tol <= 0:
        fail("Contact shell and orthogonality tolerances must be positive")
    n = max(1001, int(quadrature_points))
    w = np.linspace(0.0, length, n)
    R = np.sqrt(d * d + w * w)
    shell = np.exp(-((R - 1.0) ** 2) / (2.0 * shell_sigma * shell_sigma))
    # For antiparallel tangents, |Rhat.t_i| = |Rhat.t_j| = w/R.
    orth = np.exp(-(w * w) / (R * R * orth_tol * orth_tol))
    kernel = shell * orth
    integral = 2.0 * np.trapezoid((length - w) * kernel, w)
    return float(integral * core_overlap_factor(profile, gaussian_width))


def antiparallel_periodic_features(
    separation_over_D: float,
    period_length_over_D: float,
    shell_sigma: float,
    orth_tol: float,
    profile: str,
    gaussian_width: float,
    quadrature_points: int,
) -> dict[str, float]:
    return {
        "L_D": 2.0 * period_length_over_D,
        "bend": 0.0,
        "twist": 0.0,
        "contact": antiparallel_periodic_contact_proxy(
            separation_over_D=separation_over_D,
            period_length_over_D=period_length_over_D,
            shell_sigma=shell_sigma,
            orth_tol=orth_tol,
            profile=profile,
            gaussian_width=gaussian_width,
            quadrature_points=quadrature_points,
        ),
    }


def make_row(
    row_id: str,
    role: str,
    observable: str,
    geometry: str,
    parameters: dict[str, Any],
    features: dict[str, float],
    feature_derivation: str,
) -> dict[str, Any]:
    return {
        "id": row_id,
        "role": role,
        "observable": observable,
        "value": None,
        "sigma": None,
        "features": {
            "bend": float(features["bend"]),
            "twist": float(features["twist"]),
            "contact": float(features["contact"]),
        },
        "geometry": {
            "description": geometry,
            "parameters": parameters,
            "L_D_for_response_subtraction": float(features["L_D"]),
        },
        "feature_derivation": feature_derivation,
        "provenance": {
            "source": None,
            "derivation": None,
            "used_constants": [],
        },
        "completion_status": "NEEDS_INDEPENDENT_RESPONSE_RESULT",
    }


def build_draft(plan: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    schema = str(plan.get("schema", ""))
    if not schema.startswith("sst.independent-calibration-plan"):
        fail("Input is not an SST independent-calibration plan")

    bend_campaign = find_campaign(plan, "CAL-BEND")
    twist_campaign = find_campaign(plan, "CAL-TWIST")
    contact_campaign = find_campaign(plan, "CAL-CONTACT")
    mixed_campaign = find_campaign(plan, "HOLD-MIXED-1")

    rows: list[dict[str, Any]] = []

    for R_over_D in list_parameter(bend_campaign, "R_over_D"):
        features = circular_ring_features(R_over_D)
        rows.append(
            make_row(
                row_id=f"CAL-BEND-R{R_over_D:g}",
                role="calibration",
                observable="renormalized microscopic transverse-response residual",
                geometry="isolated circular finite-core vortex ring",
                parameters={"R_over_D": R_over_D},
                features=features,
                feature_derivation=(
                    "For a circle: L_D=2*pi*(R/D), "
                    "I_kappa2=2*pi/(R/D), I_Omega2=0, C_contact=0."
                ),
            )
        )

    for omega_hat in list_parameter(twist_campaign, "D_Omega3"):
        features = straight_periodic_twist_features(
            args.period_length_over_D, omega_hat
        )
        rows.append(
            make_row(
                row_id=f"CAL-TWIST-W{omega_hat:g}",
                role="calibration",
                observable="renormalized microscopic transverse-response residual",
                geometry="straight finite-core tube with periodic axial boundary",
                parameters={
                    "period_length_over_D": args.period_length_over_D,
                    "D_Omega3": omega_hat,
                },
                features=features,
                feature_derivation=(
                    "For a straight periodic tube: I_kappa2=0, "
                    "I_Omega2=(D*Omega3)^2*(L/D), C_contact=0."
                ),
            )
        )

    for separation in list_parameter(contact_campaign, "separation_over_D"):
        features = antiparallel_periodic_features(
            separation_over_D=separation,
            period_length_over_D=args.contact_period_length_over_D,
            shell_sigma=args.contact_shell_sigma,
            orth_tol=args.orth_tol,
            profile=args.core_profile,
            gaussian_width=args.gaussian_width,
            quadrature_points=args.quadrature_points,
        )
        rows.append(
            make_row(
                row_id=f"CAL-CONTACT-D{separation:g}",
                role="calibration",
                observable="renormalized microscopic two-tube response residual",
                geometry="two antiparallel finite-core tubes with periodic axial boundary",
                parameters={
                    "separation_over_D": separation,
                    "period_length_over_D": args.contact_period_length_over_D,
                    "contact_shell_sigma": args.contact_shell_sigma,
                    "orthogonality_tolerance": args.orth_tol,
                    "core_profile": args.core_profile,
                    "gaussian_sigma_over_D": (
                        args.gaussian_width
                        if args.core_profile == "gaussian"
                        else None
                    ),
                },
                features=features,
                feature_derivation=(
                    "Cross-component contact proxy: "
                    "2*integral_0^L (L-w) K(w,d) dw with the declared "
                    "radial-shell and chord-orthogonality weights."
                ),
            )
        )

    R_hold = scalar_parameter(mixed_campaign, "R_over_D")
    W_hold = scalar_parameter(mixed_campaign, "D_Omega3")
    features = circular_ring_features(R_hold, W_hold)
    rows.append(
        make_row(
            row_id="HOLD-MIXED-TWISTED-RING",
            role="holdout",
            observable="renormalized microscopic transverse-response residual",
            geometry="twisted circular finite-core vortex ring",
            parameters={"R_over_D": R_hold, "D_Omega3": W_hold},
            features=features,
            feature_derivation=(
                "I_kappa2=2*pi/(R/D); "
                "I_Omega2=(D*Omega3)^2*2*pi*(R/D); C_contact=0."
            ),
        )
    )

    # A genuine contact interpolation holdout with a separation not used in fit.
    hold_sep = args.contact_holdout_separation_over_D
    features = antiparallel_periodic_features(
        separation_over_D=hold_sep,
        period_length_over_D=args.contact_holdout_length_over_D,
        shell_sigma=args.contact_shell_sigma,
        orth_tol=args.orth_tol,
        profile=args.core_profile,
        gaussian_width=args.gaussian_width,
        quadrature_points=args.quadrature_points,
    )
    rows.append(
        make_row(
            row_id="HOLD-CONTACT-INTERPOLATION",
            role="holdout",
            observable="renormalized microscopic two-tube response residual",
            geometry="antiparallel periodic tube pair at unseen separation and length",
            parameters={
                "separation_over_D": hold_sep,
                "period_length_over_D": args.contact_holdout_length_over_D,
                "contact_shell_sigma": args.contact_shell_sigma,
                "orthogonality_tolerance": args.orth_tol,
                "core_profile": args.core_profile,
            },
            features=features,
            feature_derivation=(
                "Same frozen contact feature definition as CAL-CONTACT, "
                "evaluated at a separation and period length excluded from fitting."
            ),
        )
    )

    return {
        "schema": "sst.calibration-draft.v2",
        "ready_for_harness": False,
        "model": {
            "features": ["bend", "twist", "contact"],
            "equation": (
                "Delta = c_kappa*I_kappa2 + "
                "c_Omega*I_Omega2 + c_C*C_contact"
            ),
            "renormalization_condition": "c_L = 0",
            "forbidden_removed_feature": "length",
        },
        "response_definition": {
            "calibration_value": (
                "value = R_micro - (8*pi/3)*L_D_for_response_subtraction"
            ),
            "allowed_alternative": (
                "A solver may output the same renormalized residual directly."
            ),
            "boundary_requirement": (
                "Periodic or closed geometries must use the declared total L_D."
            ),
        },
        "normalization": plan.get("normalization", {}),
        "contact_feature_definition": {
            "shell_sigma": args.contact_shell_sigma,
            "orthogonality_tolerance": args.orth_tol,
            "core_profile": args.core_profile,
            "gaussian_sigma_over_D": (
                args.gaussian_width if args.core_profile == "gaussian" else None
            ),
            "quadrature_points": args.quadrature_points,
        },
        "rules": {
            "target_coupling_may_be_used_in_calibration": False,
            "target_correction_may_be_used_in_calibration": False,
            "elementary_charge_may_be_used_in_calibration": False,
            "alpha_calibrated_swirl_speed_may_be_used_in_calibration": False,
            "coefficients_are_frozen_before_trefoil_test": True,
            "all_null_values_must_be_replaced_before_finalization": True,
        },
        "rows": rows,
        "source_plan": {
            "schema": plan.get("schema"),
            "status": plan.get("status"),
            "minimum_gates": plan.get("minimum_gates", []),
        },
    }


def write_results_template(draft: dict[str, Any], path: Path) -> None:
    fields = [
        "id",
        "role",
        "value",
        "R_micro",
        "sigma",
        "source",
        "derivation",
        "used_constants",
        "notes",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in draft["rows"]:
            writer.writerow(
                {
                    "id": row["id"],
                    "role": row["role"],
                    "value": "",
                    "R_micro": "",
                    "sigma": "",
                    "source": "",
                    "derivation": "",
                    "used_constants": "",
                    "notes": (
                        "Provide value directly, or provide R_micro and let the "
                        "upgrader subtract (8*pi/3)*L_D."
                    ),
                }
            )


def parse_used_constants(raw: str) -> list[str]:
    raw = raw.strip()
    if not raw:
        return []
    return [part.strip() for part in re.split(r"[;|]", raw) if part.strip()]


def load_results(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        required = {"id", "value", "R_micro", "sigma", "source", "derivation", "used_constants"}
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            fail(
                f"{path}: expected columns {sorted(required)}; "
                f"found {reader.fieldnames}"
            )
        rows: dict[str, dict[str, str]] = {}
        for row in reader:
            row_id = (row.get("id") or "").strip()
            if not row_id:
                continue
            if row_id in rows:
                fail(f"Duplicate result id: {row_id}")
            rows[row_id] = row
    return rows


def evidence_text(row: dict[str, Any]) -> str:
    provenance = row.get("provenance", {})
    parts = [
        str(provenance.get("source", "")),
        str(provenance.get("derivation", "")),
        " ".join(str(x) for x in provenance.get("used_constants", [])),
    ]
    return "\n".join(parts).lower()


def leakage_findings(row: dict[str, Any]) -> list[str]:
    text = evidence_text(row)
    for declaration in (
        "alpha-independent",
        "alpha independent",
        "without alpha",
        "does not use alpha",
        "not using alpha",
    ):
        text = text.replace(declaration, "")
    findings = []
    for token in FORBIDDEN_EVIDENCE_TOKENS:
        if token.lower() in text:
            findings.append(token)
    return sorted(set(findings))


def merge_results(
    draft: dict[str, Any],
    results: dict[str, dict[str, str]],
    allow_missing_holdouts: bool,
) -> dict[str, Any]:
    expected_ids = {row["id"] for row in draft["rows"]}
    unknown = sorted(set(results) - expected_ids)
    if unknown:
        fail(f"Results CSV contains unknown row ids: {unknown}")

    merged = json.loads(json.dumps(draft))
    missing: list[str] = []

    for row in merged["rows"]:
        result = results.get(row["id"])
        if result is None:
            if row["role"] == "holdout" and allow_missing_holdouts:
                continue
            missing.append(row["id"])
            continue

        value_raw = (result.get("value") or "").strip()
        response_raw = (result.get("R_micro") or "").strip()
        sigma_raw = (result.get("sigma") or "").strip()

        if value_raw:
            value = float(value_raw)
        elif response_raw:
            response = float(response_raw)
            L_D = float(row["geometry"]["L_D_for_response_subtraction"])
            value = response - (8.0 * math.pi / 3.0) * L_D
        else:
            if row["role"] == "holdout" and allow_missing_holdouts:
                continue
            missing.append(row["id"])
            continue

        if not sigma_raw:
            if row["role"] == "holdout" and allow_missing_holdouts:
                continue
            missing.append(row["id"])
            continue
        sigma = float(sigma_raw)
        if not np.isfinite(value):
            fail(f"{row['id']}: non-finite value")
        if not np.isfinite(sigma) or sigma <= 0:
            fail(f"{row['id']}: sigma must be finite and positive")

        source = (result.get("source") or "").strip()
        derivation = (result.get("derivation") or "").strip()
        used_constants = parse_used_constants(result.get("used_constants") or "")
        if not source or not derivation:
            fail(f"{row['id']}: source and derivation are required")

        row["value"] = value
        row["sigma"] = sigma
        row["provenance"] = {
            "source": source,
            "derivation": derivation,
            "used_constants": used_constants,
            "notes": (result.get("notes") or "").strip(),
        }
        row["completion_status"] = "COMPLETE"

        findings = leakage_findings(row)
        if findings:
            fail(
                f"{row['id']}: forbidden calibration evidence tokens: "
                + ", ".join(findings)
            )

    if missing:
        fail(
            "Missing value/sigma/result rows: "
            + ", ".join(sorted(set(missing)))
        )

    calibration_rows = [r for r in merged["rows"] if r["role"] == "calibration"]
    p = len(merged["model"]["features"])
    if len(calibration_rows) < p + 1:
        fail(f"Need at least p+1 calibration rows; got {len(calibration_rows)} for p={p}")

    A = np.asarray(
        [
            [float(row["features"][name]) for name in merged["model"]["features"]]
            for row in calibration_rows
        ],
        dtype=float,
    )
    rank = int(np.linalg.matrix_rank(A))
    singular = np.linalg.svd(A, compute_uv=False)
    condition = (
        math.inf
        if singular[-1] <= 0
        else float(singular[0] / singular[-1])
    )
    if rank != p:
        fail(f"Final calibration design is rank deficient: rank={rank}, required={p}")

    merged["schema"] = "sst.calibration.v1"
    merged["ready_for_harness"] = True
    merged["design_diagnostics"] = {
        "calibration_rows": len(calibration_rows),
        "coefficient_count": p,
        "rank": rank,
        "condition_number_unweighted": condition,
    }
    return merged


def sanitize_old_calibration(old: dict[str, Any]) -> dict[str, Any]:
    """
    Remove the degenerate length feature from a legacy calibration JSON.

    This does not invent missing campaigns or values. It is useful for preserving
    already-computed non-length rows before merging them into a v2 draft.
    """
    rows = old.get("rows")
    if not isinstance(rows, list):
        fail("Legacy calibration has no rows list")
    sanitized = json.loads(json.dumps(old))
    sanitized.setdefault("model", {})["features"] = ["bend", "twist", "contact"]
    sanitized["model"]["renormalization_condition"] = "c_L = 0"
    sanitized["model"]["legacy_length_feature_removed"] = True
    for row in sanitized["rows"]:
        features = row.get("features", {})
        features.pop("length", None)
        for required in ("bend", "twist", "contact"):
            features.setdefault(required, 0.0)
        row["features"] = features
    sanitized["schema"] = "sst.calibration-legacy-sanitized.v2"
    sanitized["ready_for_harness"] = False
    return sanitized


def command_generate(args: argparse.Namespace) -> None:
    plan = load_json(Path(args.plan))
    draft = build_draft(plan, args)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(draft, indent=2), encoding="utf-8")
    results_template = Path(args.results_template)
    write_results_template(draft, results_template)
    print(f"Draft calibration: {output}")
    print(f"Results template:  {results_template}")
    print(f"Rows: {len(draft['rows'])}")


def command_finalize(args: argparse.Namespace) -> None:
    draft = load_json(Path(args.draft))
    results = load_results(Path(args.results))
    merged = merge_results(
        draft=draft,
        results=results,
        allow_missing_holdouts=args.allow_missing_holdouts,
    )
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    print(f"Harness-ready calibration: {output}")
    print(json.dumps(merged["design_diagnostics"], indent=2))


def command_sanitize(args: argparse.Namespace) -> None:
    old = load_json(Path(args.input))
    sanitized = sanitize_old_calibration(old)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(sanitized, indent=2), encoding="utf-8")
    print(f"Sanitized legacy calibration: {output}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate and finalize SST independent-calibration JSON v2."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_generate = sub.add_parser(
        "generate",
        help="Expand the research plan into concrete calibration and holdout rows",
    )
    p_generate.add_argument("--plan", required=True)
    p_generate.add_argument("--out", default="calibration_v2_draft.json")
    p_generate.add_argument(
        "--results-template",
        default="calibration_results_template.csv",
    )
    p_generate.add_argument("--period-length-over-D", type=float, default=10.0)
    p_generate.add_argument(
        "--contact-period-length-over-D",
        type=float,
        default=10.0,
    )
    p_generate.add_argument("--contact-shell-sigma", type=float, default=0.08)
    p_generate.add_argument("--orth-tol", type=float, default=0.12)
    p_generate.add_argument(
        "--core-profile",
        choices=["unit", "gaussian", "tophat"],
        default="unit",
    )
    p_generate.add_argument("--gaussian-width", type=float, default=0.25)
    p_generate.add_argument("--quadrature-points", type=int, default=20001)
    p_generate.add_argument(
        "--contact-holdout-separation-over-D",
        type=float,
        default=1.075,
    )
    p_generate.add_argument(
        "--contact-holdout-length-over-D",
        type=float,
        default=7.5,
    )
    p_generate.set_defaults(func=command_generate)

    p_finalize = sub.add_parser(
        "finalize",
        help="Merge independent response results and emit harness-ready JSON",
    )
    p_finalize.add_argument("--draft", required=True)
    p_finalize.add_argument("--results", required=True)
    p_finalize.add_argument("--out", default="calibration_filled_v2.json")
    p_finalize.add_argument(
        "--allow-missing-holdouts",
        action="store_true",
        help="Allow finalization before holdout results are available",
    )
    p_finalize.set_defaults(func=command_finalize)

    p_sanitize = sub.add_parser(
        "sanitize-legacy",
        help="Remove the degenerate length feature from an old calibration JSON",
    )
    p_sanitize.add_argument("--input", required=True)
    p_sanitize.add_argument("--out", default="calibration_legacy_sanitized_v2.json")
    p_sanitize.set_defaults(func=command_sanitize)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
        return 0
    except (RuntimeError, ValueError, KeyError, np.linalg.LinAlgError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
