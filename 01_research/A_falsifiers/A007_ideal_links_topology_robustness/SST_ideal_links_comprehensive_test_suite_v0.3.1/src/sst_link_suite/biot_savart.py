from __future__ import annotations
from itertools import product
import numpy as np
from .native_ext import BackendOptions
from .native_ext.core import link_velocity_batch, neumann_coupling_matrices


def sign_configurations(m: int) -> list[tuple[int, ...]]:
    return list(product((-1, 1), repeat=m))


def sign_matrix(m: int) -> np.ndarray:
    return np.asarray(sign_configurations(m), dtype=float)


def _cross_matrix_for_omega(q: np.ndarray) -> np.ndarray:
    x, y, z = q
    return np.array([[0, z, -y], [-z, 0, x], [y, -x, 0]], dtype=float)


def fit_normal_rigid_motion(samples, velocities) -> dict:
    all_r = np.concatenate([s.r for s in samples], axis=0)
    center = all_r.mean(axis=0)
    rows, rhs = [], []
    normal_u2 = total_u2 = tang_u2 = 0.0
    for s, u in zip(samples, velocities):
        tang = s.d1 / np.maximum(np.linalg.norm(s.d1, axis=1)[:, None], 1e-300)
        for r, t, v in zip(s.r, tang, u):
            projector = np.eye(3) - np.outer(t, t)
            matrix = np.concatenate(
                [np.eye(3), _cross_matrix_for_omega(r-center)], axis=1
            )
            rows.append(projector @ matrix)
            rhs.append(projector @ v)
            normal_velocity = projector @ v
            normal_u2 += float(normal_velocity @ normal_velocity)
            total_u2 += float(v @ v)
            tang_u2 += float((v @ t)**2)
    matrix = np.concatenate(rows, axis=0)
    vector = np.concatenate(rhs, axis=0)
    solution, *_ = np.linalg.lstsq(matrix, vector, rcond=None)
    residual = matrix @ solution - vector
    rms = float(np.sqrt(np.mean(residual**2)))
    normal_rms = float(np.sqrt(normal_u2 / max(len(all_r), 1)))
    return {
        "translation": solution[:3],
        "omega": solution[3:],
        "translation_norm": float(np.linalg.norm(solution[:3])),
        "omega_norm": float(np.linalg.norm(solution[3:])),
        "normal_rigid_residual_rms": rms,
        "normal_velocity_rms": normal_rms,
        "relative_equilibrium_score": float(rms / max(normal_rms, 1e-300)),
        "tangential_energy_fraction": float(tang_u2 / max(total_u2, 1e-300)),
    }


def geometric_impulse(samples, signs: tuple[int, ...] | np.ndarray) -> np.ndarray:
    out = np.zeros(3)
    for sample, sign in zip(samples, signs):
        nxt = np.roll(sample.r, -1, axis=0)
        out += 0.5 * sign * np.sum(np.cross(sample.r, nxt-sample.r), axis=0)
    return out


def analyze_sign_configurations(
    samples,
    epsilons: list[float],
    backend_options: BackendOptions,
    linking_matrix: np.ndarray | None = None,
    local_skip_velocity: int = 3,
    local_skip_energy: int = 2,
) -> tuple[list[dict], dict]:
    curves = [np.ascontiguousarray(sample.r, dtype=float) for sample in samples]
    sectors = sign_matrix(len(samples))
    couplings, energy_backend = neumann_coupling_matrices(
        curves, epsilons, local_skip_energy, backend_options
    )
    out = []
    coupling_rows = []
    for epsilon_index, epsilon in enumerate(epsilons):
        coupling = couplings[epsilon_index]
        self_energy = float(np.trace(coupling))
        coupling_rows.append({
            "epsilon_D": float(epsilon),
            "backend": energy_backend,
            "coupling_matrix": coupling,
            "self_energy_trace_proxy": self_energy,
            "mutual_coupling_sum_proxy": float(coupling.sum() - np.trace(coupling)),
            "symmetry_error": float(np.max(np.abs(coupling - coupling.T))),
        })
        velocity_batches, velocity_backend = link_velocity_batch(
            curves, sectors, epsilon, local_skip_velocity, backend_options
        )
        if velocity_backend != energy_backend:
            raise RuntimeError(
                f"Mixed Biot-Savart backends are forbidden: velocity={velocity_backend}, "
                f"energy={energy_backend}"
            )
        for sector_index, signs_float in enumerate(sectors):
            signs = tuple(int(x) for x in signs_float)
            velocities = [batch[sector_index] for batch in velocity_batches]
            fit = fit_normal_rigid_motion(samples, velocities)
            impulse = geometric_impulse(samples, signs_float)
            energy = float(signs_float @ coupling @ signs_float)
            mutual_energy = energy - self_energy
            helicity = (
                float(signs_float @ np.asarray(linking_matrix) @ signs_float)
                if linking_matrix is not None else float("nan")
            )
            out.append({
                "backend": velocity_backend,
                "signs": list(signs),
                "circulation_class": "co-oriented" if abs(sum(signs)) == len(signs) else "mixed",
                "epsilon_D": float(epsilon),
                "local_skip_velocity": int(local_skip_velocity),
                "local_skip_energy": int(local_skip_energy),
                **fit,
                "impulse_D2": impulse,
                "impulse_norm_D2": float(np.linalg.norm(impulse)),
                "neumann_energy_proxy": energy,
                "neumann_self_energy_proxy": self_energy,
                "neumann_mutual_energy_proxy": mutual_energy,
                "mutual_energy_fraction": float(mutual_energy / max(abs(energy), 1e-300)),
                "pair_helicity_proxy_Gamma2": helicity,
            })

    by_key = {
        (tuple(row["signs"]), row["epsilon_D"]): row
        for row in out
    }
    reversal_errors = []
    for row in out:
        signs = tuple(row["signs"])
        partner = by_key[(tuple(-x for x in signs), row["epsilon_D"])]
        reversal_errors.append({
            "signs": list(signs),
            "epsilon_D": row["epsilon_D"],
            "energy_abs_error": abs(row["neumann_energy_proxy"] - partner["neumann_energy_proxy"]),
            "relative_equilibrium_abs_error": abs(
                row["relative_equilibrium_score"] - partner["relative_equilibrium_score"]
            ),
            "impulse_odd_abs_error": float(np.linalg.norm(
                np.asarray(row["impulse_D2"]) + np.asarray(partner["impulse_D2"])
            )),
            "omega_norm_abs_error": abs(row["omega_norm"] - partner["omega_norm"]),
            "translation_norm_abs_error": abs(
                row["translation_norm"] - partner["translation_norm"]
            ),
        })
    diagnostics = {
        "backend": energy_backend,
        "coupling_matrices": coupling_rows,
        "global_reversal_checks": reversal_errors,
        "global_reversal_max_energy_error": max(x["energy_abs_error"] for x in reversal_errors),
        "global_reversal_max_relative_equilibrium_error": max(
            x["relative_equilibrium_abs_error"] for x in reversal_errors
        ),
        "global_reversal_max_impulse_odd_error": max(
            x["impulse_odd_abs_error"] for x in reversal_errors
        ),
    }
    return out, diagnostics

