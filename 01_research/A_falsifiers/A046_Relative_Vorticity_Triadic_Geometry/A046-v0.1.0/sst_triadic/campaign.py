from pathlib import Path
import csv
import hashlib
import json
import numpy as np

from .spectral import grad_vector, stress_source, poisson_periodic
from .backend import decompose_gradient, invariants
from .reference import local_linear_controls, build_metric
from .synthetic import abc_flow, taylor_green, shear_wave, localized_vortex, uniform_flow
from .geometry import curvature_diagnostics
from .objectivity import objectivity_residual

def _rel_l2(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    den = np.linalg.norm(b.ravel())
    if den == 0.0:
        return float(np.linalg.norm(a.ravel()))
    return float(np.linalg.norm((a - b).ravel()) / den)

def _load_config(config_path):
    return json.loads(Path(config_path).read_text(encoding="utf-8"))

def run_blind_campaign(config_path, out_dir):
    cfg = _load_config(config_path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    L = float(cfg["domain_length"])
    n = int(cfg["grid_n_fields"])
    nc = int(cfg["grid_n_curvature"])
    tol = cfg["tolerances"]

    case_builders = {
        "B01": lambda: abc_flow(n, L),
        "B02": lambda: taylor_green(n, L),
        "B03": lambda: shear_wave(n, L),
        "B04": lambda: localized_vortex(n, L),
    }

    case_rows = []
    max_div = 0.0
    cached = {}
    for blind_id, builder in case_builders.items():
        u = builder()
        grad = grad_vector(u, L)
        S, omega, div = decompose_gradient(grad)
        inv = invariants(u, omega, S)
        cached[blind_id] = (u, grad, S, omega, div)
        max_div = max(max_div, float(np.max(np.abs(div))))
        case_rows.append({
            "blind_id": blind_id,
            "u_rms": float(np.sqrt(np.mean(inv["speed2"]))),
            "omega_rms": float(np.sqrt(np.mean(inv["omega2"]))),
            "strain_rms": float(np.sqrt(np.mean(inv["strain2"]))),
            "helicity_mean": float(np.mean(inv["helicity"])),
            "div_max_abs": float(np.max(np.abs(div))),
        })

    pair = local_linear_controls()
    hwc_equal_error = max(
        float(np.linalg.norm(pair["uA"] - pair["uB"])),
        float(np.linalg.norm(pair["omegaA"] - pair["omegaB"])),
        abs(pair["hA"] - pair["hB"]),
        abs(pair["GammaA"] - pair["GammaB"]),
    )
    strain_delta = float(np.linalg.norm(pair["strainA"] - pair["strainB"]))

    u_abc = cached["B01"][0]
    u_rms = float(np.sqrt(np.mean(np.sum(u_abc * u_abc, axis=-1))))
    c_test = float(cfg["clock_speed_factor"]) * u_rms
    q = np.sum(u_abc * u_abc, axis=-1) / (c_test * c_test)
    dp_star = -0.5 * q
    dn_direct = (1.0 - q) ** (-0.5) - 1.0
    dn_from_pressure = (1.0 + 2.0 * dp_star) ** (-0.5) - 1.0
    clock_lock_rel = _rel_l2(dn_from_pressure, dn_direct)
    clock_leading_rel = _rel_l2(-dp_star, dn_direct)

    u_loc = cached["B04"][0]
    Qsrc = stress_source(u_loc, L)
    phi, lap = poisson_periodic(Qsrc, L)
    poisson_rel = _rel_l2(lap, Qsrc)
    src_mask = np.abs(Qsrc) > np.quantile(np.abs(Qsrc), 0.90)
    phi_energy = float(np.sum(phi * phi))
    nonlocal_fraction = 0.0 if phi_energy == 0.0 else float(
        np.sum(phi[~src_mask] ** 2) / phi_energy
    )

    def metric_diag(u):
        grad = grad_vector(u, L)
        S, omega, _ = decompose_gradient(grad)
        urms = float(np.sqrt(np.mean(np.sum(u * u, axis=-1))))
        cmetric = max(1.0, float(cfg["clock_speed_factor"]) * urms)
        g = build_metric(
            u, omega, S, cmetric,
            float(cfg["metric_eps_shift"]),
            float(cfg["metric_eps_strain"]),
            float(cfg["metric_eps_omega2"]),
        )
        return curvature_diagnostics(g, L)

    geom_abc = metric_diag(abc_flow(nc, L))
    geom_null = metric_diag(uniform_flow(nc))

    uo = abc_flow(nc, L)
    go = grad_vector(uo, L)
    idx = (1, 2, 3)
    objectivity_rel, objectivity_terms = objectivity_residual(
        uo[idx], go[idx], seed=int(cfg["seed"])
    )

    gates = {
        "G01_INCOMPRESSIBILITY": max_div < tol["divergence_max"],
        "G02_HWC_DEGENERACY_FOUND": (
            hwc_equal_error < tol["hwc_equal"]
            and strain_delta > tol["strain_distinguish"]
        ),
        "G03_UWS_DISTINGUISHES_PAIR": strain_delta > tol["strain_distinguish"],
        "G04_CLOCK_PRESSURE_EXACT_LOCK": clock_lock_rel < tol["clock_lock_rel_l2"],
        "G05_POISSON_RECONSTRUCTION": poisson_rel < tol["poisson_rel_l2"],
        "G06_POISSON_NONLOCALITY": nonlocal_fraction > tol["nonlocal_phi_fraction_min"],
        "G07_METRIC_LORENTZ_SIGNATURE_ABC": (
            geom_abc["metric_negative_eigs_min"] == 1
            and geom_abc["metric_negative_eigs_max"] == 1
        ),
        "G08_METRIC_LORENTZ_SIGNATURE_NULL": (
            geom_null["metric_negative_eigs_min"] == 1
            and geom_null["metric_negative_eigs_max"] == 1
        ),
        "G09_NULL_CURVATURE": geom_null["curvature_rms"] < tol["null_curvature_rms_max"],
        "G10_NONUNIFORM_CURVATURE": geom_abc["curvature_rms"] > tol["abc_curvature_rms_min"],
        "G11_RIEMANN_PAIR_SYMMETRY": geom_abc["riemann_pair_rel_l2"] < tol["riemann_pair_rel_l2_max"],
        "G12_OBJECTIVITY": objectivity_rel < tol["objectivity_rel_max"],
    }

    summary = {
        "falsifier": "A045_relative_vorticity_triadic_geometry_falsifier",
        "version": cfg["version"],
        "blind": True,
        "overall_status": "PIPELINE_QUALIFIED" if all(gates.values()) else "PIPELINE_FAILED",
        "candidate_basis": {
            "HWC": (
                "REJECTED_AS_LOCAL_COMPLETE_BASIS"
                if gates["G02_HWC_DEGENERACY_FOUND"] else "NOT_REJECTED"
            ),
            "UWS": (
                "STRUCTURALLY_ADMISSIBLE_NOT_VALIDATED_AS_GRAVITY"
                if gates["G03_UWS_DISTINGUISHES_PAIR"] else "REJECTED"
            ),
        },
        "measurements": {
            "max_divergence": max_div,
            "hwc_equal_error": hwc_equal_error,
            "strain_delta_frobenius": strain_delta,
            "clock_pressure_exact_lock_rel_l2": clock_lock_rel,
            "clock_pressure_leading_rel_l2": clock_leading_rel,
            "poisson_reconstruction_rel_l2": poisson_rel,
            "poisson_nonlocal_phi_energy_fraction": nonlocal_fraction,
            "abc_geometry": geom_abc,
            "null_geometry": geom_null,
            "objectivity_rel_max": objectivity_rel,
            "objectivity_terms": objectivity_terms,
        },
        "gates": gates,
        "interpretation_guard": (
            "A passing run qualifies only the mathematical/numerical construction. "
            "It does not establish that the exploratory metric is physical gravity."
        ),
    }

    (out / "blind_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    with (out / "case_metrics.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(case_rows[0].keys()))
        writer.writeheader()
        writer.writerows(case_rows)

    report = [
        "# A045 blind report",
        "",
        f"Overall: **{summary['overall_status']}**",
        "",
        f"HWC basis: **{summary['candidate_basis']['HWC']}**",
        f"UWS basis: **{summary['candidate_basis']['UWS']}**",
        "",
        "## Key measurements",
        "",
        f"- max |div u| = {max_div:.6e}",
        f"- HWC equality error = {hwc_equal_error:.6e}",
        f"- strain-pair distance = {strain_delta:.6e}",
        f"- exact pressure/clock lock relative L2 = {clock_lock_rel:.6e}",
        f"- leading weak-speed lock relative L2 = {clock_leading_rel:.6e}",
        f"- Poisson reconstruction relative L2 = {poisson_rel:.6e}",
        f"- nonlocal Phi energy fraction = {nonlocal_fraction:.6e}",
        f"- ABC curvature RMS = {geom_abc['curvature_rms']:.6e}",
        f"- null curvature RMS = {geom_null['curvature_rms']:.6e}",
        f"- Riemann pair-symmetry relative L2 = {geom_abc['riemann_pair_rel_l2']:.6e}",
        f"- objectivity maximum relative residual = {objectivity_rel:.6e}",
        "",
        "## Gates",
        "",
    ]
    for name, ok in gates.items():
        report.append(f"- {name}: {'PASS' if ok else 'FAIL'}")
    report += [
        "",
        "## Scientific guard",
        "",
        summary["interpretation_guard"],
    ]
    (out / "blind_report.md").write_text(
        "\n".join(report) + "\n", encoding="utf-8"
    )
    return summary

def seal_directory(out_dir):
    out = Path(out_dir)
    targets = sorted(
        p for p in out.iterdir()
        if p.is_file() and p.name != "BLIND_SEAL_SHA256.txt"
    )
    lines = []
    for p in targets:
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        lines.append(f"{digest}  {p.name}")
    seal_text = "\n".join(lines) + "\n"
    (out / "BLIND_SEAL_SHA256.txt").write_text(seal_text, encoding="utf-8")
    return seal_text

def verify_seal(out_dir):
    out = Path(out_dir)
    seal = out / "BLIND_SEAL_SHA256.txt"
    if not seal.exists():
        return False, ["seal missing"]
    errors = []
    for line in seal.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, name = line.split("  ", 1)
        p = out / name
        if not p.exists():
            errors.append(f"missing {name}")
            continue
        got = hashlib.sha256(p.read_bytes()).hexdigest()
        if got != digest:
            errors.append(f"hash mismatch {name}")
    return not errors, errors
