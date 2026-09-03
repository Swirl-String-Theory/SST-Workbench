from __future__ import annotations
import argparse, math, random
from .common import write_csv

def action(path, kind):
    rng = random.Random(12)
    rows = []
    Jstar = 0.371828  # arbitrary dimensionless control, not an SST/Planck constant
    for carrier in range(4):
        epsRE = 0.02 + 0.001 * carrier
        for N in [64, 96, 128]:
            for amp in [0.002, 0.003, 0.004, 0.006]:
                f = 1.2 * (1 + 0.1 * carrier) * (1 + 0.0003 * (128 - N))
                if kind == "positive":
                    dE = Jstar * f * (1 + rng.gauss(0, 0.004))
                elif kind == "classical":
                    dE = 0.7 * amp**2 * (1 + rng.gauss(0, 0.005))
                else:
                    dE = Jstar * f * (1 + rng.gauss(0, 0.2))
                rows.append({
                    "case_index": carrier,
                    "source_name": f"carrier{carrier}",
                    "source_path": "synthetic",
                    "family_hint": "synthetic",
                    "resolution_N": N,
                    "amplitude_hat": amp,
                    "delta_E_hat": dE,
                    "base_energy_hat": 2.0,
                    "delta_E_over_abs_base": dE / 2.0,
                    "energy_signal_valid": True,
                    "frequency_hat": f,
                    "omega_hat": 2 * math.pi * f,
                    "fft_bin_index": 3,
                    "frequency_window_limited": False,
                    "frequency_auto_extended": False,
                    "effective_t_final_hat": 8.0 / f,
                    "spectral_power": 0.85,
                    "cycles": 8,
                    "period_cv": 0.03,
                    "harmonic_r2": 0.95,
                    "pod_discovery_fraction": 0.8,
                    "epsilon_RE": epsRE,
                    "mesh_cv_plus": 0.03,
                    "mesh_cv_minus": 0.03,
                    "dt_hat_min": 1e-5,
                    "dt_hat_max": 1e-5,
                    "n_steps": 1000,
                    "normalization_L_hat": 1.0,
                    "normalization_Gamma_hat": 1.0,
                    "core_fraction_hat": 0.05,
                    "temporal_frequency_rel_change": 0.002,
                })
    write_csv(path, rows)

def closure(path, good=True):
    # External closure control remains target-free; these numbers are arbitrary test data.
    rng = random.Random(3)
    rows = []
    for i in range(20):
        a = 0.8 + 0.03 * i
        w = 2.0 / a**2 * (1 + rng.gauss(0, 0.005 if good else 0.15))
        MI = 1.0 * (1 + 0.01 * i)
        ME = MI * (1 + rng.gauss(0, 0.01 if good else 0.12))
        Cp = 2.0 * MI * (1 + rng.gauss(0, 0.01 if good else 0.2))
        bk = 1.0 * (1 + rng.gauss(0, 0.01))
        bf = bk * (1 + rng.gauss(0, 0.01 if good else 0.15))
        dr = rng.gauss(0, 2e-7 if good else 1e-4)
        rows.append({
            "scale_a": a,
            "omega_rad_s": w,
            "M_E_kg": ME,
            "M_I_kg": MI,
            "C_p": Cp,
            "beta_knot": bk,
            "beta_fluid": bf,
            "energy_drift_rel": dr,
        })
    write_csv(path, rows)

def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "kind",
        choices=[
            "action-positive",
            "action-classical",
            "action-noisy",
            "closure-positive",
            "closure-negative",
        ],
    )
    p.add_argument("out")
    a = p.parse_args()
    if a.kind.startswith("action-"):
        action(a.out, a.kind.split("-", 1)[1])
    else:
        closure(a.out, a.kind.endswith("positive"))

if __name__ == "__main__":
    main()
