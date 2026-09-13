"""Validate SST_RAW_MODAL_TIMESERIES-1.0 records without jsonschema."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA_NAME = "SST_RAW_MODAL_TIMESERIES-1.0"
REQUIRED = (
    "schema",
    "schema_version",
    "record_type",
    "source_id",
    "t",
    "a_real",
    "a_imag",
    "spatial_mode_basis_source",
    "spatial_basis_hash",
    "written_before_predictor_postprocess",
    "predicted_omega_used_in_extraction",
    "predicted_vg_used_in_extraction",
    "predicted_omega_used_for_demodulation",
    "predicted_omega_used_for_bandpass",
    "synthetic_wavepacket_used",
    "scientific",
)
BASIS = {"model_conditioned_frozen", "measurement_fixed", "unavailable"}


class TimeseriesError(ValueError):
    pass


def load_schema(path: Path | None = None) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    schema_path = path or root / "10_docs" / "registry" / "schemas" / f"{SCHEMA_NAME}.json"
    return json.loads(schema_path.read_text(encoding="utf-8"))


def spatial_basis_hash(vector) -> str:
    payload = json.dumps([float(x) for x in vector], separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _require(obj: dict[str, Any], keys: tuple[str, ...]) -> None:
    missing = [k for k in keys if k not in obj]
    if missing:
        raise TimeseriesError(f"missing fields: {missing}")


def validate_raw_timeseries(record: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise TimeseriesError("record must be an object")
    _require(record, REQUIRED)
    if record["schema"] != SCHEMA_NAME:
        raise TimeseriesError("schema mismatch")
    if record["schema_version"] != "1.0" or record["record_type"] != "raw_modal_timeseries":
        raise TimeseriesError("record_type/schema_version mismatch")
    t, re, im = record["t"], record["a_real"], record["a_imag"]
    if not isinstance(t, list) or len(t) < 2:
        raise TimeseriesError("t must have at least two samples")
    if len(re) != len(t) or len(im) != len(t):
        raise TimeseriesError("t, a_real, and a_imag must have the same length")
    if record["spatial_mode_basis_source"] not in BASIS:
        raise TimeseriesError("unknown spatial_mode_basis_source")
    digest = record["spatial_basis_hash"]
    if not isinstance(digest, str) or len(digest) != 64:
        raise TimeseriesError("spatial_basis_hash must be 64 hex chars")
    if record["scientific"] and record.get("selftest"):
        raise TimeseriesError("a SELFTEST series cannot be scientific")
    if record["spatial_mode_basis_source"] == "model_conditioned_frozen" and record.get("fully_model_independent"):
        raise TimeseriesError("a frozen modal spatial basis is not fully model-independent")
    contaminated = (
        not record["written_before_predictor_postprocess"]
        or record["predicted_omega_used_in_extraction"]
        or record["predicted_vg_used_in_extraction"]
        or record["predicted_omega_used_for_demodulation"]
        or record["predicted_omega_used_for_bandpass"]
        or record["synthetic_wavepacket_used"]
    )
    if record["scientific"] and contaminated:
        raise TimeseriesError("scientific series cannot use predictor post-processing")
    return {"ok": True, "n": len(t), "scientific": bool(record["scientific"]), "contaminated": bool(contaminated)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    args = ap.parse_args()
    rec = json.loads(Path(args.path).read_text(encoding="utf-8"))
    print(json.dumps(validate_raw_timeseries(rec), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
