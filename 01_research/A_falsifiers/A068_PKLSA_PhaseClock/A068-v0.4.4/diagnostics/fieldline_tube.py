"""A068 experimental T=0 flux-surface candidate via Poincare field-line returns.

Does not join an open tracer curtain into a fictitious closed torus. A real 3D
vorticity field need not admit any invariant toroidal surface; this module
returns a FAIL/UNRESOLVED measurement rather than inventing a vortex tube.
"""
from __future__ import annotations
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import linear_sum_assignment


def section_frame(w):
    w=np.asarray(w,float);w=w/np.linalg.norm(w)
    axis=np.eye(3)[np.argmin(abs(w))]
    e1=axis-w*np.dot(axis,w);e1/=np.linalg.norm(e1)
    return w,e1,np.cross(w,e1)


def trace_poincare_ring(omega_sampler,anchor,radius=.08,sides=16,
                        smax=45.,min_length=.2,rtol=1e-8,atol=1e-10,
                        max_step=.06,invariance_tol=.02,tangency_tol=.05,include_curves=False):
    """Follow vorticity lines to FIRST same-direction Poincare-section return.

    omega_sampler accepts position array (N,3) and returns sampled omega vectors.
    A successful ring return is a necessary, not sufficient, invariant-surface screen.
    """
    center=np.asarray(anchor,float)
    w=np.asarray(omega_sampler(center[None,:]))[0]
    if np.linalg.norm(w)<1e-9:raise ValueError('Vorticity too weak at anchor')
    normal,e1,e2=section_frame(w)
    angles=2*np.pi*np.arange(sides)/sides
    starts=center+radius*(np.cos(angles)[:,None]*e1+np.sin(angles)[:,None]*e2)
    returns=[];curves=[];periods=[];fails=[]
    def f(_s,y):
        v=np.asarray(omega_sampler(np.asarray(y)[None,:]))[0]
        speed=np.linalg.norm(v)
        if speed<1e-12:raise ValueError('Vanishing vorticity along path')
        return v/speed
    def hit(s,y):
        return float(np.dot(y-center,normal))
    hit.terminal=True;hit.direction=1
    for i,x0 in enumerate(starts):
        warm=solve_ivp(f,(0,min_length),x0,method='DOP853',rtol=rtol,atol=atol,
                       max_step=max_step,dense_output=True)
        if not warm.success:
            fails.append({'side':i,'reason':'INITIAL_TRACING_FAILED'});continue
        sol=solve_ivp(f,(min_length,smax),warm.y[:,-1],method='DOP853',rtol=rtol,atol=atol,
                      max_step=max_step,events=hit,dense_output=True)
        if not sol.success or not len(sol.t_events[0]):
            fails.append({'side':i,'reason':'NO_DIRECTED_POINCARE_RETURN','arc_length_reached':float(sol.t[-1])})
            continue
        t=float(sol.t_events[0][0]);xf=sol.y_events[0][0]
        ret=np.dot(xf-center,normal)
        if abs(ret)>1e-6:
            fails.append({'side':i,'reason':'SECTION_RESIDUAL','residual':float(ret)});continue
        returns.append(xf);periods.append(t)
        ss=np.linspace(0,t,96)
        curves.append(np.stack([warm.sol(q) if q<=min_length else sol.sol(q) for q in ss]))
    if fails or len(returns)!=sides:
        return {'schema':'A068-T0-POINCARE-v0.4.5','status':'UNRESOLVED',
                'ring_side_count':sides,'returned_sides':len(returns),'failures':fails,
                'flux_surface_candidate_qualified':False,'surface_mesh':None}
    returns=np.asarray(returns)
    # Poincare map is allowed to ROTATE the cross-section: set-wise not point-wise closure.
    D=np.linalg.norm(returns[:,None,:]-starts[None,:,:],axis=2)
    ii,jj=linear_sum_assignment(D)
    maxerr=float(D[ii,jj].max());rms=float(np.sqrt(np.mean(D[ii,jj]**2)))
    # Individual field-line profiles are not identically parameterized, seam is
    # only a CANDIDATE if return map is close to original cross-section as a set.
    passed=bool(maxerr<invariance_tol and np.max(periods)-np.min(periods)<0.5*np.mean(periods))
    # Straight stacking of first-return paths is just for visualization:
    # no physical topology certification from interpolated seam endpoints.
    result={'schema':'A068-T0-POINCARE-v0.4.5',
            'status':'CANDIDATE_NUMERICAL' if passed else 'INVARIANCE_SCREEN_FAIL',
            'ring_side_count':sides, 'max_return_set_mismatch':maxerr,
            'rms_return_set_mismatch':rms, 'path_length_min':float(min(periods)),
            'path_length_max':float(max(periods)),
            'ring_permutation':list(map(int,jj)),
            'section_invariance_screen_pass':passed,
            'vorticity_tangency_required':True,'tangency_tolerance':tangency_tol,
            'field_line_samples_shape':list(np.asarray(curves).shape),
            'flux_surface_candidate_qualified':False,
            'qualification':'NOT_A_CERTIFIED_EMBEDDED_VORTEX_TUBE'}

    if include_curves:result['field_line_curves']=np.asarray(curves)
    return result
