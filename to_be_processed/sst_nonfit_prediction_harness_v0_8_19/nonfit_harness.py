#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

FLOAT_RE = r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?"
PI = math.pi

STATUS_DERIVED = "DERIVED"
STATUS_CALIBRATED = "CALIBRATED"
STATUS_RESEARCH = "RESEARCH_TRACK"
STATUS_FAILED = "FAILED"
STATUS_NA = "NOT_AVAILABLE"


@dataclass(frozen=True)
class Constants:
    c_m_s: float = 299792458.0
    v_swirl_m_s: float = 1.09384563e6
    r_c_m: float = 1.40897017e-15
    rho_f_kg_m3: float = 7.0e-7
    rho_core_kg_m3: float = 3.8934358266918687e18
    m_e_kg_evaluation_only: float = 9.1093837015e-31
    alpha_evaluation_only: float = 0.0072973525643

    @property
    def lambda_c_from_closure_m(self) -> float:
        # SST closure identity: lambda_c = 2*pi*c*r_c / v_swirl.
        return 2.0 * PI * self.c_m_s * self.r_c_m / self.v_swirl_m_s

    @property
    def alpha_gate_predicted(self) -> float:
        # lambda_c/(pi*r_c) = 2c/v_swirl = 4/alpha in the geometric gate convention.
        return self.lambda_c_from_closure_m / (PI * self.r_c_m)

    @property
    def gamma_0_m2_s(self) -> float:
        return 2.0 * PI * self.r_c_m * self.v_swirl_m_s


def load_json(path: str | Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, payload: Dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, indent=2, sort_keys=False), encoding="utf-8")


def write_gate_csv(path: str | Path, gates: Dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["gate", "status", "summary", "primary_residual", "notes"])
        w.writeheader()
        for name, g in gates.items():
            w.writerow({
                "gate": name,
                "status": g.get("status"),
                "summary": g.get("summary", ""),
                "primary_residual": g.get("primary_residual", ""),
                "notes": g.get("notes", ""),
            })


def relerr(x: Optional[float], y: Optional[float]) -> Optional[float]:
    if x is None or y is None or y == 0.0:
        return None
    return abs(x - y) / abs(y)


def _attr(text: str, name: str) -> Optional[str]:
    m = re.search(rf'{name}="([^"]*)"', text)
    return m.group(1).strip() if m else None


def _parse_vec(text: str) -> Tuple[float, float, float]:
    vals = [float(v) for v in re.findall(FLOAT_RE, text)]
    if len(vals) != 3:
        raise ValueError(f"Expected 3-vector, got {text!r}")
    return vals[0], vals[1], vals[2]


def load_ideal_coeffs(path: str | Path, knot_id: str) -> Optional[Dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))
    text = p.read_text(encoding="utf-8", errors="replace")
    m = re.search(rf'(<AB\s+[^>]*Id="{re.escape(knot_id)}"[^>]*>)(.*?)(</AB>)', text, flags=re.S)
    if not m:
        return None
    header, body = m.group(1), m.group(2)
    coeffs = []
    for cm in re.finditer(r'<Coeff\s+([^>]*)/>', body):
        attrs = cm.group(1)
        i_s = _attr(attrs, "I")
        a_s = _attr(attrs, "A")
        b_s = _attr(attrs, "B")
        if i_s is None or a_s is None or b_s is None:
            continue
        coeffs.append((int(i_s), _parse_vec(a_s), _parse_vec(b_s)))
    coeffs.sort(key=lambda x: x[0])
    return {
        "knot_id": knot_id,
        "conway": _attr(header, "Conway"),
        "declared_L": float(_attr(header, "L")) if _attr(header, "L") is not None else None,
        "declared_D": float(_attr(header, "D")) if _attr(header, "D") is not None else None,
        "coeffs": coeffs,
    }


def sample_fourier(coeffs: List[Tuple[int, Tuple[float, float, float], Tuple[float, float, float]]], n: int) -> List[Tuple[float, float, float]]:
    if n < 8:
        raise ValueError("n must be >= 8")
    pts: List[Tuple[float, float, float]] = []
    for k in range(n):
        t = 2.0 * PI * k / n
        x = y = z = 0.0
        for i, a, b in coeffs:
            ct = math.cos(i * t)
            st = math.sin(i * t)
            x += ct * a[0] + st * b[0]
            y += ct * a[1] + st * b[1]
            z += ct * a[2] + st * b[2]
        pts.append((x, y, z))
    return pts


def closed_polyline_length(points: List[Tuple[float, float, float]]) -> float:
    total = 0.0
    n = len(points)
    for i in range(n):
        a = points[i]
        b = points[(i + 1) % n]
        total += math.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2 + (b[2] - a[2]) ** 2)
    return total


def infer_ropelength(knot: Dict[str, Any], ideal_path: Optional[str], knot_id: str, n: int) -> Tuple[float, Dict[str, Any]]:
    source = {"source": "manifest_fallback"}
    fallback = knot.get("ropelength_Ltot_fallback")
    if ideal_path:
        ideal = load_ideal_coeffs(ideal_path, knot_id)
        if ideal is None:
            return float(fallback), {"source": "manifest_fallback_after_missing_ideal_id", "ideal_path": ideal_path}
        if ideal.get("declared_L") is not None:
            return float(ideal["declared_L"]), {"source": "ideal_txt_declared_L", "ideal_path": ideal_path, "declared_D": ideal.get("declared_D")}
        pts = sample_fourier(ideal["coeffs"], n)
        return closed_polyline_length(pts), {"source": "ideal_txt_sampled_polyline", "ideal_path": ideal_path, "sample_N": n}
    if fallback is None:
        raise ValueError(f"No ropelength source for knot_id={knot_id!r}")
    return float(fallback), source


def geometric_baseline_mass(constants: Constants, Ltot: float, rho_m_kg_m3: Optional[float] = None) -> float:
    rho_m = constants.rho_core_kg_m3 if rho_m_kg_m3 is None else rho_m_kg_m3
    lam = constants.lambda_c_from_closure_m
    return 2.0 * PI**3 * rho_m * constants.r_c_m**5 / (lam**2) * Ltot


def gate_mass_kernel(constants: Constants, knot: Dict[str, Any], Ltot: float, used_as_inputs: List[str], tol: Dict[str, float]) -> Dict[str, Any]:
    G = int(knot.get("exposure_gate_G", 0))
    Xi = knot.get("topology_kernel_Xi")
    kernel_status = knot.get("topology_kernel_status", STATUS_RESEARCH)
    baseline_m = geometric_baseline_mass(constants, Ltot)
    gate = constants.alpha_gate_predicted
    predicted_m = None if Xi is None else (gate**G) * float(Xi) * baseline_m
    target_m = knot.get("evaluation_targets", {}).get("mass_kg")
    target_e = knot.get("evaluation_targets", {}).get("energy_j")
    required_Xi_for_target = None
    if target_m is not None:
        denom = (gate**G) * baseline_m
        if denom != 0.0:
            required_Xi_for_target = float(target_m) / denom
    mass_res = relerr(predicted_m, target_m) if predicted_m is not None and target_m is not None else None

    if "posthoc_topology_kernel" in used_as_inputs:
        status = STATUS_FAILED
        summary = "Topology kernel was supplied post-hoc; non-fitted closure violated."
    elif Xi is None:
        status = STATUS_RESEARCH
        summary = "No predeclared topology kernel; reports required kernel but does not use it."
    elif kernel_status == STATUS_DERIVED:
        status = STATUS_DERIVED if (mass_res is None or mass_res <= tol.get("mass_rel_tol", 1e-3)) else STATUS_FAILED
        summary = "Predeclared derived topology kernel evaluated."
    elif kernel_status == STATUS_CALIBRATED:
        status = STATUS_CALIBRATED
        summary = "Predeclared calibrated topology kernel evaluated."
    else:
        status = STATUS_RESEARCH
        summary = "Predeclared topology kernel exists but is not marked DERIVED."

    return {
        "status": status,
        "summary": summary,
        "equations": {
            "lambda_c_closure": "lambda_c = 2*pi*c*r_c/v_swirl",
            "baseline_mass": "M0 = 2*pi^3*rho_m*r_c^5*Ltot/lambda_c^2",
            "prediction": "M = (lambda_c/(pi*r_c))^G * Xi_K * M0"
        },
        "inputs": {"Ltot": Ltot, "exposure_gate_G": G, "topology_kernel_Xi": Xi, "kernel_status": kernel_status},
        "computed": {
            "lambda_c_from_closure_m": constants.lambda_c_from_closure_m,
            "alpha_gate_predicted_lambda_over_pi_rc": gate,
            "baseline_mass_kg_Xi1_G0": baseline_m,
            "predicted_mass_kg": predicted_m,
            "predicted_energy_j": None if predicted_m is None else predicted_m * constants.c_m_s**2,
            "target_mass_kg_evaluation_only": target_m,
            "target_energy_j_evaluation_only": target_e,
            "mass_rel_error_if_target_available": mass_res,
            "required_Xi_for_target_not_used": required_Xi_for_target,
            "dimension_check": "rho_m[kg m^-3] * r_c^5/lambda_c^2[m^3] -> kg"
        },
        "primary_residual": mass_res,
        "notes": "A required_Xi value is diagnostic only; using it as input sets gate status FAILED."
    }


def gate_protocol(protocol: Dict[str, Any], used_as_inputs: List[str], allow_calibration: bool = False) -> Dict[str, Any]:
    forbidden = set(protocol.get("forbidden_fit_inputs", []))
    forbidden_used = sorted(set(used_as_inputs) & forbidden)
    if forbidden_used and not allow_calibration:
        status = STATUS_FAILED
        summary = "Forbidden target/calibration quantities were used as prediction inputs."
    elif forbidden_used and allow_calibration:
        status = STATUS_CALIBRATED
        summary = "Forbidden quantities were used only under explicit calibration mode."
    else:
        status = STATUS_DERIVED
        summary = "Frozen-input protocol satisfied; no target residual minimized."
    return {
        "status": status,
        "summary": summary,
        "forbidden_fit_inputs": list(protocol.get("forbidden_fit_inputs", [])),
        "used_as_inputs": used_as_inputs,
        "forbidden_used": forbidden_used,
        "primary_residual": len(forbidden_used),
        "notes": "This gate only audits protocol purity; it does not certify physical correctness."
    }


def gate_spinorial(knot: Dict[str, Any]) -> Dict[str, Any]:
    sb = knot.get("spinorial_boundary", {})
    theta = sb.get("expected_theta_rad")
    derived = bool(sb.get("theta_pi_derived", False))
    declared_status = sb.get("status", STATUS_RESEARCH)
    if derived and theta is not None and abs(float(theta) - PI) < 1e-12:
        status = STATUS_DERIVED
        summary = "theta=pi boundary condition marked derived in frozen manifest."
    elif declared_status == STATUS_FAILED:
        status = STATUS_FAILED
        summary = "Frozen manifest marks spinorial boundary gate failed."
    else:
        status = STATUS_RESEARCH
        summary = "theta=pi boundary condition not yet derived; treated as research-track."
    return {
        "status": status,
        "summary": summary,
        "inputs": sb,
        "computed": {
            "theta_expected_rad": theta,
            "theta_minus_pi_abs": None if theta is None else abs(float(theta) - PI),
            "theta_pi_derived": derived,
        },
        "primary_residual": None if theta is None else abs(float(theta) - PI),
        "notes": "This gate must be promoted only by a topological boundary derivation, not by particle-label selection."
    }


def _iter_torsion_cases(node: Any, path: str = "") -> Iterable[Tuple[str, Dict[str, Any]]]:
    if isinstance(node, dict):
        if "chi_T" in node and "isotropy_residual" in node:
            yield path.rstrip("/"), node
        for k, v in node.items():
            if isinstance(v, dict):
                yield from _iter_torsion_cases(v, f"{path}/{k}")


def find_torsion_case(torsion_json: Dict[str, Any], knot_id: str, density_key: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    # Prefer exact knot-id in path and selected density key in path.
    all_cases = list(_iter_torsion_cases(torsion_json))
    for p, c in all_cases:
        if knot_id in p and density_key in p:
            return p, c
    # Common outputs label trefoil/figure-eight rather than AB id.
    aliases = {
        "3:1:1": ["3_1", "trefoil"],
        "4:1:1": ["4_1", "figure", "figure_eight"],
    }.get(knot_id, [])
    for p, c in all_cases:
        p_low = p.lower()
        if any(a.lower() in p_low for a in aliases) and density_key.lower() in p_low:
            return p, c
    # Fallback first density key.
    for p, c in all_cases:
        if density_key.lower() in p.lower():
            return p, c
    return (all_cases[0] if all_cases else (None, None))


def gate_torsion(torsion_json_path: Optional[str], knot_id: str, density_key: str, tol: Dict[str, float]) -> Dict[str, Any]:
    if torsion_json_path is None:
        return {
            "status": STATUS_NA,
            "summary": "No torsion tensor audit JSON supplied.",
            "primary_residual": None,
            "notes": "Run the standalone torsion-impedance pybind11 audit and pass --torsion-json."
        }
    data = load_json(torsion_json_path)
    path, case = find_torsion_case(data, knot_id, density_key)
    if case is None:
        return {
            "status": STATUS_NA,
            "summary": "No torsion case found in supplied JSON.",
            "source": torsion_json_path,
            "primary_residual": None,
            "notes": "Expected fields chi_T and isotropy_residual."
        }
    chi = float(case.get("chi_T"))
    iso = float(case.get("isotropy_residual"))
    chi_res = abs(chi - 1.0)
    chi_tol = tol.get("torsion_chi_rel_tol", 1e-3)
    iso_tol = tol.get("torsion_isotropy_max", 1e-2)
    if chi_res <= chi_tol and iso <= iso_tol:
        status = STATUS_DERIVED
        summary = "Core--torsion impedance residual passes configured tolerance."
    else:
        status = STATUS_FAILED
        summary = "Core--torsion impedance residual fails configured tolerance."
    return {
        "status": status,
        "summary": summary,
        "source": torsion_json_path,
        "matched_case_path": path,
        "density_key": density_key,
        "computed": case,
        "criteria": {"abs_chi_minus_one_max": chi_tol, "isotropy_residual_max": iso_tol},
        "primary_residual": chi_res,
        "notes": "Required scale/density fields are diagnostics; using them to force chi=1 violates non-fitted mode."
    }


def overall_status(gates: Dict[str, Dict[str, Any]]) -> str:
    statuses = [g.get("status") for g in gates.values()]
    if STATUS_FAILED in statuses:
        return STATUS_FAILED
    if STATUS_CALIBRATED in statuses:
        return STATUS_CALIBRATED
    if STATUS_RESEARCH in statuses or STATUS_NA in statuses:
        return STATUS_RESEARCH
    return STATUS_DERIVED


def build_report(args: argparse.Namespace) -> Dict[str, Any]:
    root = Path(__file__).parent
    protocol = load_json(args.protocol or root / "config" / "frozen_protocol.json")
    manifest = load_json(args.manifest or root / "config" / "frozen_topology_manifest.json")
    constants = Constants(**{k: v for k, v in protocol.get("canonical_constants", {}).items() if k in Constants.__dataclass_fields__})
    tol = dict(protocol.get("default_tolerances", {}))
    knots = manifest.get("knots", {})
    if args.knot_id not in knots:
        raise KeyError(f"knot_id={args.knot_id!r} not found in manifest")
    knot = knots[args.knot_id]

    used_as_inputs: List[str] = [
        "c_m_s", "v_swirl_m_s", "r_c_m", "rho_core_kg_m3", "knot_id", "ropelength_Ltot", "exposure_gate_G"
    ]
    if knot.get("topology_kernel_Xi") is not None:
        used_as_inputs.append("topology_kernel_Xi_if_predeclared")
    if args.use_required_kernel_as_input:
        used_as_inputs.append("posthoc_topology_kernel")
    if args.use_target_mass_as_input:
        used_as_inputs.append("target_mass_kg")
    if args.torsion_json:
        used_as_inputs.append("torsion_tensor_audit_json")

    Ltot, Lsrc = infer_ropelength(knot, args.ideal, args.knot_id, args.n)
    gates: Dict[str, Dict[str, Any]] = {}
    gates["i_topological_mass_kernel_closure"] = gate_mass_kernel(constants, knot, Ltot, used_as_inputs, tol)
    gates["ii_non_fitted_prediction_protocol"] = gate_protocol(protocol, used_as_inputs, allow_calibration=args.allow_calibration)
    gates["iii_spinorial_boundary_theta_pi"] = gate_spinorial(knot)
    gates["iv_core_torsion_impedance_matching"] = gate_torsion(args.torsion_json, args.knot_id, args.torsion_density_key, tol)

    report = {
        "harness": {
            "name": "sst_nonfit_prediction_harness",
            "version": protocol.get("protocol_version"),
            "epistemic_status": "RESEARCH-TRACK harness; not a canon proof.",
            "strict_nonfit": not args.allow_calibration,
        },
        "target": {
            "knot_id": args.knot_id,
            "label": knot.get("label"),
            "candidate_sector": knot.get("candidate_sector"),
            "ropelength_Ltot": Ltot,
            "ropelength_source": Lsrc,
        },
        "constants": asdict(constants),
        "dimensionless_checks": {
            "lambda_c_over_pi_r_c": constants.alpha_gate_predicted,
            "2c_over_v_swirl": 2.0 * constants.c_m_s / constants.v_swirl_m_s,
            "c_over_v_swirl": constants.c_m_s / constants.v_swirl_m_s,
            "c_over_v_swirl_squared": (constants.c_m_s / constants.v_swirl_m_s) ** 2,
            "gamma_0_m2_s": constants.gamma_0_m2_s,
        },
        "used_as_prediction_inputs": used_as_inputs,
        "gates": gates,
        "overall_status": overall_status(gates),
        "next_required_promotions": [
            "Derive Xi_K without target masses.",
            "Lock freeze-then-predict manifest before residual evaluation.",
            "Derive theta=pi from a spinorial/topological boundary obstruction.",
            "Derive torsion impedance scale/density instead of using required scale diagnostics."
        ]
    }
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description="SST non-fitted prediction harness for four closure gates.")
    ap.add_argument("--knot-id", default="3:1:1")
    ap.add_argument("--ideal", default=None, help="Optional SSTcore ideal.txt path for ropelength extraction.")
    ap.add_argument("--n", type=int, default=512, help="Fourier sample count if ideal.txt has no declared L.")
    ap.add_argument("--torsion-json", default=None, help="Optional standalone torsion impedance audit JSON.")
    ap.add_argument("--torsion-density-key", default="rho_f", help="Prefer rho_f or rho_core case from torsion JSON.")
    ap.add_argument("--protocol", default=None)
    ap.add_argument("--manifest", default=None)
    ap.add_argument("--allow-calibration", action="store_true", help="Downgrade forbidden target inputs to CALIBRATED instead of FAILED.")
    ap.add_argument("--use-target-mass-as-input", action="store_true", help="Deliberate negative-control flag: should fail strict nonfit protocol.")
    ap.add_argument("--use-required-kernel-as-input", action="store_true", help="Deliberate negative-control flag: should fail mass-kernel gate.")
    ap.add_argument("--out-json", default="out/nonfit_report.json")
    ap.add_argument("--out-csv", default="out/nonfit_gates.csv")
    args = ap.parse_args()

    report = build_report(args)
    write_json(args.out_json, report)
    write_gate_csv(args.out_csv, report["gates"])
    print(json.dumps({
        "overall_status": report["overall_status"],
        "knot_id": report["target"]["knot_id"],
        "gates": {k: v["status"] for k, v in report["gates"].items()},
        "out_json": args.out_json,
        "out_csv": args.out_csv,
    }, indent=2))
    return 0 if report["overall_status"] != STATUS_FAILED else 2


if __name__ == "__main__":
    raise SystemExit(main())
