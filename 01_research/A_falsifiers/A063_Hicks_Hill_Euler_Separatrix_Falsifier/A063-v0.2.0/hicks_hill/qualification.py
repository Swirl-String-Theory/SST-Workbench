"""Additive v0.1.1 qualifications for Hicks/Hill exact-field controls.

The returned rational-winding curve is a numerical *candidate* on an invariant
axisymmetric streamline torus, not a rigorous certified knot isotope, finite-
core vortex tube, or Euler stability result.
"""
from __future__ import annotations
import math
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq


def interior_refinement(field, points, steps=(4e-4,2e-4,1e-4,5e-5)):
    samples=[]
    for h in steps:
        v=[field.numerical_residual(s*field.a,z*field.a,h=h*field.a) for s,z in points]
        samples.append({'h_over_a':h,
                        'max_abs_divergence':max(abs(x['divergence']) for x in v),
                        'max_euler_residual':max(x['euler_norm'] for x in v),
                        'max_beltrami_residual':max(x['beltrami_norm'] for x in v)})
    return samples


def boundary_ladder(field,n_theta=121,offsets=(1e-3,1e-4,1e-5)):
    if n_theta<5:raise ValueError('n_theta too small')
    th=np.linspace(0.06,math.pi-0.06,n_theta)
    sin,cos=np.sin(th),np.cos(th)
    samples=[]
    for e in offsets:
        sr=field.a*(1-e)*sin;zr=field.a*(1-e)*cos
        sl=field.a*(1+e)*sin;zl=field.a*(1+e)*cos
        ur=np.stack(field.velocity(sr,zr),axis=-1)
        ul=np.stack(field.velocity(sl,zl),axis=-1)
        pr=field.pressure(sr,zr);pl=field.pressure(sl,zl)
        us,uphi,uz=field.velocity(field.a*sin,field.a*cos)
        un=us*sin+uz*cos
        samples.append({'radial_offset_fraction':e,'n_theta':n_theta,
            'max_velocity_jump':float(np.max(np.linalg.norm(ur-ul,axis=-1))),
            'max_pressure_jump':float(np.max(np.abs(pr-pl))),
            'max_boundary_normal_velocity':float(np.max(np.abs(un))),
            'max_boundary_swirl_abs':float(np.max(np.abs(uphi)))})
    vel=[x['max_velocity_jump'] for x in samples]
    prs=[x['max_pressure_jump'] for x in samples]
    return {'samples':samples,'velocity_converges':all(vel[i+1]<vel[i]/5 for i in range(len(vel)-1)),
        'pressure_converges':all(prs[i+1] < max(prs[i]/5,1e-12) for i in range(len(prs)-1)),
        'endpoint_theta_excluded_rad':0.06}


def poloidal_cycle(field,s0,rtol=5e-11,atol=5e-11):
    """Return the azimuthal advance of an unknotted meridional section loop.

    Cross the z=0 Poincare section in the same direction as the initial flow,
    excluding the t=0 event. Results are in the co-moving steady frame.
    """
    u0=field.velocity(s0,0)[2]
    direction=1 if u0>0 else -1
    if not direction:raise ValueError('zero section velocity')
    def rhs(t,x):
        s,z,phi=x
        if s<=1e-9*field.a:raise RuntimeError('axis encounter')
        us,uphi,uz=field.velocity(s,z)
        return [us,uz,uphi/s]
    def crossing(t,x):return x[1] if t>1e-7 else direction*1e-5*field.a
    crossing.direction=direction;crossing.terminal=True
    sol=solve_ivp(rhs,(0,40*field.a/max(abs(u0),1e-8)),[s0,0,0],events=crossing,
                  rtol=rtol,atol=atol,max_step=0.01*field.a/max(abs(u0),1))
    if sol.status!=1:raise RuntimeError('section return missing')
    ret=sol.y[:,-1]
    return {'start_s_over_a':s0/field.a,'T':float(sol.t[-1]),'advance_phi':float(ret[2]),
            'W':float(ret[2]/(2*math.pi)),
            'return_error':float(np.hypot(ret[0]-s0,ret[1])/field.a),
            'streamfunction_relative_drift':float(abs(field.psi(ret[0],ret[1])-field.psi(s0,0))/max(abs(field.psi(s0,0)),1e-12))}


def rational_torus_knot_candidate(field,target_p=3,target_q=4,lo=.96,hi=.98):
    """Find coprime toroidal/poloidal winding p/q by a Poincare return map.

    This supports a T(p,q) *candidate*, not a knot-polynomial certification.
    """
    from math import gcd
    if gcd(target_p,target_q)!=1:raise ValueError('target winding must be primitive')
    goal=target_p/target_q
    cache={}
    def w(s):
        if s not in cache:cache[s]=poloidal_cycle(field,s*field.a)
        return cache[s]['W']
    left,right=w(lo),w(hi)
    if (left-goal)*(right-goal)>=0:raise ValueError('target not bracketed by sampled winding')
    sr=brentq(lambda s:w(s)-goal,lo,hi,xtol=2e-11)
    one=poloidal_cycle(field,sr*field.a,rtol=1e-11,atol=1e-11)
    period=one['T'];s0=sr*field.a
    # Integrate one continuous curve for q complete poloidal sections, not simply
    # concatenated copies, to check orbit closure in 3D independently of root.
    def rhs(t,x):
        s,z,phi=x
        us,uphi,uz=field.velocity(s,z)
        return [us,uz,uphi/s]
    t_end=target_q*period
    sol=solve_ivp(rhs,(0,t_end),[s0,0,0],rtol=2e-11,atol=2e-11,
                  max_step=min(period/180,0.012),dense_output=True)
    if not sol.success:raise RuntimeError(sol.message)
    end=sol.y[:,-1];xyz=np.array([end[0]*math.cos(end[2]),end[0]*math.sin(end[2]),end[1]])
    xyz0=np.array([s0,0,0.]);closure=np.linalg.norm(xyz-xyz0)/field.a
    points=sol.sol(np.linspace(0,t_end,1201));s,z,phi=points
    # Centre of the recirculation cell on the z=0 meridional section.
    cell=brentq(lambda x:field.velocity(x*field.a,0)[2],.55,.67)
    phase=np.unwrap(np.arctan2(z,s-cell*field.a))
    meridional_winding=float((phase[-1]-phase[0])/(2*math.pi))
    toroidal_winding=float((phi[-1]-phi[0])/(2*math.pi))
    radius_min=float(np.min(s)/field.a)
    # On a regular torus containing no axis and with monotone meridional angle,
    # rational winding p/q is a torus-knot *candidate*. These are necessary
    # geometry checks; they do not certify topological isotopy computationally.
    dphi=np.diff(phase)
    monotone=bool(np.all(dphi>0) or np.all(dphi<0))
    return {'label':f'T({target_p},{target_q})_NUMERICAL_CANDIDATE',
            'classification_authority':'CANDIDATE_ONLY',
            'target_winding':goal,'bracket':[lo,hi],'bracket_windings':[left,right],
            's0_over_a':sr,'poloidal_period':period,
            'winding_per_cycle':one['W'],
            'winding_target_abs_error':abs(one['W']-goal),
            'total_poloidal_winding':meridional_winding,
            'total_azimuthal_winding':toroidal_winding,
            'full_3d_closure_relative_a':float(closure),
            'radius_min_over_a':radius_min,
            'meridional_phase_monotone':monotone,
            'poincare_return_relative_a':one['return_error'],
            'no_finite_core_claim':True,'no_independent_knot_invariant':True,
            'no_euler_stability_claim':True}
