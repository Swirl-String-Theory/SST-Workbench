"""Validate P2.6 bridge / reconstruction / tube certificates without jsonschema."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

BRIDGE = "SST_STATE_SPACE_BRIDGE-1.0"
RECON = "SST_MODE_RECONSTRUCTION-1.0"
TUBE = "SST_TUBE_VALIDITY-1.0"

BRIDGE_STATUSES = {
    "BRIDGE_QUALIFIED",
    "BRIDGE_REJECTED",
    "INDETERMINATE_MODE_RECONSTRUCTION",
    "INDETERMINATE_TUBE_CHART_INVALID",
    "INDETERMINATE_INSUFFICIENT_STATE",
    "INDETERMINATE_NO_VALID_PRODUCER",
}
RECON_STATUSES = {"RECONSTRUCTED_SAME_BRANCH", "INDETERMINATE_MODE_RECONSTRUCTION"}
TUBE_STATUSES = {"TUBE_VALID", "INDETERMINATE_TUBE_CHART_INVALID"}

BRIDGE_REQUIRED = (
    "schema",
    "schema_version",
    "record_type",
    "status",
    "prediction_inputs_consumed",
    "scientific_amplitude",
    "d_bridge",
    "d_score",
    "holdout_scoring_enabled",
    "bridge_rejected_falsifies_a029_clock",
)
RECON_REQUIRED = (
    "schema",
    "schema_version",
    "record_type",
    "status",
    "carrier_id",
    "q_hash",
    "p_hash",
    "biorthogonality_residual",
)
TUBE_REQUIRED = (
    "schema",
    "schema_version",
    "record_type",
    "status",
    "rmax",
    "rmax_was_reduced",
    "c_kappa",
    "c_d",
)


class BridgeCertError(ValueError):
    pass


def _require(obj: dict[str, Any], keys: tuple[str, ...]) -> None:
    missing = [k for k in keys if k not in obj]
    if missing:
        raise BridgeCertError(f"missing fields: {missing}")


def _hex64(value: Any, name: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise BridgeCertError(f"{name} must be 64 hex chars")


def validate_bridge_certificate(record: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise BridgeCertError("record must be an object")
    schema = record.get("schema")
    if schema == BRIDGE:
        return _validate_bridge(record)
    if schema == RECON:
        return _validate_recon(record)
    if schema == TUBE:
        return _validate_tube(record)
    raise BridgeCertError(f"unknown schema: {schema}")


def _validate_bridge(record: dict[str, Any]) -> dict[str, Any]:
    _require(record, BRIDGE_REQUIRED)
    if record["schema_version"] != "1.0" or record["record_type"] != "state_space_bridge":
        raise BridgeCertError("record_type/schema_version mismatch")
    if record["status"] not in BRIDGE_STATUSES:
        raise BridgeCertError(f"unknown bridge status: {record['status']}")
    consumed = record["prediction_inputs_consumed"]
    if not isinstance(consumed, list) or consumed:
        raise BridgeCertError("prediction_inputs_consumed must be []")
    if record["scientific_amplitude"] != "left_eigenvector_Wr_B":
        raise BridgeCertError("scientific amplitude must be left_eigenvector_Wr_B")
    if record["bridge_rejected_falsifies_a029_clock"] is not False:
        raise BridgeCertError("BRIDGE_REJECTED must not falsify the A029 clock")
    if record["status"] == "BRIDGE_QUALIFIED" and record.get("holdout_scoring_enabled"):
        if not record.get("d_score"):
            raise BridgeCertError("holdout scoring requires a non-empty D_score")
    d_bridge = set(record["d_bridge"] or [])
    d_score = set(record["d_score"] or [])
    if d_bridge & d_score:
        raise BridgeCertError("D_bridge and D_score must be disjoint")
    return {"ok": True, "schema": BRIDGE, "status": record["status"]}


def _validate_recon(record: dict[str, Any]) -> dict[str, Any]:
    _require(record, RECON_REQUIRED)
    if record["schema_version"] != "1.0" or record["record_type"] != "mode_reconstruction":
        raise BridgeCertError("record_type/schema_version mismatch")
    if record["status"] not in RECON_STATUSES:
        raise BridgeCertError(f"unknown reconstruction status: {record['status']}")
    _hex64(record["q_hash"], "q_hash")
    _hex64(record["p_hash"], "p_hash")
    return {"ok": True, "schema": RECON, "status": record["status"]}


def _validate_tube(record: dict[str, Any]) -> dict[str, Any]:
    _require(record, TUBE_REQUIRED)
    if record["schema_version"] != "1.0" or record["record_type"] != "tube_validity":
        raise BridgeCertError("record_type/schema_version mismatch")
    if record["status"] not in TUBE_STATUSES:
        raise BridgeCertError(f"unknown tube status: {record['status']}")
    if record["rmax_was_reduced"] is not False:
        raise BridgeCertError("r_max must not be reduced after a tube fail")
    return {"ok": True, "schema": TUBE, "status": record["status"]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    args = ap.parse_args()
    rec = json.loads(Path(args.path).read_text(encoding="utf-8"))
    print(json.dumps(validate_bridge_certificate(rec), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
