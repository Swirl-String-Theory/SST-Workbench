"""Complete TWO-NORMAL-DOF Jacobian of a finite-N Ruban discretization.

*Not* the full continuum spectrum; not a proof of stability. The operator is
physically interpretable only at a verified exact/near-exact relative equilibrium.
"""
from __future__ import annotations
import numpy as np
from scipy.optimize import linear_sum_assignment
from .high_order import residual,field,validate
from .core import derivative,DELTA


def normal_frame(x):
    x,s=validate(x);t=derivative(x)/s[:,None]
    vertical=np.array([0.,0.,1.])
    e1=vertical-np.sum(t*vertical,axis=1)[:,None]*t
    ss=np.linalg.norm(e1,axis=1)
    if ss.min()<.1:raise ValueError('Vertical frame singular')
    e1=e1/ss[:,None];e2=np.cross(t,e1)
    return e1,e2


def jacobian(x,scheme='trapezoid',step=1e-5,delta=DELTA):
    x=np.array(x,dtype=float,copy=True)
    if not (0<step<1e-2):raise ValueError('Invalid FD perturbation step')
    base=residual(x,scheme,delta)
    u,om,alpha=base['U'],base['Omega'],base['alpha']
    e1,e2=normal_frame(x);n=len(x)
    directions=np.empty((2*n,n,3))
    for k in range(n):
        directions[2*k,k]=e1[k]
        directions[2*k+1,k]=e2[k]
    # explicit zero ensures other vertices are never perturbed
    directions.fill(0)
    for k in range(n):
        directions[2*k,k]=e1[k];directions[2*k+1,k]=e2[k]
    mat=np.empty((2*n,2*n))
    for k,dx in enumerate(directions):
        # Corotating, comoving frame; freeze base-state tangential gauge alpha(theta)
        vf=(field(x+step*dx,scheme,delta)-field(x-step*dx,scheme,delta))/(2*step)
        g=vf-om*np.column_stack((-dx[:,1],dx[:,0],np.zeros(n)))-alpha[:,None]*derivative(dx)
        mat[0::2,k]=np.sum(g*e1,axis=1)
        mat[1::2,k]=np.sum(g*e2,axis=1)
    if not np.isfinite(mat).all():raise RuntimeError('Nonfinite Jacobian')
    return mat,{'U':u,'Omega':om,'base_residual':base['epsilon'],
                'tangential_gauge_max':float(np.max(np.abs(alpha))),
                'dof':2*n,'finite_N_matrix_complete':True,
                'gauge':'fixed normal frame, frozen alpha(theta), U, Omega',
                'linearization_valid_only_at_relative_equilibrium':True}


def evaluate_spectrum(mat):
    eig=np.linalg.eigvals(mat)
    eig=eig[np.lexsort((eig.imag,eig.real))]
    return {'eigenvalues':[[float(z.real),float(z.imag)] for z in eig],
            'n_eigenvalues':len(eig),'max_real':float(np.max(eig.real)),
            'max_imag_abs':float(np.max(np.abs(eig.imag)))}


def compare_matrices(a,b):
    return float(np.linalg.norm(a-b)/max(np.linalg.norm(a),1e-30))


def match_eigenvalues(ref,other,max_count=16):
    """Nearest finite complex eigenvalues: diagnostic, cannot establish modes on its own."""
    ref=np.array(ref,dtype=complex);other=np.array(other,dtype=complex)
    idx=np.argsort(np.abs(ref))[:min(max_count,len(ref),len(other))]
    dist=np.abs(ref[idx,None]-other[None,:])
    rows,cols=linear_sum_assignment(dist)
    return [{'ref':[float(ref[idx[i]].real),float(ref[idx[i]].imag)],
             'other':[float(other[j].real),float(other[j].imag)],
             'absolute_difference':float(dist[i,j])} for i,j in zip(rows,cols)]
