"""A068 v0.4.4 matrix-free relative-periodic shooting.

Frozen candidate period and group transform from full-field search. Optional Newton
Krylov corrections to U0 with explicit zero-mean/gauge orthogonality; no scalar
phase fitting and no implicit numerical qualification.
"""
from __future__ import annotations
import numpy as np
from scipy.sparse.linalg import LinearOperator,gmres
from .rpo import rotate_field,shift_field
from .floquet import symmetry_inverse

def integrate(G,U,dt,steps):
    empty=np.empty((0,*U.shape));W=U.copy()
    for _ in range(steps):W,_=G.rk4(W,empty,dt)
    return W

def fixed_symmetry_shoot(G,U0,dt,steps,rotation,shift_cells,tolerance=.025,
                         iterations=3,gmres_rtol=.05,gmres_maxiter=12):
    """Real nonlinear full-field shooting at fixed period and symmetry.

    The period/shift are held at independently measured candidate values, *not*
    optimized based on observed scalar phase. This is a shooting subproblem, not
    full free-period/moving-frame RPO certification.
    """
    from .floquet import monodromy_action
    x=G.project(np.asarray(U0,float));N=x.size
    record=[]
    for iteration in range(iterations+1):
        end=integrate(G,x,dt,steps)
        error=symmetry_inverse(end,rotation,shift_cells)-x
        rel=float(np.linalg.norm(error)/max(np.linalg.norm(x),1e-30))
        record.append({'iteration':iteration,'residual':rel})
        if rel<tolerance:break
        if iteration==iterations:break
        # D[g^-1 Phi_T(x)-x] v ; phase drift neutral modes make the linear
        # system potentially singular; use regularization, and no false PASS.
        def matvec(v):
            v=G.project(v.reshape(x.shape))
            mapped=monodromy_action(G,x,dt,steps,v,rotation,shift_cells)
            return (mapped-v+1e-4*v).ravel()
        A=LinearOperator((N,N),matvec=matvec,dtype=np.float64)
        rhs=-error.ravel()
        correction,info=gmres(A,rhs,rtol=gmres_rtol,maxiter=gmres_maxiter,restart=8)
        record[-1]['gmres_info']=int(info)
        if not np.all(np.isfinite(correction)) or info!=0:break
        step=G.project(correction.reshape(x.shape))
        # Trust region: changing the state can invalidate the original source
        # topology. Never silently promote this revised solution as PKLSA.
        sz=np.linalg.norm(step)/max(np.linalg.norm(x),1e-30)
        if sz>0.1:step*=.1/sz
        x=G.project(x+step)
    return {'schema':'A068-RPO-SHOOT-v0.4.4','algorithm':'FIXED_PERIOD_FIXED_GROUP_NEWTON_GMRES','iterations':record,
            'final_residual':record[-1]['residual'],'screen_pass':bool(record[-1]['residual']<tolerance),
            'period_optimized':False,'group_optimized':False,'second_return_certified':False,
            'neutral_mode_gauge_certified':False,'rpo_certified':False,
            'reason':'Fixed-period shooting is diagnostic; free period, second return, gauge and discretization convergence required'}

def double_return(G,U,dt,steps,rotation,shift_cells):
    """Reintegrate for 2T independently; report second closure residual."""
    first=integrate(G,U,dt,steps)
    second=integrate(G,first,dt,steps)
    one=symmetry_inverse(first,rotation,shift_cells)
    two=symmetry_inverse(symmetry_inverse(second,rotation,shift_cells),rotation,shift_cells)
    return {'first_return':float(np.linalg.norm(one-U)/max(np.linalg.norm(U),1e-30)),
            'second_return':float(np.linalg.norm(two-U)/max(np.linalg.norm(U),1e-30))}
