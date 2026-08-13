from __future__ import annotations

import numpy as np

from .perturbations import ReducedBasis


def candidate_filament_symplectic_matrix(samples, basis: ReducedBasis, signs: np.ndarray) -> np.ndarray:
    r"""Compute the reduced Rasetti--Regge-type filament two-form proxy.

    .. math::
       \Omega_{ab}=\sum_i\sigma_i\oint \hat t_i\cdot
       (\delta X_a\times\delta X_b)\,ds.

    This is a Research-Track candidate kinematic form.  It becomes a physical SST symplectic
    structure only after derivation from the accepted action and circulation normalization.
    """
    signs = np.asarray(signs, dtype=float)
    dimension = basis.vectors.shape[0]
    omega = np.zeros((dimension, dimension), dtype=float)
    for component_index, (sample, component_slice) in enumerate(zip(samples, basis.component_slices)):
        tangent = sample.d1 / np.maximum(np.linalg.norm(sample.d1, axis=1)[:, None], 1e-300)
        dt = 2.0*np.pi/len(sample.r)
        ds = np.linalg.norm(sample.d1, axis=1)*dt
        fields = basis.vectors[:, component_slice, :]
        for a in range(dimension):
            cross = np.cross(fields[a][None, :, :], fields)  # (d,n,3)
            value = np.sum(ds[None, :] * np.einsum("ij,kij->ki", tangent, cross), axis=1)
            omega[a, :] += signs[component_index]*value
    omega = 0.5*(omega-omega.T)
    return omega


def symplectic_diagnostics(omega: np.ndarray, rank_tolerance: float = 1e-9) -> dict:
    omega = np.asarray(omega, dtype=float)
    singular = np.linalg.svd(omega, compute_uv=False)
    scale = max(float(singular[0]) if singular.size else 0.0, 1.0)
    threshold = rank_tolerance*scale
    rank = int(np.sum(singular > threshold))
    dimension = omega.shape[0]
    return {
        "matrix": omega,
        "dimension": dimension,
        "rank": rank,
        "nullity": int(dimension-rank),
        "full_rank": bool(rank == dimension),
        "rank_is_even": bool(rank % 2 == 0),
        "singular_values": singular,
        "rank_threshold": float(threshold),
        "antisymmetry_error": float(np.max(np.abs(omega+omega.T))),
        "pfaffian_abs_proxy": float(np.sqrt(abs(np.linalg.det(omega)))) if dimension else 1.0,
        "status": (
            "[RESEARCH TRACK] Candidate filament two-form; not canonized as the SST phase-space form."
        ),
    }


def linearized_hamiltonian_spectrum(
    omega: np.ndarray,
    hessian: np.ndarray,
    rank_tolerance: float = 1e-9,
    stability_tolerance: float = 1e-7,
    hessian_scheme: str = "full-central",
) -> dict:
    omega = np.asarray(omega, dtype=float)
    hessian = np.asarray(hessian, dtype=float)
    diagnostics = symplectic_diagnostics(omega, rank_tolerance)
    # Moore--Penrose form gives a diagnostic even when unresolved null directions remain.
    generator = np.linalg.pinv(omega, rcond=rank_tolerance) @ hessian
    eigenvalues = np.linalg.eigvals(generator)
    order = np.argsort(np.abs(eigenvalues.imag) + np.abs(eigenvalues.real))
    eigenvalues = eigenvalues[order]
    real = eigenvalues.real
    imag = eigenvalues.imag
    unstable = np.abs(real) > stability_tolerance
    oscillatory = (~unstable) & (np.abs(imag) > stability_tolerance)
    zero = (~unstable) & (~oscillatory)
    positive_frequencies = sorted(float(abs(x)) for x in imag[(~unstable) & (imag > stability_tolerance)])
    pair_errors = []
    remaining = list(eigenvalues)
    while remaining:
        value = remaining.pop(0)
        if not remaining:
            pair_errors.append(float(abs(value)))
            break
        target = -value
        distances = [abs(other-target) for other in remaining]
        index = int(np.argmin(distances))
        pair_errors.append(float(distances[index]))
        remaining.pop(index)
    return {
        "generator": generator,
        "eigenvalues_real": real,
        "eigenvalues_imag": imag,
        "unstable_mode_count": int(np.sum(unstable)),
        "oscillatory_eigenvalue_count": int(np.sum(oscillatory)),
        "near_zero_eigenvalue_count": int(np.sum(zero)),
        "positive_frequencies_dimensionless": positive_frequencies,
        "lowest_positive_frequency": positive_frequencies[0] if positive_frequencies else float("nan"),
        "frequency_ratios_to_lowest": (
            [float(value/positive_frequencies[0]) for value in positive_frequencies]
            if positive_frequencies else []
        ),
        "hamiltonian_pairing_max_error": max(pair_errors, default=0.0),
        "spectrally_stable_screen": bool(not np.any(unstable)),
        "spectrally_stable": bool(not np.any(unstable) and hessian_scheme == "full-central"),
        "stability_claim_eligible": bool(hessian_scheme == "full-central"),
        "hessian_scheme": hessian_scheme,
        "used_pseudoinverse": bool(not diagnostics["full_rank"]),
        "interpretation": (
            "Dimensionless linearized spectrum of the selected effective closure. A diagonal-central "
            "Hessian is screening-only and cannot establish stability. Absolute quantum energies require "
            "an independently derived action scale and hbar normalization."
        ),
    }


def symplectic_kernel_quotient(
    omega: np.ndarray,
    metadata: tuple[dict, ...] | list[dict] | None = None,
    rank_tolerance: float = 1e-9,
) -> dict:
    """Diagnose the kernel and construct an algebraic image-space quotient candidate.

    The image-space projection is mathematically useful, but it is *not* automatically a
    physical gauge quotient.  A kernel direction can also be a Casimir or a missing degree
    of freedom.  v0.3.3 therefore reports the quotient as a diagnostic candidate only.
    """
    omega = np.asarray(omega, dtype=float)
    u, singular, _ = np.linalg.svd(omega, full_matrices=True)
    scale = max(float(singular[0]) if singular.size else 0.0, 1.0)
    threshold = float(rank_tolerance) * scale
    rank = int(np.sum(singular > threshold))
    image_basis = u[:, :rank]
    null_basis = u[:, rank:]
    quotient_omega = image_basis.T @ omega @ image_basis

    null_modes = []
    for k in range(null_basis.shape[1]):
        vector = null_basis[:, k]
        order = np.argsort(np.abs(vector))[::-1][: min(8, len(vector))]
        support = []
        for idx in order:
            row = {
                "coordinate_index": int(idx),
                "coefficient": float(vector[idx]),
                "abs_coefficient": float(abs(vector[idx])),
            }
            if metadata is not None and int(idx) < len(metadata):
                row["basis_metadata"] = dict(metadata[int(idx)])
            support.append(row)
        null_modes.append({
            "null_mode_index": int(k),
            "top_coordinate_support": support,
            "l2_norm": float(np.linalg.norm(vector)),
        })

    qdiag = symplectic_diagnostics(quotient_omega, rank_tolerance)
    return {
        "original_dimension": int(omega.shape[0]),
        "rank": rank,
        "nullity": int(omega.shape[0] - rank),
        "rank_threshold": float(threshold),
        "singular_values": singular,
        "null_modes": null_modes,
        "image_basis": image_basis,
        "quotient_omega": quotient_omega,
        "quotient_dimension": int(rank),
        "quotient_full_rank": bool(qdiag["full_rank"]),
        "quotient_condition_number": (
            float(qdiag["singular_values"][0] / qdiag["singular_values"][-1])
            if rank and qdiag["singular_values"][-1] > 0 else float("inf")
        ),
        "physical_quotient_established": False,
        "status": (
            "[RESEARCH TRACK] Algebraic image-space quotient of the candidate two-form. "
            "Kernel directions are not declared gauge without an action-level derivation."
        ),
    }


def quotient_linearized_spectrum(
    omega: np.ndarray,
    hessian: np.ndarray,
    rank_tolerance: float = 1e-9,
    stability_tolerance: float = 1e-7,
) -> dict:
    """Linearized spectrum on the algebraic image of Omega, for diagnostics only."""
    omega = np.asarray(omega, dtype=float)
    hessian = np.asarray(hessian, dtype=float)
    u, singular, _ = np.linalg.svd(omega, full_matrices=True)
    scale = max(float(singular[0]) if singular.size else 0.0, 1.0)
    rank = int(np.sum(singular > rank_tolerance * scale))
    q = u[:, :rank]
    if rank == 0:
        return {
            "quotient_dimension": 0,
            "spectrally_stable": False,
            "error": "candidate symplectic form has zero rank",
            "physical_quotient_established": False,
        }
    omega_q = q.T @ omega @ q
    hessian_q = q.T @ hessian @ q
    base = linearized_hamiltonian_spectrum(
        omega_q, hessian_q, rank_tolerance=rank_tolerance,
        stability_tolerance=stability_tolerance, hessian_scheme="full-central",
    )
    base.update({
        "quotient_dimension": int(rank),
        "projected_hessian_negative_modes": int(np.sum(np.linalg.eigvalsh(0.5*(hessian_q+hessian_q.T)) < -1e-7)),
        "physical_quotient_established": False,
        "status": "[RESEARCH TRACK] Spectrum on algebraic image(Omega); not a proven physical reduced phase space.",
    })
    return base
