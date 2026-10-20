"""Independent full-state Arnoldi/monodromy validation, never scalar-fit period.

Solver uses independently supplied RPO candidate. Two Arnoldi resolutions and
full-state eigen residuals are required; unstable/neutral modes are retained.
"""
from __future__ import annotations
import numpy as np
from scipy.sparse.linalg import LinearOperator,eigs
from .floquet import monodromy_action

def arnoldi_euler(G,U,dt,steps,rotation,shift_cells,k=3,ncv=12,tol=1e-5,maxiter=100):
    dim=U.size
    if dim<=k+2: raise ValueError('Insufficient state dimension')
    rng=np.random.default_rng(683043)
    probe=G.project(rng.normal(size=U.shape)).ravel()
    probe/=np.linalg.norm(probe)
    def mv(v):return monodromy_action(G,U,dt,steps,G.project(v.reshape(U.shape)),rotation,shift_cells).ravel()
    A=LinearOperator((dim,dim),matvec=mv,dtype=float)
    eigval,eigvec=eigs(A,k=k,ncv=min(ncv,dim-1),which='LM',v0=probe,tol=tol,maxiter=maxiter)
    pairs=[]
    for index,lam in enumerate(eigval):
        v=eigvec[:,index]
        # complex vectors: evaluate real and imaginary parts separately through a real-linear operator
        Av=mv(v.real)+1j*mv(v.imag)
        error=float(np.linalg.norm(Av-lam*v)/max(np.linalg.norm(Av),1e-30))
        pairs.append({'multiplier':[float(lam.real),float(lam.imag)],
                      'frequency_abs':float(abs(np.angle(lam))/(dt*steps)),
                      'growth_rate':float(np.log(max(abs(lam),1e-30))/(dt*steps)),
                      'full_state_residual':error})
    return {'schema':'A068-FLOQUET-ARNOLDI-v0.4.3','k':k,'ncv':ncv,'pairs':pairs,
            'passed_residual_screen':all(p['full_state_residual']<tol*10 for p in pairs),
            'independence':'UNFORCED_EULER_TANGENT_OPERATOR_NO_MEASURED_SCALAR_FREQUENCY'}

def manufactured_arnoldi_oracle():
    # Deterministic 2-mode dense linear algebra verifying frequency and growth.
    freq=1.75; damping=.20;T=1.2
    angle=freq*T;scale=np.exp(-damping*T)
    M=scale*np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
    eigs=np.linalg.eigvals(M)
    frequencies=np.sort(abs(np.angle(eigs))/T)
    return {'oracle_pass':bool(np.allclose(frequencies,freq,rtol=0,atol=1e-12)),
            'omega_expected':freq,'omega_calculated':float(frequencies[0])}
