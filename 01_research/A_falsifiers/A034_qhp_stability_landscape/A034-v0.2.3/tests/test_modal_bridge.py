from __future__ import annotations

import json

import numpy as np
import pytest

from sst_qhp_falsifier.modal_bridge import (
    build_bridge,
    check_bridge,
    cluster_eigenvalues,
    cluster_projectors,
    matrix_sha256,
    reconstruction_rel_error,
    tangent_curvature_proxy,
    constraint_projector,
)


def _overnight_parent():
    return np.diag([0.011249458, 0.25364441, 0.25364441]), np.array([[1.0, 0.0, 0.0]])


def test_exact_degenerate_pair_is_one_cluster():
    H, C = _overnight_parent()
    built = build_bridge(H, C, g=[0.0, 0.0, 0.0])
    rec = built["record"]
    assert rec["operator_semantics"] == "abs_real_jacobian_curvature_proxy"
    assert rec["dynamic_stability_claim"] is False
    assert rec["physical_energy_hessian_claim"] is False
    assert rec["parent_classification_semantics"] == "historical_parent_only"
    assert rec["basis_is_unique"] is False
    assert rec["reconstruction_rel_error"] <= rec["reconstruction_tolerance"]
    wrapper = check_bridge(rec, built["arrays"])
    assert wrapper["passed"]


def test_near_degenerate_clusters_together():
    evals = np.array([0.0, 0.25364441, 0.25364441 + 1e-10])
    clusters = cluster_eigenvalues(evals, tol=1e-8)
    assert any(len(c) == 2 for c in clusters)


def test_rotation_inside_cluster_leaves_projector_and_hash_invariant():
    rng = np.random.default_rng(0)
    evals = np.array([0.0, 0.25, 0.25])
    evecs = np.eye(3)
    clusters = cluster_eigenvalues(evals, 1e-8)
    p0 = cluster_projectors(evecs, clusters)[1]
    q, _ = np.linalg.qr(rng.normal(size=(2, 2)))
    mixed = evecs.copy()
    mixed[:, [1, 2]] = mixed[:, [1, 2]] @ q
    p1 = cluster_projectors(mixed, clusters)[1]
    assert np.allclose(p0, p1, atol=1e-12)
    assert matrix_sha256(p0) == matrix_sha256(p1)


def test_never_uses_mean_lambda_as_restricted_operator():
    H, C = _overnight_parent()
    P = constraint_projector(C)
    built = build_bridge(H, C)
    assert "K_tan" not in built["arrays"]
    assert "hessian" not in json.dumps({k: None for k in built["arrays"]}).lower()
    for key, arr in built["arrays"].items():
        if key.startswith("C_") and key[2:].isdigit():
            mean = float(np.mean(built["record"]["cluster_means"]))
            assert not np.allclose(arr, mean * P)


def test_restricted_operators_are_C_j():
    H, C_constraint = _overnight_parent()
    built = build_bridge(H, C_constraint)
    C_proxy = built["arrays"]["C"]
    assert built["record"]["restricted_operator_symbol"] == "C_j = P_j C P_j"
    assert built["record"]["curvature_proxy_symbol"] == "C = P H_parent P"
    for i, pj in enumerate(built["projectors"]):
        assert np.allclose(built["arrays"][f"C_{i}"], pj @ C_proxy @ pj, atol=1e-12)


def test_reconstruction_identity():
    H = np.diag([1.0, 2.0, 4.0])
    C = np.array([[1.0, 0.0, 0.0]])
    built = build_bridge(H, C)
    err = reconstruction_rel_error(built["arrays"]["C"], built["projectors"])
    assert err <= 1e-12
