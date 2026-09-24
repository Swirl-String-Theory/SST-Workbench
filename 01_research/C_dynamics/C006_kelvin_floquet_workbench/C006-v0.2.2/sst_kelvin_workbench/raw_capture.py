"""Write raw X(t) and SST_RAW_MODAL_TIMESERIES-1.0 only after a QUALIFIED bridge."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from .backend import load_backend
from .kelvin import make_ring, perturb_ring, single_rhs_hat
from .orbit import rk4_step
from .paths import complex_hash, sha256_obj


def capture_ring_trajectory(
    *,
    n: int = 48,
    amplitude: complex = 1e-3,
    dt_hat: float = 0.01,
    time_hat: float = 0.24,
    sample_stride: int = 2,
) -> dict[str, Any]:
    backend, name = load_backend(force_python=True, skip_build=True)
    base = make_ring(n, 1.0)
    x = perturb_ring(base, {1: amplitude})
    rhs = lambda q: single_rhs_hat(q, radius=1.0, gamma=1.0, eps_over_R=0.05, backend=backend)
    times = []
    curves = []
    nsteps = int(np.ceil(time_hat / dt_hat))
    for step in range(nsteps + 1):
        if step % sample_stride == 0:
            times.append(step * dt_hat)
            curves.append(x.copy())
        if step == nsteps:
            break
        x = rk4_step(x, dt_hat, rhs)
    return {
        "backend": name,
        "t": np.asarray(times, dtype=float),
        "X": np.asarray(curves, dtype=float),
        "X_ref": base,
        "prediction_inputs_consumed": [],
    }


def write_raw_modal_timeseries(
    path: Path,
    *,
    t,
    a,
    source_id: str,
    spatial_basis,
    scientific: bool,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    extra = extra or {}
    if scientific:
        if extra.get("bridge_status") != "BRIDGE_QUALIFIED":
            raise ValueError("scientific series require BRIDGE_QUALIFIED")
        if extra.get("mode_recon_status") != "RECONSTRUCTED_SAME_BRANCH":
            raise ValueError("scientific series require RECONSTRUCTED_SAME_BRANCH")
        if extra.get("tube_status") != "TUBE_VALID":
            raise ValueError("scientific series require TUBE_VALID")
        if extra.get("prediction_inputs_consumed"):
            raise ValueError("scientific series cannot consume prediction inputs")
        if extra.get("d_bridge_record") and extra.get("scored"):
            raise ValueError("D_bridge records must not be scored")
    t = np.asarray(t, dtype=float)
    a = np.asarray(a, dtype=complex)
    record = {
        "schema": "SST_RAW_MODAL_TIMESERIES-1.0",
        "schema_version": "1.0",
        "record_type": "raw_modal_timeseries",
        "source_id": source_id,
        "provider_id": "C006",
        "t": [float(x) for x in t],
        "a_real": [float(z.real) for z in a],
        "a_imag": [float(z.imag) for z in a],
        "spatial_mode_basis_source": "model_conditioned_frozen",
        "spatial_basis_hash": complex_hash(spatial_basis),
        "written_before_predictor_postprocess": True,
        "predicted_omega_used_in_extraction": False,
        "predicted_vg_used_in_extraction": False,
        "predicted_omega_used_for_demodulation": False,
        "predicted_omega_used_for_bandpass": False,
        "synthetic_wavepacket_used": False,
        "scientific": bool(scientific),
        "selftest": False,
        "prediction_inputs_consumed": list(extra.get("prediction_inputs_consumed", [])),
        "bridge_status": extra.get("bridge_status"),
        "mode_recon_status": extra.get("mode_recon_status"),
        "tube_status": extra.get("tube_status"),
        "scored": False,
        "d_set": extra.get("d_set", "D_bridge"),
        "code_hash": sha256_obj({"module": "raw_capture", "version": "0.2.1"}),
    }
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return record


def write_state_npz(path: Path, capture: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, t=capture["t"], X=capture["X"], X_ref=capture["X_ref"])
