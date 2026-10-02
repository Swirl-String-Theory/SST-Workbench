from pathlib import Path
import csv
import hashlib
import json
import os
import numpy as np

from .spectral import grad_vector, stress_source, poisson_periodic
from .backend import decompose_gradient, invariants, backend_name
from .reference import local_linear_controls, build_metric
from .synthetic import abc_flow, taylor_green, shear_wave, localized_vortex, uniform_flow
from .geometry import curvature_diagnostics
from .objectivity import objectivity_residual, rotation_matrix
from .pipeline import reconstruct_velocity_gradient, three_layer_response
from .rotating import absolute_vorticity, matched_cyclonic_hemisphere_pair
from .delay import circulation_delay_control


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
    gradient_reconstruction_max = 0.0
    for blind_id, builder in case_builders.items():
        u = builder()
        grad = grad_vector(u, L)
        S, omega, div = decompose_gradient(grad)
        inv = invariants(u, omega, S)
        grad_rec = reconstruct_velocity_gradient(S, omega)
        grad_rec_rel = _rel_l2(grad_rec, grad)
        gradient_reconstruction_max = max(gradient_reconstruction_max, grad_rec_rel)
        cached[blind_id] = (u, grad, S, omega, div)
        max_div = max(max_div, float(np.max(np.abs(div))))
        case_rows.append({
            "blind_id": blind_id,
            "u_rms": float(np.sqrt(np.mean(inv["speed2"]))),
            "omega_rms": float(np.sqrt(np.mean(inv["omega2"]))),
            "strain_rms": float(np.sqrt(np.mean(inv["strain2"]))),
            "helicity_mean": float(np.mean(inv["helicity"])),
            "div_max_abs": float(np.max(np.abs(div))),
            "gradient_reconstruction_rel_l2": grad_rec_rel,
        })

    # v0.1 local-basis degeneracy control.
    pair = local_linear_controls()
    hwc_equal_error = max(
        float(np.linalg.norm(pair["uA"] - pair["uB"])),
        float(np.linalg.norm(pair["omegaA"] - pair["omegaB"])),
        abs(pair["hA"] - pair["hB"]),
        abs(pair["GammaA"] - pair["GammaB"]),
    )
    strain_delta = float(np.linalg.norm(pair["strainA"] - pair["strainB"]))

    # Clock-pressure locking on steady ABC/Beltrami control.
    u_abc = cached["B01"][0]
    u_rms = float(np.sqrt(np.mean(np.sum(u_abc * u_abc, axis=-1))))
    c_test = float(cfg["clock_speed_factor"]) * u_rms
    q = np.sum(u_abc * u_abc, axis=-1) / (c_test * c_test)
    dp_star = -0.5 * q
    dn_direct = (1.0 - q) ** (-0.5) - 1.0
    dn_from_pressure = (1.0 + 2.0 * dp_star) ** (-0.5) - 1.0
    clock_lock_rel = _rel_l2(dn_from_pressure, dn_direct)
    clock_leading_rel = _rel_l2(-dp_star, dn_direct)

    # Explicit three-layer response u -> (omega,S) -> Phi_bulk.
    chain = three_layer_response(cached["B04"][0], L)
    poisson_rel = _rel_l2(chain["lap_phi"], chain["q_transport"])
    Qsrc = chain["q_transport"]
    phi = chain["phi_bulk"]
    src_mask = np.abs(Qsrc) > np.quantile(np.abs(Qsrc), 0.90)
    phi_energy = float(np.sum(phi * phi))
    nonlocal_fraction = 0.0 if phi_energy == 0.0 else float(
        np.sum(phi[~src_mask] ** 2) / phi_energy
    )

    # Relative-vorticity metric controls retained from v0.1.
    def metric_diag(u, omega_override=None, strain_override=None):
        grad = grad_vector(u, L)
        S, omega, _ = decompose_gradient(grad)
        if omega_override is not None:
            omega = np.broadcast_to(np.asarray(omega_override, dtype=float), omega.shape).copy()
        if strain_override is not None:
            S = np.broadcast_to(np.asarray(strain_override, dtype=float), S.shape).copy()
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

    # Constant planetary absolute-vorticity background in a local tangent frame.
    omega_p = float(cfg["planetary_rotation_blind"])
    uniform_abs = np.array([0.0, 0.0, 2.0 * omega_p])
    geom_planetary_flat = metric_diag(
        uniform_flow(nc),
        omega_override=uniform_abs,
        strain_override=np.zeros((3, 3)),
    )

    # SO(3) objectivity of local kinematics.
    uo = abc_flow(nc, L)
    go = grad_vector(uo, L)
    idx = (1, 2, 3)
    objectivity_rel, objectivity_terms = objectivity_residual(
        uo[idx], go[idx], seed=int(cfg["seed"])
    )

    # Rotating-frame absolute-vorticity and hemisphere controls.
    omega_rel_probe = np.array([0.31, -0.17, 0.83])
    omega_planet_probe = np.array([-0.09, 0.04, omega_p])
    eta_probe = absolute_vorticity(omega_rel_probe, omega_planet_probe)
    eta_expected = omega_rel_probe + 2.0 * omega_planet_probe
    absolute_vorticity_rel = _rel_l2(eta_probe, eta_expected)
    zero_rotation_rel = _rel_l2(
        absolute_vorticity(omega_rel_probe, np.zeros(3)), omega_rel_probe
    )

    hemi = matched_cyclonic_hemisphere_pair(
        zeta=float(cfg["cyclonic_relative_vorticity_blind"]),
        omega_planet=omega_p,
    )
    hemi_mirror_rel = _rel_l2(
        hemi["south_absolute"], -hemi["north_absolute"]
    )
    hemi_magnitude_rel = abs(
        np.linalg.norm(hemi["north_absolute"])
        - np.linalg.norm(hemi["south_absolute"])
    ) / max(1.0, np.linalg.norm(hemi["north_absolute"]))

    Qrot = rotation_matrix(seed=int(cfg["seed"]) + 17)
    eta_rot_direct = Qrot @ eta_probe
    eta_rot_constructed = absolute_vorticity(
        Qrot @ omega_rel_probe, Qrot @ omega_planet_probe
    )
    rotating_objectivity_rel = _rel_l2(eta_rot_constructed, eta_rot_direct)

    # Delay/circulation-memory controls.
    delay = circulation_delay_control(
        n=int(cfg["delay_samples"]),
        mode=int(cfg["delay_mode"]),
        phase_rad=float(cfg["delay_phase_rad"]),
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
        "G13_UWS_GRADIENT_RECONSTRUCTION": gradient_reconstruction_max < tol["gradient_reconstruction_rel_l2"],
        "G14_ABSOLUTE_VORTICITY_IDENTITY": absolute_vorticity_rel < tol["absolute_vorticity_rel_l2"],
        "G15_HEMISPHERE_CYCLONIC_MIRROR": (
            hemi_mirror_rel < tol["hemisphere_mirror_rel_l2"]
            and hemi_magnitude_rel < tol["hemisphere_mirror_rel_l2"]
        ),
        "G16_ZERO_ROTATION_LIMIT": zero_rotation_rel < tol["rotation_zero_limit_rel_l2"],
        "G17_ROTATING_OBJECTIVITY": rotating_objectivity_rel < tol["rotating_objectivity_rel_l2"],
        "G18_PLANETARY_BACKGROUND_FLAT_CONTROL": (
            geom_planetary_flat["curvature_rms"] < tol["planetary_flat_curvature_rms_max"]
        ),
        "G19_DELAY_PHASE_RECOVERY": delay["phase_error_rad"] < tol["delay_phase_abs_rad"],
        "G20_DELAY_ZERO_LIMIT": delay["zero_delay_memory_rms"] < tol["delay_zero_rms_max"],
        "G21_DELAY_MEMORY_NONTRIVIAL": delay["memory_rms"] > tol["delay_memory_rms_min"],
    }

    gates = {key: bool(value) for key, value in gates.items()}

    summary = {
        "catalog_id": cfg.get("catalog_id", "A046"),
        "falsifier": "A046_relative_vorticity_triadic_geometry_falsifier",
        "version": cfg["version"],
        "blind": True,
        "backend": backend_name(),
        "overall_status": "PIPELINE_QUALIFIED" if all(gates.values()) else "PIPELINE_FAILED",
        "candidate_basis": {
            "HWC": (
                "REJECTED_AS_LOCAL_COMPLETE_BASIS"
                if gates["G02_HWC_DEGENERACY_FOUND"] else "NOT_REJECTED"
            ),
            "UWS": (
                "LOCAL_FIRST_ORDER_KINEMATICS_RECONSTRUCTED_NOT_VALIDATED_AS_GRAVITY"
                if gates["G13_UWS_GRADIENT_RECONSTRUCTION"] else "REJECTED"
            ),
        },
        "three_layer_model": {
            "layer_1": "u: local transport / clock input",
            "layer_2": "omega_rel and S_ij: complete local first-order velocity-gradient decomposition",
            "layer_3": "Phi_bulk: nonlocal Poisson response of organized transport source",
            "rotation_extension": "omega_abs = omega_rel + 2 Omega_p",
            "delay_extension": "Gamma(t)-Gamma(t-tau), with Delta phi = omega*tau",
        },
        "measurements": {
            "max_divergence": max_div,
            "hwc_equal_error": hwc_equal_error,
            "strain_delta_frobenius": strain_delta,
            "gradient_reconstruction_max_rel_l2": gradient_reconstruction_max,
            "clock_pressure_exact_lock_rel_l2": clock_lock_rel,
            "clock_pressure_leading_rel_l2": clock_leading_rel,
            "poisson_reconstruction_rel_l2": poisson_rel,
            "poisson_nonlocal_phi_energy_fraction": nonlocal_fraction,
            "abc_geometry": geom_abc,
            "null_geometry": geom_null,
            "planetary_flat_geometry": geom_planetary_flat,
            "objectivity_rel_max": objectivity_rel,
            "objectivity_terms": objectivity_terms,
            "absolute_vorticity_rel_l2": absolute_vorticity_rel,
            "zero_rotation_rel_l2": zero_rotation_rel,
            "hemisphere_mirror_rel_l2": hemi_mirror_rel,
            "hemisphere_magnitude_rel": hemi_magnitude_rel,
            "rotating_objectivity_rel_l2": rotating_objectivity_rel,
            "delay": delay,
        },
        "gates": gates,
        "interpretation_guard": (
            "Passing qualifies the preregistered kinematic, rotating-frame, delay, Poisson, "
            "and exploratory-geometry controls only. It does not establish physical gravity, "
            "a spacetime metric, or a universal coupling law."
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
        "# A046 v0.2.0 blind report",
        "",
        f"Backend: **{summary['backend']}**",
        f"Overall: **{summary['overall_status']}**",
        "",
        f"HWC basis: **{summary['candidate_basis']['HWC']}**",
        f"UWS basis: **{summary['candidate_basis']['UWS']}**",
        "",
        "## Three-layer chain",
        "",
        "1. u -> clock/transport input",
        "2. (omega_rel, S_ij) -> local first-order kinematics",
        "3. Q_transport -> Phi_bulk through Poisson inversion",
        "",
        "Rotation: omega_abs = omega_rel + 2 Omega_p.",
        "Delay: Gamma(t)-Gamma(t-tau), Delta phi = omega*tau.",
        "",
        "## Key measurements",
        "",
        f"- max |div u| = {max_div:.6e}",
        f"- HWC equality error = {hwc_equal_error:.6e}",
        f"- strain-pair distance = {strain_delta:.6e}",
        f"- UWS gradient reconstruction max relative L2 = {gradient_reconstruction_max:.6e}",
        f"- exact pressure/clock lock relative L2 = {clock_lock_rel:.6e}",
        f"- Poisson reconstruction relative L2 = {poisson_rel:.6e}",
        f"- nonlocal Phi energy fraction = {nonlocal_fraction:.6e}",
        f"- ABC curvature RMS = {geom_abc['curvature_rms']:.6e}",
        f"- planetary flat-control curvature RMS = {geom_planetary_flat['curvature_rms']:.6e}",
        f"- hemisphere mirror relative L2 = {hemi_mirror_rel:.6e}",
        f"- rotating objectivity relative L2 = {rotating_objectivity_rel:.6e}",
        f"- delay phase error = {delay['phase_error_rad']:.6e} rad",
        f"- delay memory RMS = {delay['memory_rms']:.6e}",
        "",
        "## Gates",
        "",
    ]
    for name, ok in gates.items():
        report.append(f"- {name}: {'PASS' if ok else 'FAIL'}")
    report += ["", "## Scientific guard", "", summary["interpretation_guard"]]
    (out / "blind_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    return summary


def seal_directory(out_dir):
    out = Path(out_dir)
    targets = sorted(
        p for p in out.rglob("*")
        if p.is_file() and p.name != "BLIND_SEAL_SHA256.txt"
    )
    lines = []
    for p in targets:
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        rel = p.relative_to(out).as_posix()
        lines.append(f"{digest}  {rel}")
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
        p = out / Path(name)
        if not p.exists():
            errors.append(f"missing {name}")
            continue
        got = hashlib.sha256(p.read_bytes()).hexdigest()
        if got != digest:
            errors.append(f"hash mismatch {name}")
    return not errors, errors
