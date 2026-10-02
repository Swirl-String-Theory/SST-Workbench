"""Darboux / intertwining diagnostics for C006 v0.3.0.

A Darboux claim requires scalar second-order operators (or an equivalent
factorisation) and is intentionally *not* inferred from a generic 4x4 Kelvin
projection.  The finite-dimensional routines below are only eligibility and
implementation diagnostics.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import linear_sum_assignment


def _spectrum_distance(a: np.ndarray, b: np.ndarray) -> dict:
    a = np.asarray(a, dtype=complex).reshape(-1)
    b = np.asarray(b, dtype=complex).reshape(-1)
    if a.size == 0 or b.size == 0:
        return {"rms": float("inf"), "max": float("inf"), "pairs": []}
    C = np.empty((a.size, b.size), dtype=float)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            C[i, j] = abs(x-y) / max(abs(x), abs(y), 1e-12)
    rr, cc = linear_sum_assignment(C)
    ds = [float(C[i,j]) for i,j in zip(rr,cc)]
    return {"rms": float(np.sqrt(np.mean(np.square(ds)))) if ds else float("inf"),
            "max": float(max(ds)) if ds else float("inf"),
            "pairs": [{"a_index": int(i), "b_index": int(j), "relative_distance": float(C[i,j])}
                      for i,j in zip(rr,cc)]}


def best_intertwiner(A: np.ndarray, B: np.ndarray) -> dict:
    """Find normalized X minimizing ||B X - X A||_F by SVD."""
    A = np.asarray(A, dtype=complex); B = np.asarray(B, dtype=complex)
    if A.ndim != 2 or B.ndim != 2 or A.shape[0] != A.shape[1] or B.shape[0] != B.shape[1]:
        raise ValueError("A and B must be square")
    if A.shape != B.shape:
        raise ValueError("A and B must have equal size")
    n = A.shape[0]
    K = np.kron(np.eye(n), B) - np.kron(A.T, np.eye(n))
    _u, s, vh = np.linalg.svd(K)
    x = vh[-1].conj().reshape((n,n), order="F")
    xn = np.linalg.norm(x)
    if xn > 0: x /= xn
    resid = np.linalg.norm(B@x - x@A) / max((np.linalg.norm(A)+np.linalg.norm(B))*np.linalg.norm(x), 1e-30)
    return {"relative_residual": float(resid), "smallest_kronecker_singular_value": float(s[-1]),
            "X": x}


def sector_intertwining_diagnostic(G: np.ndarray, *, coupling_max: float = 0.05,
                                   spectrum_rel_max: float = 0.10,
                                   intertwiner_rel_max: float = 0.05) -> dict:
    """Common/differential-sector pretest in the C006 helical basis.

    Basis order is [h+ common, h+ differential, h- common, h- differential].
    A small off-block coupling is required before separate-sector spectra have a
    useful interpretation.  Passing this pretest is *not* a Darboux proof.
    """
    G = np.asarray(G, dtype=complex)
    if G.shape != (4,4):
        raise ValueError("C006 projected generator must be 4x4")
    ic = [0,2]; idf = [1,3]
    A = G[np.ix_(ic,ic)]
    B = G[np.ix_(idf,idf)]
    CD = G[np.ix_(ic,idf)]
    DC = G[np.ix_(idf,ic)]
    coupling = float(np.sqrt(np.linalg.norm(CD)**2 + np.linalg.norm(DC)**2) / max(np.linalg.norm(G),1e-30))
    ea = np.linalg.eigvals(A); eb = np.linalg.eigvals(B)
    sd = _spectrum_distance(ea, eb)
    it = best_intertwiner(A, B)
    eligible = bool(coupling <= coupling_max)
    pretest = bool(eligible and sd["max"] <= spectrum_rel_max and it["relative_residual"] <= intertwiner_rel_max)
    return {
        "classification": "FINITE_DIMENSIONAL_INTERTWINING_PRETEST_ONLY",
        "off_block_coupling_ratio": coupling,
        "coupling_max": float(coupling_max),
        "common_spectrum": [{"re":float(z.real),"im":float(z.imag)} for z in ea],
        "differential_spectrum": [{"re":float(z.real),"im":float(z.imag)} for z in eb],
        "spectrum_distance": sd,
        "intertwiner_relative_residual": it["relative_residual"],
        "eligible_for_decoupled_sector_comparison": eligible,
        "pretest_pass": pretest,
        "strict_darboux_status": "SKIP_NO_SCALAR_SECOND_ORDER_OPERATOR_PAIR",
    }


def synthetic_darboux_selftest(n: int = 48) -> dict:
    """Finite-dimensional AA^dagger / A^dagger A isospectrality self-test.

    This validates the implementation path only; it contains no SST inference.
    """
    if n < 8: raise ValueError("n must be >= 8")
    L = 2.0*np.pi; h=L/n
    D=np.zeros((n,n),dtype=float)
    for i in range(n):
        D[i,(i+1)%n] = 1.0/(2.0*h)
        D[i,(i-1)%n] = -1.0/(2.0*h)
    x=np.arange(n)*h
    W=np.diag(0.7 + 0.2*np.cos(x) + 0.05*np.sin(2*x))
    A=D+W; Ad=-D+W
    Hp=A@Ad; Hm=Ad@A
    ep=np.linalg.eigvals(Hp); em=np.linalg.eigvals(Hm)
    sd=_spectrum_distance(ep,em)
    adjoint_defect=float(np.linalg.norm(Ad-A.T)/max(np.linalg.norm(A),1e-30))
    return {
        "classification":"NUMERICAL_DARBOUX_FACTORIZATION_SELFTEST",
        "n":int(n), "adjoint_defect":adjoint_defect,
        "isospectral_relative_rms":sd["rms"], "isospectral_relative_max":sd["max"],
        "pass": bool(adjoint_defect < 1e-12 and sd["max"] < 1e-10),
    }
