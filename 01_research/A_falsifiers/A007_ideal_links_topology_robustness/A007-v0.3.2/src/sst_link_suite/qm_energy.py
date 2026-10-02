from __future__ import annotations

import numpy as np

from .native_ext import BackendOptions
from .native_ext.core import neumann_coupling_matrices
from .perturbations import ReducedBasis, apply_reduced_coordinates


def _periodic_derivatives(curve: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    n = len(curve)
    dt = 2.0*np.pi/n
    d1 = (np.roll(curve, -1, axis=0)-np.roll(curve, 1, axis=0))/(2.0*dt)
    d2 = (np.roll(curve, -1, axis=0)-2.0*curve+np.roll(curve, 1, axis=0))/(dt*dt)
    return d1, d2, dt


def discrete_length_bending(curves: list[np.ndarray]) -> tuple[float, float]:
    length = 0.0
    bending = 0.0
    for curve in curves:
        d1, d2, dt = _periodic_derivatives(curve)
        speed = np.linalg.norm(d1, axis=1)
        curvature = np.linalg.norm(np.cross(d1, d2), axis=1)/np.maximum(speed**3, 1e-300)
        length += float(np.sum(speed)*dt)
        bending += float(np.sum(curvature**2*speed)*dt)
    return length, bending


def tube_repulsion_energy(
    curves: list[np.ndarray], diameter: float, softness: float = 0.04,
    contact_margin: float = 0.0, local_skip_fraction: float = 0.035,
) -> float:
    """Smooth point-sampled overlap penalty, normalized by tested pair count.

    This is a transparent diagnostic regularizer, not the Ridgerunner strut functional.
    """
    threshold = diameter*(1.0+contact_margin)
    softness_abs = max(softness*diameter, 1e-12)
    total = 0.0
    count = 0
    for i, a in enumerate(curves):
        for j in range(i, len(curves)):
            b = curves[j]
            dist = np.linalg.norm(a[:, None, :]-b[None, :, :], axis=2)
            if i == j:
                n = len(a)
                rows = np.arange(n)[:, None]
                cols = np.arange(n)[None, :]
                cyc = np.minimum((rows-cols) % n, (cols-rows) % n)
                mask = (cyc > max(3, int(local_skip_fraction*n))) & (rows < cols)
            else:
                mask = np.ones_like(dist, dtype=bool)
            z = (threshold-dist[mask])/softness_abs
            values = np.logaddexp(0.0, z)
            total += float(np.sum(values*values))
            count += int(values.size)
    return total/max(count, 1)


def geometric_terms(
    curves: list[np.ndarray], diameter: float,
    repulsion_softness: float, repulsion_margin: float,
) -> np.ndarray:
    length, bending = discrete_length_bending(curves)
    repulsion = tube_repulsion_energy(curves, diameter, repulsion_softness, repulsion_margin)
    return np.asarray([length, bending, repulsion], dtype=float)


def neumann_term(
    curves: list[np.ndarray], signs: np.ndarray, epsilon: float,
    backend_options: BackendOptions, local_skip_energy: int,
) -> tuple[float, str]:
    matrices, backend = neumann_coupling_matrices(
        curves, [float(epsilon)], int(local_skip_energy), backend_options
    )
    coupling = np.asarray(matrices[0], dtype=float)
    signs = np.asarray(signs, dtype=float)
    return float(signs @ coupling @ signs), backend


def _finite_difference_vector(
    dimension: int, step: float, evaluator, compute_offdiagonal: bool = True,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    zero = np.zeros(dimension)
    f0 = np.asarray(evaluator(zero), dtype=float)
    gradient = np.zeros((len(f0), dimension), dtype=float)
    hessian = np.zeros((len(f0), dimension, dimension), dtype=float)
    plus, minus = {}, {}
    for i in range(dimension):
        q = np.zeros(dimension); q[i] = step
        plus[i] = np.asarray(evaluator(q), dtype=float)
        q[i] = -step
        minus[i] = np.asarray(evaluator(q), dtype=float)
        gradient[:, i] = (plus[i]-minus[i])/(2.0*step)
        hessian[:, i, i] = (plus[i]-2.0*f0+minus[i])/(step*step)
    if compute_offdiagonal:
        for i in range(dimension):
            for j in range(i+1, dimension):
                qpp = np.zeros(dimension); qpp[i] = step; qpp[j] = step
                qpm = np.zeros(dimension); qpm[i] = step; qpm[j] = -step
                qmp = np.zeros(dimension); qmp[i] = -step; qmp[j] = step
                qmm = np.zeros(dimension); qmm[i] = -step; qmm[j] = -step
                value = (evaluator(qpp)-evaluator(qpm)-evaluator(qmp)+evaluator(qmm))/(4.0*step*step)
                hessian[:, i, j] = value
                hessian[:, j, i] = value
    return f0, gradient, hessian


def compute_geometric_reduced_derivatives(
    samples, basis: ReducedBasis, diameter: float, step: float,
    repulsion_softness: float = 0.04, repulsion_margin: float = 0.0,
    compute_offdiagonal: bool = True,
) -> dict:
    dimension = basis.vectors.shape[0]
    def evaluator(q):
        return geometric_terms(
            apply_reduced_coordinates(samples, basis, np.asarray(q, dtype=float)),
            diameter, repulsion_softness, repulsion_margin,
        )
    f0, gradient, hessian = _finite_difference_vector(dimension, step, evaluator, compute_offdiagonal)
    return {
        "names": ["length", "bending", "tube_repulsion"],
        "baseline": f0,
        "gradient": gradient,
        "hessian": hessian,
        "step_D": float(step),
        "compute_offdiagonal": bool(compute_offdiagonal),
    }


def compute_neumann_reduced_derivatives(
    samples, basis: ReducedBasis, signs: np.ndarray, epsilon: float,
    backend_options: BackendOptions, step: float, local_skip_energy: int = 2,
    compute_offdiagonal: bool = True,
) -> dict:
    dimension = basis.vectors.shape[0]
    observed_backend = None
    def evaluator(q):
        nonlocal observed_backend
        value, backend = neumann_term(
            apply_reduced_coordinates(samples, basis, np.asarray(q, dtype=float)),
            signs, epsilon, backend_options, local_skip_energy,
        )
        if observed_backend is None:
            observed_backend = backend
        elif backend != observed_backend:
            raise RuntimeError(f"Mixed Neumann backends: {observed_backend} vs {backend}")
        return np.asarray([value], dtype=float)
    f0, gradient, hessian = _finite_difference_vector(dimension, step, evaluator, compute_offdiagonal)
    return {
        "name": "neumann",
        "baseline": float(f0[0]),
        "gradient": gradient[0],
        "hessian": hessian[0],
        "backend": observed_backend,
        "step_D": float(step),
    }


def _matrix_ledger(matrix: np.ndarray) -> dict:
    matrix = 0.5*(np.asarray(matrix, dtype=float)+np.asarray(matrix, dtype=float).T)
    eigenvalues = np.linalg.eigvalsh(matrix)
    return {
        "matrix": matrix,
        "eigenvalues": eigenvalues,
        "negative_mode_count": int(np.sum(eigenvalues < -1e-7)),
        "near_zero_mode_count": int(np.sum(np.abs(eigenvalues) <= 1e-7)),
        "positive_mode_count": int(np.sum(eigenvalues > 1e-7)),
        "minimum_eigenvalue": float(eigenvalues[0]),
        "spectral_gap_positive": float(np.min(eigenvalues[eigenvalues > 1e-7])) if np.any(eigenvalues > 1e-7) else float("nan"),
        "symmetry_error": float(np.max(np.abs(matrix-matrix.T))),
    }


def _profile_cancellation_diagnostics(weight_vector: np.ndarray, term_gradients: np.ndarray) -> dict:
    contributions = weight_vector[:, None] * term_gradients
    vector_sum = np.sum(contributions, axis=0)
    norm_sum = float(np.sum(np.linalg.norm(contributions, axis=1)))
    resultant = float(np.linalg.norm(vector_sum))
    return {
        "gradient_contribution_norm_sum": norm_sum,
        "gradient_resultant_norm": resultant,
        "gradient_cancellation_ratio": float(resultant / max(norm_sum, 1e-300)),
        "term_contribution_norms": np.linalg.norm(contributions, axis=1),
    }


def assemble_reduced_energy(
    geometric: dict,
    neumann: dict,
    profiles: dict[str, dict[str, float]],
    normalization_scales: dict[str, float] | None = None,
    normalization_mode: str = "local_baseline",
    normalization_reference: str | None = None,
) -> dict:
    names = list(geometric["names"]) + ["neumann"]
    baseline = np.concatenate([
        np.asarray(geometric["baseline"]), [float(neumann["baseline"])]
    ]).astype(float)
    gradient_raw = np.concatenate([
        np.asarray(geometric["gradient"]), np.asarray(neumann["gradient"])[None, :]
    ], axis=0)
    hessian_raw = np.concatenate([
        np.asarray(geometric["hessian"]), np.asarray(neumann["hessian"])[None, :, :]
    ], axis=0)

    if normalization_scales is None:
        scales = np.maximum(np.abs(baseline), 1e-10)
        effective_mode = "local_baseline"
    else:
        missing = [name for name in names if name not in normalization_scales]
        if missing:
            raise KeyError(f"Missing normalization scales for {missing}")
        scales = np.asarray([max(abs(float(normalization_scales[name])), 1e-10) for name in names])
        effective_mode = normalization_mode
    gradient = gradient_raw / scales[:, None]
    hessian = hessian_raw / scales[:, None, None]

    result = {
        "backend": neumann["backend"],
        "dimension": int(gradient.shape[1]),
        "step_D": geometric["step_D"],
        "hessian_scheme": "full-central" if geometric.get("compute_offdiagonal", True) else "diagonal-central",
        "normalization_mode": effective_mode,
        "normalization_reference": normalization_reference,
        "baseline_raw": {name: float(value) for name, value in zip(names, baseline)},
        "normalization_scales": {name: float(value) for name, value in zip(names, scales)},
        "term_gradient_raw": {name: gradient_raw[i] for i, name in enumerate(names)},
        "term_hessian_raw": {name: hessian_raw[i] for i, name in enumerate(names)},
        "names": names + list(profiles),
        "gradients": {},
        "hessians": {},
        "profile_diagnostics": {},
    }
    for i, name in enumerate(names):
        result["gradients"][name] = {
            "vector": gradient[i],
            "raw_vector": gradient_raw[i],
            "norm": float(np.linalg.norm(gradient[i])),
            "raw_norm": float(np.linalg.norm(gradient_raw[i])),
            "max_abs": float(np.max(np.abs(gradient[i]))),
        }
        result["hessians"][name] = _matrix_ledger(hessian[i])
        result["hessians"][name]["raw_matrix"] = hessian_raw[i]
    for profile, weights in profiles.items():
        weight_vector = np.asarray([float(weights.get(name, 0.0)) for name in names])
        profile_gradient = weight_vector @ gradient
        profile_hessian = np.tensordot(weight_vector, hessian, axes=(0, 0))
        result["gradients"][profile] = {
            "vector": profile_gradient,
            "norm": float(np.linalg.norm(profile_gradient)),
            "max_abs": float(np.max(np.abs(profile_gradient))),
        }
        result["hessians"][profile] = _matrix_ledger(profile_hessian)
        result["profile_diagnostics"][profile] = _profile_cancellation_diagnostics(
            weight_vector, gradient
        )
    return result


def finite_difference_reduced_energy(
    samples, basis: ReducedBasis, signs: np.ndarray, diameter: float, epsilon: float,
    backend_options: BackendOptions, step: float, profiles: dict[str, dict[str, float]],
    local_skip_energy: int = 2, repulsion_softness: float = 0.04,
    repulsion_margin: float = 0.0, geometric_derivatives: dict | None = None,
    compute_offdiagonal: bool = True,
    normalization_scales: dict[str, float] | None = None,
    normalization_mode: str = "local_baseline",
    normalization_reference: str | None = None,
) -> tuple[dict, dict]:
    geometric = geometric_derivatives or compute_geometric_reduced_derivatives(
        samples, basis, diameter, step, repulsion_softness, repulsion_margin, compute_offdiagonal
    )
    neumann = compute_neumann_reduced_derivatives(
        samples, basis, signs, epsilon, backend_options, step, local_skip_energy, compute_offdiagonal
    )
    return assemble_reduced_energy(
        geometric, neumann, profiles,
        normalization_scales=normalization_scales,
        normalization_mode=normalization_mode,
        normalization_reference=normalization_reference,
    ), geometric
