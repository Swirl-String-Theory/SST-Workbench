"""Write and discover raw a_m(t) before any predictor post-processing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from . import __version__
from .residual import sha256_obj

SCHEMA = "SST_RAW_MODAL_TIMESERIES-1.0"
NO_RAW = "INDETERMINATE_NO_RAW_MODAL_TIMESERIES"
SERIES_GLOBS = (
    "**/raw_modal_timeseries*.json",
    "**/raw_timeseries/*.json",
    "**/*_raw_am.json",
)
EXCLUDE_PARTS = {"paper_upgrade", ".venv", "__pycache__", "private_reveal_keys"}


def spatial_basis_hash(vector) -> str:
    import hashlib

    payload = json.dumps([float(x) for x in np.asarray(vector, dtype=float).ravel()], separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def write_raw_modal_timeseries(
    path: Path | str,
    *,
    t,
    a,
    source_id: str,
    spatial_basis,
    spatial_mode_basis_source: str = "model_conditioned_frozen",
    carrier_group_token: str | None = None,
    scientific: bool = False,
    selftest: bool = False,
    predicted_omega_used_in_extraction: bool = False,
    predicted_vg_used_in_extraction: bool = False,
    predicted_omega_used_for_demodulation: bool = False,
    predicted_omega_used_for_bandpass: bool = False,
    synthetic_wavepacket_used: bool = False,
    written_before_predictor_postprocess: bool = True,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    t = np.asarray(t, dtype=float)
    a = np.asarray(a, dtype=complex)
    if t.size != a.size:
        raise ValueError("t and a_m must have the same length")
    if scientific and selftest:
        raise ValueError("SELFTEST series cannot be marked scientific")
    record = {
        "schema": SCHEMA,
        "schema_version": "1.0",
        "record_type": "raw_modal_timeseries",
        "source_id": source_id,
        "provider_id": "A029",
        "carrier_group_token": carrier_group_token,
        "t": [float(x) for x in t],
        "a_real": [float(z.real) for z in a],
        "a_imag": [float(z.imag) for z in a],
        "spatial_mode_basis_source": spatial_mode_basis_source,
        "spatial_basis_hash": spatial_basis_hash(spatial_basis),
        "written_before_predictor_postprocess": bool(written_before_predictor_postprocess),
        "predicted_omega_used_in_extraction": bool(predicted_omega_used_in_extraction),
        "predicted_vg_used_in_extraction": bool(predicted_vg_used_in_extraction),
        "predicted_omega_used_for_demodulation": bool(predicted_omega_used_for_demodulation),
        "predicted_omega_used_for_bandpass": bool(predicted_omega_used_for_bandpass),
        "synthetic_wavepacket_used": bool(synthetic_wavepacket_used),
        "scientific": bool(scientific),
        "selftest": bool(selftest),
        "code_hash": sha256_obj({"module": "raw_timeseries", "version": __version__}),
        **(extra or {}),
    }
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return record


def load_raw_modal_timeseries(path: Path | str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def series_is_contaminated(record: dict[str, Any]) -> bool:
    return bool(
        not record.get("written_before_predictor_postprocess")
        or record.get("predicted_omega_used_in_extraction")
        or record.get("predicted_vg_used_in_extraction")
        or record.get("predicted_omega_used_for_demodulation")
        or record.get("predicted_omega_used_for_bandpass")
        or record.get("synthetic_wavepacket_used")
    )


def series_is_scientific(record: dict[str, Any]) -> bool:
    return bool(record.get("scientific")) and not record.get("selftest") and not series_is_contaminated(record)


def find_raw_modal_timeseries(*roots: Path | str) -> list[Path]:
    hits: list[Path] = []
    for root in roots:
        if root is None:
            continue
        path = Path(root)
        if path.is_file() and path.suffix == ".json":
            hits.append(path.resolve())
            continue
        if not path.exists():
            continue
        for pattern in SERIES_GLOBS:
            for candidate in path.glob(pattern):
                if candidate.is_file() and not any(part in EXCLUDE_PARTS for part in candidate.parts):
                    hits.append(candidate.resolve())
    return sorted(set(hits))


def load_scientific_series(paths: Iterable[Path]) -> list[dict[str, Any]]:
    rows = []
    for path in paths:
        try:
            rec = load_raw_modal_timeseries(path)
        except (OSError, json.JSONDecodeError):
            continue
        if rec.get("schema") != SCHEMA:
            continue
        rec["_path"] = str(path)
        if series_is_scientific(rec):
            rows.append(rec)
    return rows
