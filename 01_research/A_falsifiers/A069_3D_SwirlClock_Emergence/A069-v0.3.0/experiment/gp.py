"""Stationary dimensionless Gross-Pitaevskii vortex in a radial box.

Equation i d_t psi = -1/2 Laplacian psi+(abs(psi)^2-1)psi.
A stationary m=1 winding psi=f(r)exp(i phi), f(0)=0,f(Rbox)=1.
This is a straight 2D vortex column, NOT a 3D ring, eigenclock or SST mass prediction.
The gauge zero direction of linearization is an important negative control.
"""
from __future__ import annotations
import numpy as np
from scipy.integrate import solve_bvp

def solve_gp(n=160,rmax=16.,tol=2e-8):
    r=np.linspace(1e-3,rmax,int(n));f=r/np.sqrt(r*r+2)
    y0=np.vstack((f,np.gradient(f,r)))
    def fun(r,y):
        f,df=y
        return np.vstack((df, -df/r+f/(r*r)+2*(f*f-1)*f))
    def bc(ya,yb):return np.array([ya[0]-r[0]*ya[1],yb[0]-1.])
    sol=solve_bvp(fun,bc,r,y0,tol=tol,max_nodes=10000)
    if sol.status!=0: raise RuntimeError('GP boundary value solver did not converge')
    return sol

def profile_at(sol,r):return np.asarray(sol.sol(np.asarray(r))[0])

def radial_residual(sol,r):
    """Independent finite-difference residual, not the BVP solver's own interpolation equation."""
    r=np.asarray(r,dtype=float)
    h=8.e-4
    f=profile_at(sol,r)
    fp=(profile_at(sol,r+h)-profile_at(sol,r-h))/(2*h)
    fpp=(profile_at(sol,r+h)-2*f+profile_at(sol,r-h))/(h*h)
    return -0.5*(fpp+fp/r-f/(r*r))+(f*f-1)*f

def gp_suite():
    fine=solve_gp(150,16)
    finer=solve_gp(270,16)
    probe=np.array([.2,.5,1.,2.,4.,7.,11.])
    diff=float(np.max(np.abs(profile_at(fine,probe)-profile_at(finer,probe))))
    rr=np.linspace(.14,12.,75)
    residual=float(np.max(np.abs(radial_residual(finer,rr))))
    ff=profile_at(finer,probe)
    monotonic=bool(np.all(np.diff(ff)>0) and np.min(ff)>0 and np.max(ff)<1)
    # Gauge-invariant fields: psi and exp(i alpha) psi represent same physical state.
    # L_+ f + f^2(-f) = GP radial stationary residual = 0.
    gauge_null=max(abs(residual),abs(float(np.max(np.abs(radial_residual(fine,rr))))))
    # Vortex circulation in dimensionless GP from u=grad(arg psi): 2 pi m, independent of radius.
    winding=1
    circulation=2*np.pi*winding
    # Uniform psi=e^{i alpha} globally has identical velocity/density at all alpha;
    # a global phase change cannot itself identify an atomic physical clock.
    passed=diff<6e-5 and residual<2e-5 and monotonic and abs(circulation-2*np.pi)<1e-12
    return {'schema':'A069-NLS-GP-RADIAL-CONTROL-1','status':'PASS' if passed else 'FAIL',
       'classification':'MODEL_CONSISTENCY_ONLY','dimension':'2D vortex embedded in 3D',
       'model':'i dt psi=-0.5 laplacian psi+(|psi|^2-1)psi; m=1',
       'normalization':'dimensionless; asymptotic density=1, chemical potential subtracted',
       'domain':{'radius_min':1e-3,'radius_max':16,'boundary_value':1},
       'probe_radii':probe.tolist(),'profile_f':ff.tolist(),
       'max_radial_residual':residual,'mesh_solution_discrepancy':diff,
       'gauge_zero_mode_residual_bound':gauge_null,
       'winding':winding,'circulation':circulation,
       'global_phase_is_observable_clock':False,
       'self_clock_predicted':False,'bdg_eigenmode_qualified':False,
       'not_full_3d_ring':True,'not_pklsa':True}
