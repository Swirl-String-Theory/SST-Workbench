from __future__ import annotations

import numpy as np


def _real_basis(x, k):
    x = np.asarray(x, float)
    x = x - np.mean(x, axis=0, keepdims=True)
    _, s, vh = np.linalg.svd(x, full_matrices=False)
    kk = max(1, min(int(k), vh.shape[0]))
    return s, vh[:kk]


def raw_pod_metrics(phi, top_k=3, discovery_fraction=0.65):
    """Historical v0.3.x linear-POD diagnostic on raw phase.

    The early/late subspace overlap is retained for longitudinal comparison only in
    A056-v0.4.0.  It is deliberately *not* a blocking G2 criterion because raw phase
    is a circular variable and the metric is not covariant under phase wrapping/drift.
    """
    x = np.asarray(phi, float)
    x0 = x - np.mean(x, axis=0, keepdims=True)
    _, s, vh = np.linalg.svd(x0, full_matrices=False)
    e = s * s
    frac = e / max(float(np.sum(e)), 1e-30)
    energetic = int(np.sum(frac > 1e-6))
    k = max(1, min(int(top_k), vh.shape[0], energetic if energetic > 0 else 1))
    orth = float(np.linalg.norm(vh[:k] @ vh[:k].T - np.eye(k), ord="fro"))
    cut = max(3, min(len(x) - 3, int(round(float(discovery_fraction) * len(x)))))
    _, v1 = _real_basis(x[:cut], k)
    _, v2 = _real_basis(x[cut:], k)
    kk = min(v1.shape[0], v2.shape[0])
    sv = np.linalg.svd(v1[:kk] @ v2[:kk].T, compute_uv=False)
    overlap = float(np.mean(sv)) if len(sv) else 0.0
    q = x0 @ vh[:k].T
    return {
        "top_energy_fraction": float(np.sum(frac[:k])),
        "orthogonality_residual": orth,
        "discovery_confirmation_subspace_overlap": overlap,
        "rank": int(np.sum(s > max(float(s[0]) * 1e-12, 1e-15))) if len(s) else 0,
        "k": k,
        "discovery_cut": cut,
    }, q, vh[:k]


# Backwards-compatible name for tooling that wants the historical diagnostic.
pod_metrics = raw_pod_metrics


def _complex_spatial_center(phi):
    """Circular embedding with per-time spatial mean removal.

    For z=exp(i phi), z -> exp(i psi(t)) z under a global time-dependent phase
    shift.  Subtracting the spatial mean per time preserves that row-wise unitary
    factor, so the right-singular spatial subspace is phase-shift covariant.
    """
    z = np.exp(1j * np.asarray(phi, float))
    return z - np.mean(z, axis=1, keepdims=True)


def _complex_basis(phi, k):
    zc = _complex_spatial_center(phi)
    _, s, vh = np.linalg.svd(zc, full_matrices=False)
    kk = max(1, min(int(k), vh.shape[0]))
    return s, vh[:kk]


def _normalized_nonzero_fourier_power(phi_block):
    z = np.exp(1j * np.asarray(phi_block, float))
    # Unit-normalized discrete transform.  Absolute normalization cancels after
    # conversion to a probability distribution but keeps Parseval diagnostics clear.
    f = np.fft.fft(z, axis=1) / np.sqrt(z.shape[1])
    p = np.mean(np.abs(f) ** 2, axis=0).astype(float)
    total_all = float(np.sum(p))
    p_nonzero = p.copy()
    if len(p_nonzero):
        p_nonzero[0] = 0.0
    nz = float(np.sum(p_nonzero))
    if nz <= 1e-30:
        return np.zeros_like(p_nonzero), 0.0, total_all
    return p_nonzero / nz, nz / max(total_all, 1e-30), total_all


def circular_fourier_metrics(phi, top_k=3, discovery_fraction=0.65):
    """A056-v0.4.0 representation-covariant spectral qualification metrics.

    Blocking quantities are designed to be insensitive to:
      * 2*pi phase wrapping (because z=exp(i phi));
      * arbitrary global phase psi(t) (row-wise unitary factor);
      * cyclic spatial translations in the Fourier-power comparison.

    The circular-POD early/late overlap is still reported diagnostically.  It is not
    blocking because a travelling coherent mode may rotate its spatial basis while
    preserving the same Kelvin/Fourier sector distribution.
    """
    x = np.asarray(phi, float)
    if x.ndim != 2 or x.shape[0] < 6 or x.shape[1] < 8:
        raise ValueError("phi must be a 2-D (time, space) array with at least 6x8 samples")

    zc = _complex_spatial_center(x)
    _, s, vh = np.linalg.svd(zc, full_matrices=False)
    e = np.abs(s) ** 2
    frac = e / max(float(np.sum(e)), 1e-30)
    energetic = int(np.sum(frac > 1e-6))
    k = max(1, min(int(top_k), vh.shape[0], energetic if energetic > 0 else 1))
    orth = float(np.linalg.norm(vh[:k] @ vh[:k].conj().T - np.eye(k), ord="fro"))
    q = zc @ vh[:k].conj().T

    cut = max(3, min(len(x) - 3, int(round(float(discovery_fraction) * len(x)))))
    _, v1 = _complex_basis(x[:cut], k)
    _, v2 = _complex_basis(x[cut:], k)
    kk = min(v1.shape[0], v2.shape[0])
    sv = np.linalg.svd(v1[:kk] @ v2[:kk].conj().T, compute_uv=False)
    circ_overlap = float(np.mean(sv)) if len(sv) else 0.0

    p_early, nz_early, _ = _normalized_nonzero_fourier_power(x[:cut])
    p_late, nz_late, _ = _normalized_nonzero_fourier_power(x[cut:])
    p_all, nz_all, _ = _normalized_nonzero_fourier_power(x)
    if float(np.sum(p_early)) <= 0.0 or float(np.sum(p_late)) <= 0.0:
        fourier_overlap = 0.0
    else:
        # Bhattacharyya coefficient between normalized non-zero-mode power spectra.
        fourier_overlap = float(np.sum(np.sqrt(p_early * p_late)))
        # Guard tiny floating overshoots outside the mathematical [0,1] range.
        fourier_overlap = float(np.clip(fourier_overlap, 0.0, 1.0))

    top_idx = np.argsort(p_all)[::-1][: max(1, min(int(top_k), len(p_all)))]
    fourier_top = float(np.sum(p_all[top_idx])) if len(p_all) else 0.0
    ns = int(x.shape[1])
    signed_modes = [int(i if i <= ns // 2 else i - ns) for i in top_idx]

    return {
        "circular_top_energy_fraction": float(np.sum(frac[:k])),
        "circular_orthogonality_residual": orth,
        "circular_discovery_confirmation_subspace_overlap_diagnostic": circ_overlap,
        "circular_rank": int(np.sum(s > max(float(s[0]) * 1e-12, 1e-15))) if len(s) else 0,
        "k": k,
        "discovery_cut": cut,
        "fourier_power_overlap": fourier_overlap,
        "fourier_top_energy_fraction": fourier_top,
        "fourier_nonzero_power_fraction_all": float(nz_all),
        "fourier_nonzero_power_fraction_discovery": float(nz_early),
        "fourier_nonzero_power_fraction_confirmation": float(nz_late),
        "dominant_signed_modes": signed_modes,
    }, q, vh[:k]


def spectral_qualification(phi, cfg, discovery_fraction=0.65):
    """Return v0.4.0 blocking decision plus legacy and invariant diagnostics."""
    top_k = int(cfg.get("top_k", 3))
    legacy, q_legacy, basis_legacy = raw_pod_metrics(phi, top_k, discovery_fraction)
    inv, _, _ = circular_fourier_metrics(phi, top_k, discovery_fraction)

    passes = {
        "circular_energy_pass": bool(
            inv["circular_top_energy_fraction"]
            >= float(cfg["circular_top_energy_fraction_min"])
        ),
        "circular_orthogonality_pass": bool(
            inv["circular_orthogonality_residual"]
            <= float(cfg["circular_orthogonality_max"])
        ),
        "fourier_power_overlap_pass": bool(
            inv["fourier_power_overlap"] >= float(cfg["fourier_power_overlap_min"])
        ),
    }
    passed = bool(all(passes.values()))
    return {
        "method": "circular_fourier_v1",
        "pass": passed,
        "blocking": {**inv, **passes},
        "legacy_raw_phase_pod_diagnostic": legacy,
    }, q_legacy, basis_legacy


def derived_ringdown(t, q):
    q = np.asarray(q)
    if q.ndim == 2:
        e = np.sqrt(np.sum(np.abs(q) ** 2, axis=1))
    else:
        e = np.abs(q)
    if len(e) >= 7:
        ker = np.ones(5) / 5
        e = np.convolve(np.pad(e, (2, 2), mode="edge"), ker, mode="valid")
    return np.asarray(t, float), np.asarray(e, float)
