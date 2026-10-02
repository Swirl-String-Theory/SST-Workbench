from __future__ import annotations
import numpy as np
import math
from scipy.optimize import linprog, nnls


def gram_spectral(A, rel_tol=1e-9):
    """Fast spectrum via G=A^T A; returns serializable diagnostics plus positive row-space basis."""
    m,n=A.shape
    if n==0 or m==0:
        return dict(rank=0,singular_values=[],sigma_max=0.0,sigma_min_positive=0.0,condition_positive=float("inf"),right_nullity=n,left_nullity=m,tol=0.0),np.zeros((n,0)),np.zeros((n,n)),np.eye(n)
    G=(A.T@A).toarray() if hasattr(A.T@A,"toarray") else np.asarray(A.T@A,float)
    G=0.5*(G+G.T)
    evals,V=np.linalg.eigh(G)
    evals=np.maximum(evals,0.0)[::-1]
    V=V[:,::-1]
    s=np.sqrt(evals)
    smax=float(s[0]) if len(s) else 0.0
    lam_max=float(evals[0]) if len(evals) else 0.0
    # A^T A squares the condition number. Rank is therefore thresholded in
    # eigenvalue space with an explicit roundoff floor, rather than by taking
    # sqrt(eigenvalue) and applying the requested singular tolerance directly.
    lam_tol=max((float(rel_tol)*smax)**2,np.finfo(float).eps*max(m,n)*lam_max)
    tol=math.sqrt(lam_tol) if lam_tol>0 else 0.0
    mask=evals>lam_tol; rank=int(np.count_nonzero(mask)); spos=s[mask]
    smin=float(spos[-1]) if len(spos) else 0.0
    diag=dict(rank=rank,singular_values=[float(x) for x in s],sigma_max=smax,sigma_min_positive=smin,
              condition_positive=float(smax/smin) if smin>0 else float("inf"),right_nullity=int(n-rank),left_nullity=int(m-rank),tol=float(tol),method="eigh(A^T A)",gram_eigenvalue_tol=float(lam_tol))
    return diag,V[:,:rank],G,V[:,rank:]


def svd_diagnostics(A, rel_tol=1e-9):
    return gram_spectral(A,rel_tol)[0]


def nnls_equilibrium(A,b):
    b=np.asarray(b,float)
    if A.shape[1]==0:
        lam=np.zeros(0); r=-b; success=False; status="NO_CONSTRAINTS"
    else:
        X=A.toarray() if hasattr(A,"toarray") else np.asarray(A,float)
        lam,resnorm=nnls(X,b,maxiter=max(1000,20*X.shape[1]))
        r=X@lam-b; success=True; status="scipy.optimize.nnls"
    bn=max(float(np.linalg.norm(b)),np.finfo(float).tiny)
    return lam,np.asarray(r,float),float(np.linalg.norm(r)/bn),{"success":success,"status":status}


def positive_self_stress(A, rel_tol=1e-9, samples=16, seed=2401864, row_basis=None, null_basis=None):
    """Search ker(A) ∩ simplex in nullspace coordinates.

    If Z spans ker(A), lambda=Z y.  Feasibility then uses only k=dim ker(A)
    optimization variables, with n positivity inequalities, instead of rank(A)
    equality constraints in n lambda variables.
    """
    m,n=A.shape
    if n==0:
        return dict(feasible=False,residual=float("inf"),affine_dim_lower_bound=0,support=0,witnesses=[])
    if null_basis is None:
        _,row_basis,_,null_basis=gram_spectral(A,rel_tol)
    Z=np.asarray(null_basis,float); k=Z.shape[1]
    if k==0:
        return dict(feasible=False,residual=float("inf"),affine_dim_lower_bound=0,support=0,witnesses=[])
    # Z y >= 0; sum(Z y)=1.
    Aub=-Z; bub=np.zeros(n)
    aeq=(np.ones(n)@Z).reshape(1,-1); beq=np.array([1.0])
    base=linprog(np.zeros(k),A_ub=Aub,b_ub=bub,A_eq=aeq,b_eq=beq,bounds=[(None,None)]*k,method="highs")
    if not base.success:
        return dict(feasible=False,residual=float("inf"),affine_dim_lower_bound=0,support=0,witnesses=[])
    sols=[Z@base.x]; rng=np.random.default_rng(seed)
    for _ in range(int(samples)):
        c_lambda=rng.normal(size=n); c_y=Z.T@c_lambda
        for sign in (1,-1):
            res=linprog(sign*c_y,A_ub=Aub,b_ub=bub,A_eq=aeq,b_eq=beq,bounds=[(None,None)]*k,method="highs")
            if res.success: sols.append(Z@res.x)
    S=np.vstack(sols); S[np.abs(S)<1e-14]=0.0
    residuals=np.linalg.norm((A@S.T).T,axis=1); best=int(np.argmin(residuals)); x=S[best]
    aff=int(np.linalg.matrix_rank(S[1:]-S[0],tol=max(1e-10,rel_tol))) if len(S)>1 else 0
    return dict(feasible=True,residual=float(residuals[best]),affine_dim_lower_bound=aff,support=int(np.count_nonzero(x>1e-10)),
                witnesses=[[float(v) for v in row] for row in S[:min(len(S),6)]])


def duplicate_column_count(A, cosine_tol=1e-8, gram=None):
    n=A.shape[1]
    if n<2: return 0
    G=gram if gram is not None else (A.T@A).toarray()
    norms=np.sqrt(np.maximum(np.diag(G),0.0)); count=0
    for i in range(n):
        if norms[i]==0: continue
        c=G[i,i+1:]/(norms[i]*np.where(norms[i+1:]>0,norms[i+1:],np.inf))
        count+=int(np.count_nonzero(c>1.0-cosine_tol))
    return count
