from __future__ import annotations

from collections import defaultdict
from typing import Any

import numpy as np

from .io import ffloat


def infer_empirical_couplings(rows: list[dict[str, str]], sigma_threshold: float, min_fraction: float) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[tuple[float, float, float]]] = defaultdict(list)
    for row in rows:
        drive = ffloat(row, "drive_energy_eV")
        delta = ffloat(row, "delta_energy_eV")
        noise = ffloat(row, "noise_eV", 0.0) or 0.0
        if drive is None or delta is None or drive <= 0:
            continue
        grouped[(row["knot"], row["mode_id"])].append((drive, delta, noise))
    out = []
    for (knot, mode_id), vals in sorted(grouped.items()):
        fractions = [abs(d) / drv for drv, d, _ in vals]
        sigmas = [abs(d) / n if n > 0 else float("inf") for _, d, n in vals]
        frac = float(np.median(fractions))
        sigma = float(np.median(sigmas))
        coupled = sigma >= sigma_threshold and frac >= min_fraction
        out.append({
            "knot": knot,
            "mode_id": mode_id,
            "coupled": bool(coupled),
            "median_transfer_fraction": frac,
            "median_sigma": sigma,
            "n_encounters": len(vals),
        })
    return out


def three_gate(coupling_norm: float | None, gap_eV: float | None, tau_s: float | None, drive_energy_eV: float, observation_time_s: float, coupling_threshold: float) -> dict[str, bool | None]:
    coupling_gate = None if coupling_norm is None else abs(coupling_norm) >= coupling_threshold
    energy_gate = None if gap_eV is None else drive_energy_eV >= gap_eV
    time_gate = None if tau_s is None else tau_s <= observation_time_s
    all_known = coupling_gate is not None and energy_gate is not None and time_gate is not None
    return {
        "coupling_gate": coupling_gate,
        "energy_gate": energy_gate,
        "time_gate": time_gate,
        "active": bool(coupling_gate and energy_gate and time_gate) if all_known else None,
    }
