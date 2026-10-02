from __future__ import annotations

import json
import math
from copy import deepcopy

import pytest

from validate_modal_phase_contract import (
    CANONICAL_CONVENTION,
    RAW_CONVENTION,
    SCHEMA_NAME,
    ContractError,
    canonical_json_hash,
    convention_bridge,
    load_schema,
    validate_record,
    wrap_angle,
)


def _identity(**extra):
    rec = {
        "schema": SCHEMA_NAME,
        "schema_version": "1.0",
        "record_type": "curvature_bridge",
        "source_id": "A034-v0.2.2",
        "parent_hashes": {"gate_input_sha256": "a" * 64},
        "code_hash": "b" * 64,
        "blind_status": "not_applicable",
    }
    rec.update(extra)
    return rec


def _curvature(**extra):
    rec = _identity(
        record_type="curvature_bridge",
        operator_semantics="abs_real_jacobian_curvature_proxy",
        dynamic_stability_claim=False,
        physical_energy_hessian_claim=False,
        parent_classification="ENERGETICALLY_ADMISSIBLE",
        parent_classification_semantics="historical_parent_only",
        eigenvalues=[0.011249458, 0.25364441, 0.25364441],
        cluster_ids=[0, 1, 1],
        cluster_means=[0.011249458, 0.25364441],
        basis_is_unique=False,
        reconstruction_rel_error=1e-16,
        certifies={"subspace_reconstruction": True},
        does_not_certify={"dynamic_stability": True, "physical_energy_hessian": True},
    )
    rec.update(extra)
    return rec


def _blocks(**extra):
    rec = _identity(
        record_type="symmetry_blocks",
        source_id="A037-v0.3.2",
        selection_matrix=[[1, 0, 0], [0, 1, 1], [0, 1, 1]],
        blocks=[[0], [1, 2]],
        channel_ids=[0, 1, 2],
        channel_labels=["body_x", "body_y", "body_z"],
        basis_order="body_xyz",
        measured_response_claim=False,
    )
    rec.update(extra)
    return rec


def _dispersion(**extra):
    L_hat = 2.0 * math.pi
    n = 1
    m = 0
    theta_B = 0.3
    k_ref = 2.0 * math.pi * n / L_hat
    k_closed = (2.0 * math.pi * n - m * theta_B) / L_hat
    conv = convention_bridge(0.01, -2.5)
    rec = _identity(
        record_type="dispersion_branch",
        source_id="A029-v0.3.0",
        **conv,
        k_hat=k_closed,
        k_ref=k_ref,
        k_closed=k_closed,
        L_hat=L_hat,
        m=m,
        n=n,
        theta_B=theta_B,
        holonomy_representation="embedded_in_k",
        phi_holonomy_explicit=0.0,
        branch_id="n1_m0",
        branch_overlap=0.99,
        ambiguity_status="unique",
    )
    rec.update(extra)
    return rec


def _phase(**extra):
    phi_loop = 1.2
    phi_env = 0.4
    rec = _identity(
        record_type="phase_observation",
        source_id="A029-v0.3.0",
        phi_loop=phi_loop,
        phi_envelope=phi_env,
        phi_carrier_derived=wrap_angle(phi_loop - phi_env),
        holonomy_representation="embedded_in_k",
        phi_holonomy_explicit=0.0,
        return_time_representation="synthetic_wavepacket_accounting",
        target_independence={
            "class": "derived_from_predictors",
            "predicted_omega_used_in_extraction": True,
        },
        tau_return_independence={
            "class": "derived_from_predicted_dispersion",
            "predicted_omega_used": True,
            "synthetic_wavepacket_used": True,
        },
    )
    rec.update(extra)
    return rec


def test_load_schema_title():
    schema = load_schema()
    assert schema["title"] == SCHEMA_NAME
    assert "curvature_bridge" in schema["$defs"]


def test_canonical_json_hash_is_order_invariant():
    a = {"b": 1, "a": 2}
    b = {"a": 2, "b": 1}
    assert canonical_json_hash(a) == canonical_json_hash(b)
    assert canonical_json_hash(a) == "d3626ac30a87e6f7a6428233b3c68299976865fa5508e4267c5415c76af7a772"


def test_wrap_angle_principal_interval():
    assert wrap_angle(0.0) == pytest.approx(0.0)
    assert wrap_angle(math.pi + 0.1) == pytest.approx(-math.pi + 0.1)
    assert wrap_angle(-math.pi - 0.2) == pytest.approx(math.pi - 0.2)


def test_convention_bridge_maps_raw_to_canonical():
    out = convention_bridge(0.2, -1.5)
    assert out["sigma"] == pytest.approx(0.2)
    assert out["omega"] == pytest.approx(1.5)
    assert out["eigenvalue_raw"]["convention"] == RAW_CONVENTION
    assert out["canonical_complex"]["convention"] == CANONICAL_CONVENTION
    assert out["canonical_complex"]["imag"] == pytest.approx(1.5)


def test_convention_bridge_rejects_inconsistent_omega():
    with pytest.raises(ContractError, match="disagrees"):
        convention_bridge(0.2, -1.5, omega=1.4)


def test_validate_curvature_bridge_ok():
    result = validate_record(_curvature())
    assert result["ok"] is True
    assert result["record_type"] == "curvature_bridge"
    assert len(result["canonical_sha256"]) == 64


def test_validate_curvature_bridge_rejects_stability_claim():
    rec = _curvature(dynamic_stability_claim=True)
    with pytest.raises(ContractError, match="dynamic_stability_claim"):
        validate_record(rec)


def test_validate_symmetry_blocks_ok():
    assert validate_record(_blocks())["ok"] is True


def test_validate_symmetry_blocks_rejects_bool_matrix_and_measured_claim():
    rec = _blocks(selection_matrix=[[True, False, False], [False, True, True], [False, True, True]])
    with pytest.raises(ContractError, match="0 or 1"):
        validate_record(rec)
    rec2 = _blocks(measured_response_claim=True)
    with pytest.raises(ContractError, match="measured_response_claim"):
        validate_record(rec2)


def test_validate_dispersion_branch_ok():
    assert validate_record(_dispersion())["ok"] is True


def test_validate_dispersion_rejects_double_counted_holonomy():
    rec = _dispersion(phi_holonomy_explicit=0.3)
    with pytest.raises(ContractError, match="explicit holonomy"):
        validate_record(rec)


def test_validate_dispersion_rejects_wrong_k_closed():
    rec = _dispersion(k_closed=0.0)
    with pytest.raises(ContractError, match="k_closed"):
        validate_record(rec)


def test_validate_phase_observation_ok():
    assert validate_record(_phase())["ok"] is True


def test_validate_phase_rejects_inconsistent_carrier():
    rec = _phase(phi_carrier_derived=0.0)
    with pytest.raises(ContractError, match="phi_carrier_derived"):
        validate_record(rec)


def test_validate_phase_rejects_independent_class_with_omega_extraction():
    rec = _phase()
    rec["target_independence"] = {
        "class": "independent_time_domain_given_frozen_spatial_mode",
        "predicted_omega_used_in_extraction": True,
        "temporal_frequency_source": "derived_from_predictors",
        "return_phase_source": "derived_from_predictors",
        "spatial_mode_basis_source": "model_conditioned_frozen",
        "predicted_vg_used_in_extraction": False,
    }
    with pytest.raises(ContractError, match="cannot use predicted omega"):
        validate_record(rec)


def test_validate_phase_rejects_frozen_basis_as_fully_independent():
    rec = _phase()
    rec["target_independence"] = {
        "class": "fully_model_independent_time_domain",
        "predicted_omega_used_in_extraction": False,
        "predicted_vg_used_in_extraction": False,
        "spatial_mode_basis_source": "model_conditioned_frozen",
        "temporal_frequency_source": "independent_time_domain",
        "return_phase_source": "measured_from_raw_trajectory",
    }
    with pytest.raises(ContractError, match="not fully model-independent"):
        validate_record(rec)


def test_validate_record_requires_identity():
    rec = _curvature()
    del rec["code_hash"]
    with pytest.raises(ContractError, match="code_hash"):
        validate_record(rec)


def test_validate_deep_copy_does_not_mutate():
    rec = _blocks()
    snapshot = deepcopy(rec)
    validate_record(rec)
    assert rec == snapshot


def test_json_is_hash_source_and_parquet_is_optional_table():
    rec = _dispersion()
    h1 = canonical_json_hash(rec)
    h2 = canonical_json_hash(json.loads(json.dumps(rec, sort_keys=False)))
    assert h1 == h2
    pa = pytest.importorskip("pyarrow")
    import pyarrow.parquet as pq

    table = pa.Table.from_pylist([{"k_hat": rec["k_hat"], "omega": rec["omega"]}])
    assert table.num_rows == 1
    assert "lambda" not in rec

