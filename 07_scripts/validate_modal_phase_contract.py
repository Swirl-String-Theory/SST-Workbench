"""Validate SST_MODAL_PHASE_CONTRACT-1.0 records without a jsonschema dependency."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

SCHEMA_NAME = "SST_MODAL_PHASE_CONTRACT-1.0"
SCHEMA_VERSION = "1.0"
RECORD_TYPES = (
    "curvature_bridge",
    "symmetry_blocks",
    "dispersion_branch",
    "phase_observation",
)
IDENTITY_REQUIRED = (
    "schema",
    "schema_version",
    "record_type",
    "source_id",
    "parent_hashes",
    "code_hash",
    "blind_status",
)
BLIND_STATUSES = {
    "unblinded",
    "pair_identity_blind",
    "prediction_locked",
    "retrospective_prediction_locked",
    "not_applicable",
}
TARGET_INDEPENDENCE_CLASSES = {
    "fully_model_independent_time_domain",
    "independent_time_domain_given_frozen_spatial_mode",
    "derived_from_predictors",
    "unavailable",
}
TAU_INDEPENDENCE_CLASSES = {
    "raw_trajectory_phase_blind",
    "model_conditioned",
    "derived_from_predicted_dispersion",
    "unavailable",
}
RAW_CONVENTION = "lambda_raw = sigma - i*omega"
CANONICAL_CONVENTION = "mu = sigma + i*omega"
DEFAULT_CONV_TOL = 1e-12


class ContractError(ValueError):
    """A modal-phase contract violation."""


def load_schema(path: Path | None = None) -> dict[str, Any]:
    if path is None:
        path = Path(__file__).resolve().parents[1] / "10_docs" / "registry" / "schemas" / "SST_MODAL_PHASE_CONTRACT-1.0.json"
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def canonical_json_hash(obj: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(obj)).hexdigest()


def wrap_angle(phi: float) -> float:
    return (float(phi) + math.pi) % (2.0 * math.pi) - math.pi


def convention_bridge(
    lambda_real: float,
    lambda_imag: float,
    *,
    omega: float | None = None,
    tol: float = DEFAULT_CONV_TOL,
) -> dict[str, Any]:
    """Map raw λ = σ − iω onto canonical μ = σ + iω. Never rename fields to lambda."""
    sigma = float(lambda_real)
    omega_from_imag = -float(lambda_imag)
    if omega is None:
        omega_used = omega_from_imag
    else:
        omega_used = float(omega)
        if abs(omega_used - omega_from_imag) > max(tol, 1e-15 * (1.0 + abs(omega_from_imag))):
            raise ContractError(
                f"omega ({omega_used}) disagrees with -Im(lambda_raw) ({omega_from_imag})"
            )
    return {
        "eigenvalue_raw": {
            "real": sigma,
            "imag": float(lambda_imag),
            "convention": RAW_CONVENTION,
        },
        "sigma": sigma,
        "omega": omega_used,
        "canonical_complex": {
            "real": sigma,
            "imag": omega_used,
            "convention": CANONICAL_CONVENTION,
        },
    }


def _require(record: dict[str, Any], keys: tuple[str, ...] | list[str], where: str) -> None:
    missing = [k for k in keys if k not in record]
    if missing:
        raise ContractError(f"{where}: missing required fields {missing}")


def _check_identity(record: dict[str, Any]) -> None:
    _require(record, IDENTITY_REQUIRED, "identity")
    if record["schema"] != SCHEMA_NAME:
        raise ContractError(f"schema must be {SCHEMA_NAME}")
    if record["schema_version"] != SCHEMA_VERSION:
        raise ContractError(f"schema_version must be {SCHEMA_VERSION}")
    if record["record_type"] not in RECORD_TYPES:
        raise ContractError(f"unknown record_type {record['record_type']!r}")
    if not str(record["source_id"]).strip():
        raise ContractError("source_id must be non-empty")
    if not isinstance(record["parent_hashes"], dict):
        raise ContractError("parent_hashes must be an object")
    if not str(record["code_hash"]).strip() or len(str(record["code_hash"])) < 8:
        raise ContractError("code_hash must be a hash string of length >= 8")
    if record["blind_status"] not in BLIND_STATUSES:
        raise ContractError(f"unknown blind_status {record['blind_status']!r}")


def _check_convention(record: dict[str, Any], *, tol: float = DEFAULT_CONV_TOL) -> None:
    _require(record, ("eigenvalue_raw", "sigma", "omega", "canonical_complex"), "eigen_convention")
    raw = record["eigenvalue_raw"]
    can = record["canonical_complex"]
    if raw.get("convention") != RAW_CONVENTION:
        raise ContractError("eigenvalue_raw.convention mismatch")
    if can.get("convention") != CANONICAL_CONVENTION:
        raise ContractError("canonical_complex.convention mismatch")
    rebuilt = convention_bridge(raw["real"], raw["imag"], omega=record["omega"], tol=tol)
    if abs(rebuilt["sigma"] - float(record["sigma"])) > tol:
        raise ContractError("sigma must equal Re(lambda_raw)")
    if abs(rebuilt["canonical_complex"]["imag"] - float(can["imag"])) > tol:
        raise ContractError("canonical imag must equal omega")
    if abs(float(can["real"]) - float(record["sigma"])) > tol:
        raise ContractError("canonical real must equal sigma")


def _check_target_independence(obj: Any) -> None:
    if not isinstance(obj, dict):
        raise ContractError("target_independence must be an object")
    _require(obj, ("class", "predicted_omega_used_in_extraction"), "target_independence")
    if obj["class"] not in TARGET_INDEPENDENCE_CLASSES:
        raise ContractError(f"unknown target_independence.class {obj['class']!r}")
    if obj["class"] == "derived_from_predictors" and obj.get("predicted_omega_used_in_extraction") is False:
        raise ContractError("derived_from_predictors cannot claim predicted_omega_used_in_extraction=false")
    if obj["class"] in {
        "fully_model_independent_time_domain",
        "independent_time_domain_given_frozen_spatial_mode",
    }:
        if obj.get("predicted_omega_used_in_extraction") or obj.get("predicted_omega_used_for_demodulation") or obj.get("predicted_omega_used_for_bandpass") or obj.get("predicted_vg_used_in_extraction"):
            raise ContractError("independent target class cannot use predicted omega for extraction")
        if obj["class"] == "fully_model_independent_time_domain" and obj.get("spatial_mode_basis_source") == "model_conditioned_frozen":
            raise ContractError("a frozen modal spatial basis is not fully model-independent")


def _check_tau_independence(obj: Any) -> None:
    if not isinstance(obj, dict):
        raise ContractError("tau_return_independence must be an object")
    _require(obj, ("class",), "tau_return_independence")
    if obj["class"] not in TAU_INDEPENDENCE_CLASSES:
        raise ContractError(f"unknown tau_return_independence.class {obj['class']!r}")
    if obj["class"] == "raw_trajectory_phase_blind":
        if obj.get("predicted_omega_used") or obj.get("predicted_group_velocity_used") or obj.get("synthetic_wavepacket_used") or obj.get("l_over_vg_used"):
            raise ContractError("raw_trajectory_phase_blind tau cannot use predicted omega/vg/synthetic envelope")
    if obj["class"] == "derived_from_predicted_dispersion":
        if not (
            obj.get("predicted_omega_used")
            or obj.get("predicted_group_velocity_used")
            or obj.get("synthetic_wavepacket_used")
        ):
            raise ContractError("derived_from_predicted_dispersion must record a predicted-dispersion dependency")


def _check_curvature_bridge(record: dict[str, Any]) -> None:
    _require(
        record,
        (
            "operator_semantics",
            "dynamic_stability_claim",
            "physical_energy_hessian_claim",
            "parent_classification",
            "parent_classification_semantics",
            "eigenvalues",
            "cluster_ids",
            "basis_is_unique",
            "reconstruction_rel_error",
            "certifies",
            "does_not_certify",
        ),
        "curvature_bridge",
    )
    if record["operator_semantics"] != "abs_real_jacobian_curvature_proxy":
        raise ContractError("operator_semantics must be abs_real_jacobian_curvature_proxy")
    if record["dynamic_stability_claim"] is not False:
        raise ContractError("dynamic_stability_claim must be false")
    if record["physical_energy_hessian_claim"] is not False:
        raise ContractError("physical_energy_hessian_claim must be false")
    if record["parent_classification_semantics"] != "historical_parent_only":
        raise ContractError("parent_classification_semantics must be historical_parent_only")
    if len(record["eigenvalues"]) != len(record["cluster_ids"]):
        raise ContractError("eigenvalues and cluster_ids length mismatch")


def _check_symmetry_blocks(record: dict[str, Any]) -> None:
    _require(
        record,
        (
            "selection_matrix",
            "blocks",
            "channel_ids",
            "channel_labels",
            "basis_order",
            "measured_response_claim",
        ),
        "symmetry_blocks",
    )
    matrix = record["selection_matrix"]
    if not isinstance(matrix, list) or len(matrix) != 3 or any(len(row) != 3 for row in matrix):
        raise ContractError("selection_matrix must be 3x3")
    for row in matrix:
        for val in row:
            if type(val) is not int or val not in (0, 1):
                raise ContractError("selection_matrix entries must be integers 0 or 1")
    if record["measured_response_claim"] is not False:
        raise ContractError("measured_response_claim must be false")
    if len(record["channel_ids"]) != len(record["channel_labels"]):
        raise ContractError("channel_ids/channel_labels length mismatch")


def _check_dispersion_branch(record: dict[str, Any], *, tol: float = DEFAULT_CONV_TOL) -> None:
    _check_convention(record, tol=tol)
    _require(
        record,
        (
            "k_hat",
            "k_ref",
            "k_closed",
            "L_hat",
            "m",
            "n",
            "theta_B",
            "holonomy_representation",
            "branch_id",
            "branch_overlap",
            "ambiguity_status",
        ),
        "dispersion_branch",
    )
    if record["holonomy_representation"] not in {"embedded_in_k", "explicit_phase"}:
        raise ContractError("invalid holonomy_representation")
    if record["holonomy_representation"] == "embedded_in_k":
        if abs(float(record.get("phi_holonomy_explicit", 0.0))) > tol:
            raise ContractError("embedded_in_k forbids a nonzero explicit holonomy phase")
        expected = (2.0 * math.pi * int(record["n"]) - int(record["m"]) * float(record["theta_B"])) / float(record["L_hat"])
        if abs(float(record["k_closed"]) - expected) > max(tol, 1e-12 * (1.0 + abs(expected))):
            raise ContractError("k_closed must equal (2*pi*n - m*theta_B)/L_hat")
    else:
        if "phi_holonomy_explicit" not in record:
            raise ContractError("explicit_phase requires phi_holonomy_explicit")
    if record["ambiguity_status"] not in {"unique", "DISPERSION_BRANCH_AMBIGUOUS", "unavailable"}:
        raise ContractError("invalid ambiguity_status")


def _check_phase_observation(record: dict[str, Any]) -> None:
    _require(
        record,
        (
            "phi_loop",
            "phi_envelope",
            "phi_carrier_derived",
            "holonomy_representation",
            "return_time_representation",
            "target_independence",
            "tau_return_independence",
        ),
        "phase_observation",
    )
    _check_target_independence(record["target_independence"])
    _check_tau_independence(record["tau_return_independence"])
    hol = record["holonomy_representation"]
    if hol not in {"embedded_in_k", "explicit_phase"}:
        raise ContractError("invalid holonomy_representation")
    if hol == "embedded_in_k":
        if abs(float(record.get("phi_holonomy_explicit", 0.0) or 0.0)) > DEFAULT_CONV_TOL:
            raise ContractError("embedded_in_k forbids a nonzero explicit holonomy phase")
    phi_loop = record["phi_loop"]
    phi_env = record["phi_envelope"]
    phi_car = record["phi_carrier_derived"]
    if None not in (phi_loop, phi_env, phi_car):
        expected = wrap_angle(float(phi_loop) - float(phi_env))
        if abs(wrap_angle(float(phi_car) - expected)) > 1e-12:
            raise ContractError("phi_carrier_derived must equal wrap(phi_loop - phi_envelope)")


def validate_record(record: dict[str, Any], *, schema: dict[str, Any] | None = None) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise ContractError("record must be a JSON object")
    if schema is None:
        schema = load_schema()
    if schema.get("title") != SCHEMA_NAME:
        raise ContractError("unexpected schema title")
    _check_identity(record)
    kind = record["record_type"]
    if kind == "curvature_bridge":
        _check_curvature_bridge(record)
    elif kind == "symmetry_blocks":
        _check_symmetry_blocks(record)
    elif kind == "dispersion_branch":
        _check_dispersion_branch(record)
    elif kind == "phase_observation":
        _check_phase_observation(record)
    else:
        raise ContractError(f"unsupported record_type {kind!r}")
    return {
        "ok": True,
        "record_type": kind,
        "canonical_sha256": canonical_json_hash(record),
    }


def validate_file(path: Path) -> dict[str, Any]:
    record = json.loads(Path(path).read_text(encoding="utf-8"))
    result = validate_record(record)
    result["path"] = str(path)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args(argv)
    for path in args.paths:
        result = validate_file(path)
        print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
