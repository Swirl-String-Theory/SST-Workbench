from __future__ import annotations
import numpy as np
from scipy.spatial import cKDTree

def _kabsch(P: np.ndarray, Q: np.ndarray, proper: bool = True) -> np.ndarray:
    H = P.T @ Q
    U, _, Vt = np.linalg.svd(H)
    R = Vt.T @ U.T
    if proper and np.linalg.det(R) < 0:
        Vt[-1] *= -1
        R = Vt.T @ U.T
    return R

def mirror_icp_score(curves: list[np.ndarray], iterations: int = 15) -> dict:
    P = np.concatenate(curves, axis=0).astype(float)
    P -= P.mean(axis=0)
    scale = np.sqrt(np.mean(np.sum(P*P, axis=1)))
    P /= max(scale, 1e-30)
    Q = P.copy()
    Q[:, 0] *= -1.0
    R = np.eye(3)
    tree = cKDTree(P)
    previous = np.inf
    for _ in range(iterations):
        moved = Q @ R.T
        dist, idx = tree.query(moved)
        Rstep = _kabsch(Q, P[idx], proper=True)
        R = Rstep
        score = float(np.sqrt(np.mean(dist**2)))
        if abs(previous-score) < 1e-10:
            break
        previous = score
    moved = Q @ R.T
    dist1, _ = cKDTree(P).query(moved)
    dist2, _ = cKDTree(moved).query(P)
    chamfer = float(np.sqrt(0.5*(np.mean(dist1**2)+np.mean(dist2**2))))
    return {
        "mirror_icp_chamfer_normalized": chamfer,
        "mirror_fit_rotation_det": float(np.linalg.det(R)),
        "interpretation": "Geometric embedding proxy only; not a proof of topological amphichirality.",
    }

def inertia_symmetry(curves: list[np.ndarray]) -> dict:
    P = np.concatenate(curves, axis=0)
    P = P - P.mean(axis=0)
    C = P.T @ P / len(P)
    vals = np.linalg.eigvalsh(C)
    return {
        "pointcloud_covariance_eigenvalues": vals,
        "degeneracy_01": float(abs(vals[1]-vals[0])/max(vals[2], 1e-30)),
        "degeneracy_12": float(abs(vals[2]-vals[1])/max(vals[2], 1e-30)),
    }
