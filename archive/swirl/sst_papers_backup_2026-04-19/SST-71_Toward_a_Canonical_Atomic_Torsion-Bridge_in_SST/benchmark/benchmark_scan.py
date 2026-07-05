"""
Run the SST-71 helicity asymmetry benchmark: scan photon energy, compute rates and A_tot,
run controls (no anticommutator, non-helical, broken axisymmetry), and a convergence study.
Saves all results to CSV files.

Use --verbose to log most steps (per-energy results, file saves). Use --debug for additional
detail from the integration layer (grid sizes, C++/Python path, per-call rates).
"""

from __future__ import annotations

import argparse
import csv
import logging
import os
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict

try:
    from tqdm import tqdm
except ImportError:
    class _FakeTqdm:
        """No-op progress bar when tqdm is not installed; provides update() and close()."""

        def __init__(self, iterable=None, total=None, **kwargs):
            self._iterable = iterable
            self._total = total or 0

        def __iter__(self):
            if self._iterable is not None:
                return iter(self._iterable)
            return iter(range(self._total))

        def update(self, n=1):
            pass

        def close(self):
            pass

    def tqdm(iterable=None, total=None, desc=None, **kwargs):
        return _FakeTqdm(iterable=iterable, total=total, **kwargs)

import constants
import matrix_elements

logger = logging.getLogger(__name__)

# Default scan: 15 eV to 100 eV; step and number of points
I1_eV = constants.J_to_eV(constants.E_R)


def _compute_one_energy_row(
    omega_eV: float,
    I1_eV: float,
    use_anticommutator: bool,
    probe_type: str,
    eps: float | None,
    params: matrix_elements.BenchmarkParams,
) -> dict:
    """Worker for one photon energy: compute Gamma_p, Gamma_m, A_tot. Used with ProcessPoolExecutor."""
    E_k_eV = omega_eV - I1_eV
    if E_k_eV <= 0:
        return None  # caller skips
    E_k_J = constants.eV_to_J(E_k_eV)
    Gp = matrix_elements.compute_total_rate(E_k_J, 1, params, use_anticommutator, probe_type, eps)
    Gm = matrix_elements.compute_total_rate(E_k_J, -1, params, use_anticommutator, probe_type, eps)
    s = Gp + Gm
    A_tot = (Gp - Gm) / s if s > 0 else 0.0
    return {
        "omega_eV": omega_eV,
        "E_k_eV": E_k_eV,
        "Gamma_h_plus1": Gp,
        "Gamma_h_minus1": Gm,
        "A_tot": A_tot,
    }


def _run_energy_scan(
    params: matrix_elements.BenchmarkParams,
    use_anticommutator: bool,
    probe_type: str = "helical",
    eps: float | None = None,
    energies_eV: np.ndarray | None = None,
    jobs: int = 1,
    progress: bool = True,
    desc: str = "Energy scan",
) -> list[dict]:
    """Scan over photon energies; return list of dicts with omega_eV, E_k_eV, Gamma_p, Gamma_m, A_tot.
    Both helicity channels are always computed from the physics (non-helical uses C=-2 for both so rates match).
    If jobs > 1, energy points are computed in parallel using that many worker processes.
    """
    if energies_eV is None:
        energies_eV = np.linspace(15.0, 100.0, 10)  # 15–100 eV, 10 points
    energies_eV = np.atleast_1d(energies_eV)
    above_threshold = [float(om) for om in energies_eV if (om - I1_eV) > 0]
    logger.info(
        "Energy scan: %d points (%d above threshold), use_anticommutator=%s, probe_type=%s, eps=%s, jobs=%d",
        len(energies_eV), len(above_threshold), use_anticommutator, probe_type, eps, jobs,
    )
    if not above_threshold:
        return []

    # Old broken-axisymmetry (helical + eps != 0) uses 3D integral; helical_mode_plus1 uses fast 2D path
    if eps is not None and eps != 0.0 and probe_type == "helical":
        if getattr(matrix_elements, "_CPP_AVAILABLE", False):
            print("  (3D integral — using C++ kernel.)")
        else:
            print("  (3D integral — Python fallback; each energy point may take minutes.)")

    n_total = len(above_threshold)
    pbar = tqdm(total=n_total, desc=desc, unit="pt", disable=not progress)

    if jobs <= 1:
        rows = []
        for omega_eV in above_threshold:
            row = _compute_one_energy_row(
                omega_eV, I1_eV, use_anticommutator, probe_type, eps, params
            )
            if row is not None:
                rows.append(row)
                logger.info(
                    "  omega=%.2f eV -> E_k=%.4f eV, Gamma_p=%.4e, Gamma_m=%.4e, A_tot=%.6f",
                    row["omega_eV"], row["E_k_eV"], row["Gamma_h_plus1"], row["Gamma_h_minus1"], row["A_tot"],
                )
            pbar.update(1)
        pbar.close()
        rows.sort(key=lambda r: r["omega_eV"])
        return rows

    rows = []
    with ProcessPoolExecutor(max_workers=jobs) as executor:
        future_to_omega = {
            executor.submit(
                _compute_one_energy_row,
                omega_eV, I1_eV, use_anticommutator, probe_type, eps, params,
            ): omega_eV
            for omega_eV in above_threshold
        }
        for future in as_completed(future_to_omega):
            row = future.result()
            if row is not None:
                rows.append(row)
                logger.info(
                    "  omega=%.2f eV -> E_k=%.4f eV, Gamma_p=%.4e, Gamma_m=%.4e, A_tot=%.6f",
                    row["omega_eV"], row["E_k_eV"], row["Gamma_h_plus1"], row["Gamma_h_minus1"], row["A_tot"],
                )
            pbar.update(1)
    pbar.close()
    rows.sort(key=lambda r: r["omega_eV"])
    return rows


def _save_csv(path: str, rows: list[dict], fieldnames: list[str]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    logger.info("Saved CSV: %s (%d rows)", path, len(rows))


def run_main_benchmark(
    out_dir: str = ".",
    energies_eV: np.ndarray | None = None,
    params: matrix_elements.BenchmarkParams | None = None,
    jobs: int = 1,
    progress: bool = True,
) -> str:
    """Main benchmark: helical, axisymmetric, use_anticommutator=True. Expect A_tot ≈ -8/17."""
    if params is None:
        params = matrix_elements.BenchmarkParams.default()
    rows = _run_energy_scan(
        params, use_anticommutator=True, probe_type="helical",
        energies_eV=energies_eV, jobs=jobs, progress=progress, desc="Main benchmark",
    )
    path = os.path.join(out_dir, "benchmark_main.csv")
    _save_csv(path, rows, ["omega_eV", "E_k_eV", "Gamma_h_plus1", "Gamma_h_minus1", "A_tot"])
    return path


def run_control_no_anticommutator(
    out_dir: str = ".",
    energies_eV: np.ndarray | None = None,
    params: matrix_elements.BenchmarkParams | None = None,
    jobs: int = 1,
    progress: bool = True,
) -> str:
    """Control: use_anticommutator=False. Expect A_tot ≈ 0."""
    if params is None:
        params = matrix_elements.BenchmarkParams.default()
    rows = _run_energy_scan(
        params, use_anticommutator=False, probe_type="helical",
        energies_eV=energies_eV, jobs=jobs, progress=progress, desc="No anticommutator",
    )
    path = os.path.join(out_dir, "control_no_anticommutator.csv")
    _save_csv(path, rows, ["omega_eV", "E_k_eV", "Gamma_h_plus1", "Gamma_h_minus1", "A_tot"])
    return path


def run_control_non_helical(
    out_dir: str = ".",
    energies_eV: np.ndarray | None = None,
    params: matrix_elements.BenchmarkParams | None = None,
    jobs: int = 1,
    progress: bool = True,
) -> str:
    """Control: non-helical probe (h=0). Expect A_tot = 0."""
    if params is None:
        params = matrix_elements.BenchmarkParams.default()
    rows = _run_energy_scan(
        params, use_anticommutator=True, probe_type="non_helical",
        energies_eV=energies_eV, jobs=jobs, progress=progress, desc="Non-helical",
    )
    path = os.path.join(out_dir, "control_non_helical.csv")
    _save_csv(path, rows, ["omega_eV", "E_k_eV", "Gamma_h_plus1", "Gamma_h_minus1", "A_tot"])
    return path


def run_control_helical_mode_plus1(
    out_dir: str = ".",
    eps: float = 0.25,
    energies_eV: np.ndarray | None = None,
    params: matrix_elements.BenchmarkParams | None = None,
    jobs: int = 1,
    progress: bool = True,
) -> str:
    """Stronger control: one-sided Fourier perturbation (helical_mode_plus1).
    Breaks m↔-m pairing: h=+1 -> m=+1,+2; h=-1 -> m=-1,0.
    At eps=0 recovers main benchmark (A_tot ≈ -8/17); for finite eps expect deviation.
    Uses fast 2D harmonic path, not 3D.
    """
    if params is None:
        params = matrix_elements.BenchmarkParams.default()
    rows = _run_energy_scan(
        params, use_anticommutator=True, probe_type="helical_mode_plus1", eps=eps,
        energies_eV=energies_eV, jobs=jobs, progress=progress, desc="Helical mode +1 (stronger control)",
    )
    path = os.path.join(out_dir, "control_helical_mode_plus1.csv")
    _save_csv(path, rows, ["omega_eV", "E_k_eV", "Gamma_h_plus1", "Gamma_h_minus1", "A_tot"])
    return path


def run_control_helical_mode_plus1_eps_scan(
    out_dir: str = ".",
    omega_eV: float = 30.0,
    eps_values: list[float] | None = None,
    params: matrix_elements.BenchmarkParams | None = None,
    progress: bool = True,
) -> str:
    """Epsilon scan for helical_mode_plus1 at one photon energy.
    eps in [0, 0.05, 0.1, 0.2, 0.3, 0.5] by default. At eps=0, A_tot ≈ -8/17; finite eps deviates."""
    if params is None:
        params = matrix_elements.BenchmarkParams.default()
    if eps_values is None:
        eps_values = [0.0, 0.05, 0.1, 0.2, 0.3, 0.5]
    E_k_eV = omega_eV - I1_eV
    if E_k_eV <= 0:
        raise ValueError(f"Photon energy {omega_eV} eV is below threshold (I1 ≈ {I1_eV:.2f} eV).")
    E_k_J = constants.eV_to_J(E_k_eV)
    logger.info("Epsilon scan at omega=%.1f eV (E_k=%.4f eV), eps=%s", omega_eV, E_k_eV, eps_values)

    rows = []
    if progress:
        try:
            eps_iter = tqdm(eps_values, desc="Epsilon scan", unit="eps")
        except Exception:
            eps_iter = eps_values
    else:
        eps_iter = eps_values
    for eps in eps_iter:
        Gp = matrix_elements.compute_total_rate(E_k_J, 1, params, True, "helical_mode_plus1", eps)
        Gm = matrix_elements.compute_total_rate(E_k_J, -1, params, True, "helical_mode_plus1", eps)
        s = Gp + Gm
        A_tot = (Gp - Gm) / s if s > 0 else 0.0
        rows.append({
            "omega_eV": omega_eV,
            "E_k_eV": E_k_eV,
            "eps": eps,
            "Gamma_h_plus1": Gp,
            "Gamma_h_minus1": Gm,
            "A_tot": A_tot,
        })
    path = os.path.join(out_dir, "control_helical_mode_plus1_eps_scan.csv")
    _save_csv(path, rows, ["omega_eV", "E_k_eV", "eps", "Gamma_h_plus1", "Gamma_h_minus1", "A_tot"])
    return path


def run_control_broken_axisymmetry(
    out_dir: str = ".",
    eps: float = 0.2,
    energies_eV: np.ndarray | None = None,
    params: matrix_elements.BenchmarkParams | None = None,
    jobs: int = 1,
    progress: bool = True,
) -> str:
    """Control: broken axisymmetry (cos(2phi)-style, 3D path). Secondary diagnostic;
    mirror-symmetric perturbation may not move A_tot off -8/17 due to residual m↔-m pairing."""
    if params is None:
        params = matrix_elements.BenchmarkParams.default()
    rows = _run_energy_scan(
        params, use_anticommutator=True, probe_type="helical", eps=eps,
        energies_eV=energies_eV, jobs=jobs, progress=progress, desc="Broken axisymmetry (secondary)",
    )
    path = os.path.join(out_dir, "control_broken_axisymmetry.csv")
    _save_csv(path, rows, ["omega_eV", "E_k_eV", "Gamma_h_plus1", "Gamma_h_minus1", "A_tot"])
    return path


def _compute_one_convergence_row(
    E_k_J: float,
    variable: str,
    value: float | int,
    value_SI: float,
    params_dict: dict,
) -> dict:
    """Worker for one convergence configuration. Used with ProcessPoolExecutor."""
    p = matrix_elements.BenchmarkParams(**params_dict)
    Gp = matrix_elements.compute_total_rate(E_k_J, 1, p, True, "helical", None)
    Gm = matrix_elements.compute_total_rate(E_k_J, -1, p, True, "helical", None)
    s = Gp + Gm
    A_tot = (Gp - Gm) / s if s > 0 else 0.0
    return {"variable": variable, "value": value, "value_SI": value_SI, "A_tot": A_tot}


A_REF = constants.A_expected  # -8/17


def _compute_one_convergence_row_helical_mode_plus1(
    E_k_J: float,
    photon_energy_eV: float,
    eps: float,
    sweep_type: str,
    sweep_value: float | int,
    params_dict: dict,
) -> dict:
    """Worker for one stronger-control convergence configuration. Returns full row for CSV."""
    p = matrix_elements.BenchmarkParams(**params_dict)
    Gp = matrix_elements.compute_total_rate(E_k_J, 1, p, True, "helical_mode_plus1", eps)
    Gm = matrix_elements.compute_total_rate(E_k_J, -1, p, True, "helical_mode_plus1", eps)
    s = Gp + Gm
    asymmetry = (Gp - Gm) / s if s > 0 else 0.0
    delta_from_minus_8_over_17 = asymmetry - A_REF
    R_max_over_a0 = p.R_max / constants.a0_sst
    return {
        "sweep_type": sweep_type,
        "sweep_value": sweep_value,
        "photon_energy_eV": photon_energy_eV,
        "eps": eps,
        "R_max_over_a0": R_max_over_a0,
        "N_r": p.N_r,
        "N_theta": p.N_theta,
        "l_max": p.l_max,
        "gamma_plus": Gp,
        "gamma_minus": Gm,
        "asymmetry": asymmetry,
        "delta_from_minus_8_over_17": delta_from_minus_8_over_17,
    }


def run_convergence_study(
    out_dir: str = ".",
    energy_eV: float = 30.0,
    params: matrix_elements.BenchmarkParams | None = None,
    jobs: int = 1,
    progress: bool = True,
) -> str:
    """Convergence study at one energy: vary R_max, N_r, N_theta, l_max; record A_tot.
    Uses the actual 2D quadrature so N_r and N_theta are active convergence knobs.
    If jobs > 1, configurations are computed in parallel.
    """
    if params is None:
        params = matrix_elements.BenchmarkParams.default()
    E_k_eV = energy_eV - I1_eV
    if E_k_eV <= 0:
        raise ValueError(f"Photon energy {energy_eV} eV is below threshold (I1 ≈ {I1_eV:.2f} eV).")
    E_k_J = constants.eV_to_J(E_k_eV)
    logger.info(
        "Convergence study at photon energy %.1f eV (E_k=%.4f eV), jobs=%d",
        energy_eV, E_k_eV, jobs,
    )

    tasks = []
    # Vary R_max (multiples of a0_sst)
    for R_mult in [20, 50, 100, 150]:
        d = asdict(params)
        d["R_max"] = R_mult * constants.a0_sst
        tasks.append(("R_max", R_mult, d["R_max"], d))
    # Vary N_r
    for N_r in [80, 160, 320, 480]:
        d = asdict(params)
        d["N_r"] = N_r
        tasks.append(("N_r", N_r, N_r, d))
    # Vary N_theta
    for N_theta in [64, 128, 256, 384]:
        d = asdict(params)
        d["N_theta"] = N_theta
        tasks.append(("N_theta", N_theta, N_theta, d))
    # Vary l_max
    for l_max in [2, 4, 6, 8]:
        d = asdict(params)
        d["l_max"] = l_max
        tasks.append(("l_max", l_max, l_max, d))

    n_tasks = len(tasks)
    pbar = tqdm(total=n_tasks, desc="Convergence study", unit="cfg", disable=not progress)

    if jobs <= 1:
        rows = []
        for var, val, val_si, d in tasks:
            row = _compute_one_convergence_row(E_k_J, var, val, val_si, d)
            rows.append(row)
            logger.debug("  %s=%s -> A_tot=%.6f", row["variable"], row["value"], row["A_tot"])
            pbar.update(1)
    else:
        rows = []
        with ProcessPoolExecutor(max_workers=jobs) as executor:
            future_to_task = {
                executor.submit(_compute_one_convergence_row, E_k_J, var, val, val_si, d): (var, val)
                for var, val, val_si, d in tasks
            }
            for future in as_completed(future_to_task):
                row = future.result()
                rows.append(row)
                logger.debug("  %s=%s -> A_tot=%.6f", row["variable"], row["value"], row["A_tot"])
                pbar.update(1)
        # Keep order: R_max, N_r, N_theta, l_max with original value order
        order_key = lambda r: (
            ["R_max", "N_r", "N_theta", "l_max"].index(r["variable"]),
            r["value"],
        )
        rows.sort(key=order_key)
    pbar.close()

    path = os.path.join(out_dir, "convergence_study.csv")
    _save_csv(path, rows, ["variable", "value", "value_SI", "A_tot"])
    return path


# Stronger-control convergence: reference defaults (R_max, N_r, N_theta, l_max)
_STRONGER_REF_R_MAX = 100.0 * constants.a0_sst
_STRONGER_REF_N_R = 320
_STRONGER_REF_N_THETA = 256
_STRONGER_REF_L_MAX = 8

_STRONGER_CONVERGENCE_FIELDNAMES = [
    "sweep_type", "sweep_value", "photon_energy_eV", "eps",
    "R_max_over_a0", "N_r", "N_theta", "l_max",
    "gamma_plus", "gamma_minus", "asymmetry", "delta_from_minus_8_over_17",
]


def run_convergence_study_helical_mode_plus1(
    out_dir: str = ".",
    photon_energy_eV: float = 30.0,
    eps: float = 0.25,
    params: matrix_elements.BenchmarkParams | None = None,
    jobs: int = 1,
    progress: bool = True,
) -> str:
    """Convergence study for the stronger control (helical_mode_plus1, eps=0.25) at one photon energy.
    Varies R_max, N_r, N_theta, l_max in separate sweeps; reference values for non-varied params.
    Shows that the deviation from -8/17 is numerically converged, not a discretization artifact.
    """
    if params is None:
        params = matrix_elements.BenchmarkParams.default()
    E_k_eV = photon_energy_eV - I1_eV
    if E_k_eV <= 0:
        raise ValueError(
            f"Photon energy {photon_energy_eV} eV is below threshold (I1 ≈ {I1_eV:.2f} eV)."
        )
    E_k_J = constants.eV_to_J(E_k_eV)
    logger.info(
        "Stronger-control convergence at omega=%.1f eV (E_k=%.4f eV), eps=%.2f, jobs=%d",
        photon_energy_eV, E_k_eV, eps, jobs,
    )

    def ref_dict() -> dict:
        d = asdict(params)
        d["R_max"] = _STRONGER_REF_R_MAX
        d["N_r"] = _STRONGER_REF_N_R
        d["N_theta"] = _STRONGER_REF_N_THETA
        d["l_max"] = _STRONGER_REF_L_MAX
        return d

    tasks: list[tuple[str, float | int, dict]] = []
    for R_mult in [20, 40, 80, 120, 160]:
        d = ref_dict()
        d["R_max"] = R_mult * constants.a0_sst
        tasks.append(("R_max", R_mult, d))
    for N_r in [80, 160, 240, 320, 480]:
        d = ref_dict()
        d["N_r"] = N_r
        tasks.append(("N_r", N_r, d))
    for N_theta in [64, 128, 192, 256, 384]:
        d = ref_dict()
        d["N_theta"] = N_theta
        tasks.append(("N_theta", N_theta, d))
    for l_max in [2, 4, 6, 8, 10, 12]:
        d = ref_dict()
        d["l_max"] = l_max
        tasks.append(("l_max", l_max, d))

    n_tasks = len(tasks)
    pbar = tqdm(
        total=n_tasks,
        desc="Stronger-control convergence",
        unit="cfg",
        disable=not progress,
    )

    if jobs <= 1:
        rows = []
        for sweep_type, sweep_value, d in tasks:
            row = _compute_one_convergence_row_helical_mode_plus1(
                E_k_J, photon_energy_eV, eps, sweep_type, sweep_value, d,
            )
            rows.append(row)
            logger.debug(
                "  %s=%s -> asymmetry=%.6f, delta=%.6e",
                sweep_type, sweep_value, row["asymmetry"], row["delta_from_minus_8_over_17"],
            )
            pbar.update(1)
    else:
        rows = []
        with ProcessPoolExecutor(max_workers=jobs) as executor:
            future_to_task = {
                executor.submit(
                    _compute_one_convergence_row_helical_mode_plus1,
                    E_k_J, photon_energy_eV, eps, st, sv, d,
                ): (st, sv)
                for st, sv, d in tasks
            }
            for future in as_completed(future_to_task):
                row = future.result()
                rows.append(row)
                logger.debug(
                    "  %s=%s -> asymmetry=%.6f",
                    row["sweep_type"], row["sweep_value"], row["asymmetry"],
                )
                pbar.update(1)
        order_key = lambda r: (
            ["R_max", "N_r", "N_theta", "l_max"].index(r["sweep_type"]),
            r["sweep_value"] if isinstance(r["sweep_value"], (int, float)) else 0,
        )
        rows.sort(key=order_key)
    pbar.close()

    path = os.path.join(out_dir, "convergence_study_helical_mode_plus1.csv")
    _save_csv(path, rows, _STRONGER_CONVERGENCE_FIELDNAMES)

    # Summary: converged A_tot, spread at largest-resolution points, stability statement
    asyms = [float(r["asymmetry"]) for r in rows]
    deltas = [float(r["delta_from_minus_8_over_17"]) for r in rows]
    # Points at largest resolution in each sweep (last value per sweep_type)
    by_sweep = {}
    for r in rows:
        st = r["sweep_type"]
        if st not in by_sweep:
            by_sweep[st] = []
        by_sweep[st].append((r["sweep_value"], float(r["asymmetry"])))
    high_res_asyms = []
    for st in ["R_max", "N_r", "N_theta", "l_max"]:
        if st in by_sweep:
            by_sweep[st].sort(key=lambda x: (x[0] if isinstance(x[0], (int, float)) else 0))
            high_res_asyms.append(by_sweep[st][-1][1])
    spread = max(high_res_asyms) - min(high_res_asyms) if len(high_res_asyms) >= 2 else 0.0
    mean_high = sum(high_res_asyms) / len(high_res_asyms) if high_res_asyms else (asyms[-1] if asyms else 0.0)
    print("")
    print("Stronger-control convergence summary (30 eV, eps=0.25)")
    print("  Approx. converged A_tot:  {:.6g}".format(mean_high))
    print("  Spread at highest resolution (per sweep): {:.2e}".format(spread))
    if spread < 1e-4:
        print("  Stronger-control asymmetry appears numerically stable within ~1e-4.")
    elif spread < 1e-3:
        print("  Stronger-control asymmetry appears numerically stable within ~1e-3.")
    else:
        print("  Stronger-control asymmetry spread at high resolution: {:.2e}.".format(spread))
    print("")

    return path


def main() -> None:
    """Run all benchmark scans and save CSVs. Call print_constants_summary at start.
    Set env SST71_QUICK=1 or use --quick for a fast run (l_max=2, 2 energies, smaller R_max).
    Use --verbose to log most steps; use --debug for additional integration-layer detail.
    """
    parser = argparse.ArgumentParser(
        description="SST-71 helicity asymmetry benchmark: scan energies, run controls, convergence study.",
    )
    parser.add_argument(
        "--quick", "-q",
        action="store_true",
        help="Fast run: l_max=2, 2 energies, R_max=40*a0 (or set SST71_QUICK=1)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Log most steps: per-energy results, file saves, convergence points",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Log debug detail from integration layer (grid sizes, path choice, per-call rates)",
    )
    parser.add_argument(
        "--jobs", "-j",
        type=int,
        default=1,
        metavar="N",
        help="Number of worker processes for parallel runs (energy scan and convergence study). Default 1 (sequential).",
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress bar (e.g. for CI or when redirecting output).",
    )
    args = parser.parse_args()

    if args.jobs < 1:
        parser.error("--jobs must be >= 1")

    # Show progress bar only when not verbose/debug (logs would clash) and not --no-progress
    progress = not args.no_progress and not args.verbose and not args.debug

    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
        logging.getLogger("matrix_elements").setLevel(logging.DEBUG)
    elif args.verbose:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
        logging.getLogger("matrix_elements").setLevel(logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

    quick = (
        os.environ.get("SST71_QUICK", "").strip().lower() in ("1", "true", "yes")
        or args.quick
    )
    constants.print_constants_summary()
    if getattr(matrix_elements, "_CPP_AVAILABLE", False):
        print("Axisymmetric runs will use sst_benchmark_core (C++).")
    else:
        print("C++ extension not loaded; axisymmetric runs use Python fallback.")
    out_dir = os.path.dirname(os.path.abspath(__file__))
    if quick:
        energies_eV = np.array([20.0, 50.0])
        params = matrix_elements.BenchmarkParams.default()
        params.l_max = 2
        params.R_max = 40.0 * constants.a0_sst
        print("Quick mode: l_max=2, 2 energies, R_max=40*a0")
        # Broken-axisymmetry uses slow 3D integral; in quick mode use 1 energy only
        energies_broken_eV = np.array([30.0])
    else:
        energies_eV = np.linspace(15.0, 100.0, 6)
        params = None
        energies_broken_eV = None  # same as main scan

    if args.jobs > 1:
        print(f"Using {args.jobs} worker processes for parallel runs.")
    print("Running main benchmark (helical, axisymmetric)...")
    run_main_benchmark(out_dir, energies_eV=energies_eV, params=params, jobs=args.jobs, progress=progress)
    print("Running control: no anticommutator...")
    run_control_no_anticommutator(out_dir, energies_eV=energies_eV, params=params, jobs=args.jobs, progress=progress)
    print("Running control: non-helical probe...")
    run_control_non_helical(out_dir, energies_eV=energies_eV, params=params, jobs=args.jobs, progress=progress)
    print("Running control: stronger (helical_mode_plus1, eps=0.25)...")
    run_control_helical_mode_plus1(
        out_dir, eps=0.25,
        energies_eV=energies_eV, params=params, jobs=args.jobs, progress=progress,
    )
    print("Running epsilon scan at 30 eV (helical_mode_plus1)...")
    run_control_helical_mode_plus1_eps_scan(
        out_dir, omega_eV=30.0, params=params, progress=progress,
    )
    print("Running control: broken axisymmetry (secondary, eps=0.2)...")
    run_control_broken_axisymmetry(
        out_dir, eps=0.2,
        energies_eV=energies_broken_eV if quick else energies_eV,
        params=params, jobs=args.jobs, progress=progress,
    )
    print("Running convergence study at 30 eV...")
    run_convergence_study(out_dir, energy_eV=30.0, params=params, jobs=args.jobs, progress=progress)
    if not quick:
        print("Running stronger-control convergence study (30 eV, eps=0.25)...")
        run_convergence_study_helical_mode_plus1(
            out_dir, photon_energy_eV=30.0, eps=0.25, params=params,
            jobs=args.jobs, progress=progress,
        )
    else:
        print("Skipping stronger-control convergence study in quick mode.")
    print("Done. CSVs saved in", out_dir)


if __name__ == "__main__":
    main()
