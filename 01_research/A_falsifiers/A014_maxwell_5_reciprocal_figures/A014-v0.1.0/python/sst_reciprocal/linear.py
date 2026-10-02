from __future__ import annotations
import numpy as np
from scipy.optimize import nnls, linprog


def svd_diagnostics(A, rel_tol=1e-9):
    X = A.toarray() if hasattr(A, "toarray") else np.asarray(A, dtype=float)
    m,n = X.shape
    if n == 0 or m == 0:
        return dict(rank=0, singular_values=[], sigma_max=0.0, sigma_min_positive=0.0,
                    condition_positive=float("inf"), right_nullity=n, left_nullity=m, tol=0.0)
    s = np.linalg.svd(X, compute_uv=False, full_matrices=False)
    smax = float(s[0]) if len(s) else 0.0
    tol = max(float(rel_tol)*smax, np.finfo(float).eps*max(m,n)*smax)
    rank = int(np.count_nonzero(s > tol))
    spos = s[s > tol]
    smin = float(spos[-1]) if len(spos) else 0.0
    cond = float(smax/smin) if smin > 0 else float("inf")
    return dict(rank=rank, singular_values=[float(x) for x in s], sigma_max=smax,
                sigma_min_positive=smin, condition_positive=cond,
                right_nullity=int(n-rank), left_nullity=int(m-rank), tol=float(tol))


def nnls_equilibrium(A, b):
    X=A.toarray() if hasattr(A,"toarray") else np.asarray(A,float)
    if X.shape[1] == 0:
        lam=np.zeros(0); r=-np.asarray(b,float)
    else:
        lam,_ = nnls(X, np.asarray(b,float), maxiter=max(1000, 10*X.shape[1]))
        r=X@lam-b
    bn=max(np.linalg.norm(b), np.finfo(float).tiny)
    return lam, r, float(np.linalg.norm(r)/bn)


def positive_self_stress(A, rel_tol=1e-9, samples=16, seed=2401864):
    """Search ker(A) ∩ simplex. Returns a lower bound on cone/face dimension.

    Equalities are compressed to the numerical row space before LP, so the test
    uses the same preregistered singular tolerance as the rank audit.
    """
    X=A.toarray() if hasattr(A,"toarray") else np.asarray(A,float)
    m,n=X.shape
    if n == 0:
        return dict(feasible=False, residual=float("inf"), affine_dim_lower_bound=0, support=0, witnesses=[])
    U,s,Vt=np.linalg.svd(X, full_matrices=False)
    smax=float(s[0]) if len(s) else 0.0
    tol=max(rel_tol*smax, np.finfo(float).eps*max(m,n)*smax)
    r=int(np.count_nonzero(s>tol))
    Ar=(U[:,:r].T@X) if r else np.zeros((0,n))
    Aeq=np.vstack([Ar, np.ones((1,n))])
    beq=np.r_[np.zeros(r),1.0]
    bounds=[(0,None)]*n
    base=linprog(np.zeros(n), A_eq=Aeq, b_eq=beq, bounds=bounds, method="highs")
    if not base.success:
        return dict(feasible=False, residual=float("inf"), affine_dim_lower_bound=0, support=0, witnesses=[])
    sols=[base.x]
    rng=np.random.default_rng(seed)
    for _ in range(samples):
        c=rng.normal(size=n)
        for sign in (1,-1):
            res=linprog(sign*c, A_eq=Aeq, b_eq=beq, bounds=bounds, method="highs")
            if res.success: sols.append(res.x)
    S=np.vstack(sols)
    residuals=np.linalg.norm((X@S.T).T,axis=1)
    best=int(np.argmin(residuals))
    x=S[best]
    if len(S)>1:
        D=S[1:]-S[0]
        aff=int(np.linalg.matrix_rank(D, tol=max(1e-10, rel_tol)))
    else: aff=0
    return dict(feasible=True, residual=float(residuals[best]), affine_dim_lower_bound=aff,
                support=int(np.count_nonzero(x>1e-10)), witnesses=[[float(v) for v in row] for row in S[:min(len(S),6)]])


def duplicate_column_count(A, cosine_tol=1e-8):
    X=A.toarray() if hasattr(A,"toarray") else np.asarray(A,float)
    n=X.shape[1]
    if n<2: return 0
    norms=np.linalg.norm(X,axis=0)
    count=0
    for i in range(n):
        if norms[i]==0: continue
        for j in range(i+1,n):
            if norms[j]==0: continue
            cos=float(np.dot(X[:,i],X[:,j])/(norms[i]*norms[j]))
            if cos>1.0-cosine_tol: count+=1
    return count
