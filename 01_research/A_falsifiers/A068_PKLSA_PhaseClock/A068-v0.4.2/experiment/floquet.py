"""A068 v0.4: a posteriori full-state Euler tangent/relative monodromy.

Never use an observed scalar-clock frequency as an operator parameter.
No Floquet eigenfrequency unless a reproducible full-field RPO is independently
qualified; truncated Ritz approximations are diagnostic only.
"""
from __future__ import annotations
import numpy as np
from .rpo import rotate_field,shift_field


def tangent_fd_test(G,U,delta,eps=1e-6):
    """Check exact linearized Euler RHS against centered finite difference."""
    empty=np.empty((0,*U.shape))
    _,D=G.rhs(U,np.asarray([delta]))
    fp,_=G.rhs(U+eps*delta,empty)
    fm,_=G.rhs(U-eps*delta,empty)
    error=np.linalg.norm((fp-fm)/(2*eps)-D[0])/max(np.linalg.norm(D[0]),1e-30)
    return float(error)


def symmetry_inverse(field,rotation,shift_cells):
    """If U(T)=Shift_s(R U(0)), return R^-1 Shift_-s U(T)."""
    f=shift_field(field,-np.asarray(shift_cells,float))
    return rotate_field(f,np.asarray(rotation,int).T)


def monodromy_action(G,U0,dt,steps,v0,rotation,shift_cells):
    """True matrix-free derivative of frozen RK4 Euler map along same evolving U."""
    D=np.asarray([G.project(v0)])
    U=U0.copy()
    for _ in range(steps):
        U,D=G.rk4(U,D,dt)
    return symmetry_inverse(D[0],rotation,shift_cells)


def ritz_floquet(G,U0,dt,steps,rotation,shift_cells,dimension=5,seed=6840):
    """Fixed random subspace Ritz screen; not a converged full-spectrum solver.

    Each Arnoldi/QR subspace vector is divergence free. Reports full-space
    eigenpair residuals (NOT merely the small-matrix residuals). No scalar
    phase/frequency estimate is consumed by this function.
    """
    rng=np.random.default_rng(seed);Q=[]
    for _ in range(dimension):
        v=G.project(rng.normal(size=U0.shape))
        for q in Q: v-=np.mean(q*v)*q
        v=G.project(v)
        norm=np.sqrt(np.mean(v*v))
        if norm<1e-12:raise ValueError('Dependent frozen tangent trial basis')
        Q.append(v/norm)
    image=[]
    for q in Q:
        image.append(monodromy_action(G,U0,dt,steps,q,rotation,shift_cells))
    matrix=np.asarray([[np.mean(q*z) for z in image] for q in Q])
    values,coef=np.linalg.eig(matrix)
    triples=[]
    for i,lam in enumerate(values):
        v=sum(coef[j,i]*Q[j] for j in range(dimension))
        w=sum(coef[j,i]*image[j] for j in range(dimension))
        residue=float(np.sqrt(np.mean(abs(w-lam*v)**2))/max(np.sqrt(np.mean(abs(w)**2)),1e-30))
        T=dt*steps
        triples.append({'multiplier_re':float(lam.real),'multiplier_im':float(lam.imag),
                        'ritz_full_state_residual':residue,
                        'growth_exponent':float(np.log(max(abs(lam),1e-30))/T),
                        'angular_frequency_abs':float(abs(np.angle(lam))/T)})
    triples.sort(key=lambda x:x['ritz_full_state_residual'])
    return {'schema':'SST-EULER-MONODROMY-RITZ-1','mechanism':'A064 exact Euler tangent linearization RK4 + inverse measured full-field relative symmetry',
            'predicted_by_scalar_phase':False,'basis_seed':seed,'subspace_dimension':dimension,
            'grid':G.n,'steps':steps,'dt':dt,'period':dt*steps,
            'eigenpairs':triples,'predictive_authority':'RITZ_DIAGNOSTIC_ONLY_UNLESS_RPO_AND_EIGEN_RESIDUALS_QUALIFIED',
            'no_physical_floquet_claim':True}


def manufactured_floquet_test(omega=1.75,T=1.2):
    """Manufactured constant-coefficient two-mode monodromy, analytic independent oracle."""
    from scipy.linalg import expm
    A=np.array([[-0.2,-omega],[omega,-0.2]])
    M=expm(A*T)
    w=np.linalg.eigvals(M)
    expected=np.exp((-0.2+1j*omega)*T)
    return {'expected_omega':omega,'measured_omega':float(abs(np.angle(w[np.argmax(w.imag)]))/T),
            'multiplier_error':float(min(abs(w[0]-expected),abs(w[1]-expected))),
            'oracle_pass':bool(min(abs(w[0]-expected),abs(w[1]-expected))<1e-12)}
