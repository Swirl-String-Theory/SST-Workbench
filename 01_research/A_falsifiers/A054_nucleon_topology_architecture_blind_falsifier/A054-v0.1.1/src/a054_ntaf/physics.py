from __future__ import annotations
import numpy as np
from .blind_geometry import close_curve, pairwise_link_matrix

FOUR_PI=4.0*np.pi


def _all_segments(components, gammas):
    mids=[]; dls=[]; gs=[]
    for c,g in zip(components,gammas):
        x=close_curve(c); y=np.roll(x,-1,axis=0)
        mids.append(0.5*(x+y)); dls.append(y-x); gs.append(np.full(len(x),float(g)))
    return np.vstack(mids),np.vstack(dls),np.concatenate(gs)


def induced_velocity_numpy(targets, components, gammas, core):
    targets=np.asarray(targets,float)
    mids,dls,gs=_all_segments(components,gammas)
    out=np.zeros_like(targets)
    for s in range(0,len(targets),128):
        t=targets[s:s+128]
        r=t[:,None,:]-mids[None,:,:]
        den=(np.einsum('ijk,ijk->ij',r,r)+core*core)**1.5
        cr=np.cross(dls[None,:,:],r)
        out[s:s+128]=np.sum((gs[None,:,None]*cr)/den[:,:,None],axis=1)/FOUR_PI
    return out


def _native_module():
    try:
        from . import _native
        return _native
    except ImportError:
        return None


def induced_velocity_native(targets, components, gammas, core):
    native=_native_module()
    if native is None:
        raise RuntimeError('native backend unavailable')
    mids,dls,gs=_all_segments(components,gammas)
    return np.asarray(native.induced_velocity(np.asarray(targets,float),mids,dls,gs,float(core)))


def induced_velocity(targets, components, gammas, core, backend='auto'):
    if backend=='numpy_reference':
        return induced_velocity_numpy(targets,components,gammas,core)
    if backend in ('cpp_pybind11','cpp_pybind11_openmp'):
        return induced_velocity_native(targets,components,gammas,core)
    if backend!='auto':
        raise ValueError(f'unknown backend: {backend}')
    return induced_velocity_native(targets,components,gammas,core) if _native_module() is not None else induced_velocity_numpy(targets,components,gammas,core)


def backend_name():
    native=_native_module()
    if native is None:
        return 'numpy_reference'
    return 'cpp_pybind11_openmp' if bool(getattr(native,'openmp_enabled',False)) else 'cpp_pybind11'


def qualify_backend(policy='prefer_native', abs_tol=1e-11):
    """Independent native-vs-NumPy qualification on a deterministic tiny geometry."""
    actual=backend_name()
    if policy not in ('allow_numpy','prefer_native','require_native','require_openmp'):
        raise ValueError(f'unknown backend policy: {policy}')
    if actual=='numpy_reference':
        ok=policy in ('allow_numpy','prefer_native')
        return {'policy':policy,'backend':actual,'qualified':ok,'native_reference_max_abs':None,
                'reason':None if ok else 'native backend required'}
    if policy=='require_openmp' and actual!='cpp_pybind11_openmp':
        return {'policy':policy,'backend':actual,'qualified':False,'native_reference_max_abs':None,
                'reason':'OpenMP backend required'}
    t=np.linspace(0,2*np.pi,24,endpoint=False)
    c0=np.c_[np.cos(t),np.sin(t),np.zeros_like(t)]
    c1=np.c_[1.7+0.5*np.cos(t),np.zeros_like(t),0.5*np.sin(t)]
    comps=[c0,c1]
    gammas=np.array([1.0,-0.5])
    targets=np.vstack(comps)[:17]
    py=induced_velocity_numpy(targets,comps,gammas,0.03)
    cpp=induced_velocity_native(targets,comps,gammas,0.03)
    err=float(np.max(np.abs(py-cpp)))
    return {'policy':policy,'backend':actual,'qualified':bool(err<=abs_tol),
            'native_reference_max_abs':err,'native_reference_abs_tol':abs_tol,
            'reason':None if err<=abs_tol else 'native/reference mismatch'}


def velocities_on_components(components,gammas,core,cross=True,backend='auto'):
    out=[]
    if cross:
        for c in components:
            out.append(induced_velocity(c,components,gammas,core,backend=backend))
    else:
        for c,g in zip(components,gammas):
            out.append(induced_velocity(c,[c],[g],core,backend=backend))
    return out


def relative_equilibrium_residual(components, velocities):
    x=np.vstack(components); u=np.vstack(velocities); xc=x.mean(axis=0); r=x-xc
    A=np.zeros((3*len(x),6)); b=u.reshape(-1)
    for i,(rx,ry,rz) in enumerate(r):
        M=np.array([[0,rz,-ry],[-rz,0,rx],[ry,-rx,0]],float)
        A[3*i:3*i+3,:3]=np.eye(3); A[3*i:3*i+3,3:]=M
    q,*_=np.linalg.lstsq(A,b,rcond=None)
    fit=(A@q).reshape(-1,3)
    rms=np.sqrt(np.mean(np.sum((u-fit)**2,axis=1)))
    scale=np.sqrt(np.mean(np.sum(u*u,axis=1)))
    return float(rms/max(scale,1e-15)), q[:3], q[3:]


def radius_of_gyration(components):
    x=np.vstack(components); c=x.mean(axis=0)
    return float(np.sqrt(np.mean(np.sum((x-c)**2,axis=1))))


def fibonacci_sphere(n=96):
    i=np.arange(n); phi=(1+5**0.5)/2
    z=1-2*(i+0.5)/n; rr=np.sqrt(np.maximum(0,1-z*z)); a=2*np.pi*i/phi
    return np.c_[rr*np.cos(a),rr*np.sin(a),z]


def farfield_anisotropy(components,gammas,core,radius_factor=6.0,n_dir=96,directions=None,backend='auto'):
    x=np.vstack(components); ctr=x.mean(axis=0); Rg=radius_of_gyration(components)
    dirs=fibonacci_sphere(n_dir) if directions is None else np.asarray(directions,float)
    targets=ctr+radius_factor*Rg*dirs
    u=induced_velocity(targets,components,gammas,core,backend=backend)
    q=np.einsum('ij,ij->i',u,u)
    mean=float(q.mean())
    return float(q.std()/max(abs(mean),1e-20)),mean


def _component_segments(c):
    x=close_curve(c); y=np.roll(x,-1,axis=0)
    return 0.5*(x+y),y-x


def mutual_filament_energy(components,gammas,core):
    """Dimensionless regularized cross-filament Hamiltonian proxy.

    Only i<j mutual terms are included, so the value probes inter-component architecture rather
    than source-knot self-energy. The common 1/(4*pi) factor is retained. No SST constant enters.
    """
    seg=[_component_segments(c) for c in components]
    H=0.0
    for i in range(len(components)):
        mi,dli=seg[i]
        for j in range(i+1,len(components)):
            mj,dlj=seg[j]
            r=mi[:,None,:]-mj[None,:,:]
            den=np.sqrt(np.einsum('ijk,ijk->ij',r,r)+core*core)
            dot=np.einsum('ik,jk->ij',dli,dlj)
            H += float(gammas[i]*gammas[j]*np.sum(dot/den)/FOUR_PI)
    return H


def _relative_centroid_shift(components, slot, signed_fraction):
    comps=[np.asarray(c,float).copy() for c in components]
    centers=np.array([c.mean(0) for c in comps]); cm=centers.mean(0)
    d=centers[slot]-cm
    nd=float(np.linalg.norm(d))
    if nd<1e-12:
        axes=np.eye(3); d=axes[slot%3]; nd=1.0
    unit=d/nd; scale=radius_of_gyration(comps)*float(signed_fraction)
    for j in range(3):
        shift=unit*scale*(1.0 if j==slot else -0.5)
        comps[j]=comps[j]+shift
    return comps


def separation_energy_response(components,gammas,core,epsilon=0.035):
    """Finite-difference centroid-separation response for each of three relative modes."""
    h0=mutual_filament_energy(components,gammas,core)
    grads=[]; curvs=[]
    for slot in range(3):
        hm=mutual_filament_energy(_relative_centroid_shift(components,slot,-epsilon),gammas,core)
        hp=mutual_filament_energy(_relative_centroid_shift(components,slot,+epsilon),gammas,core)
        grads.append((hp-hm)/(2*epsilon))
        curvs.append((hp-2*h0+hm)/(epsilon*epsilon))
    scale=max(abs(h0),1e-12)
    return {
        'mutual_energy':float(h0),
        'separation_gradient_abs_max_norm':float(max(abs(x) for x in grads)/scale),
        'separation_curvature_median_norm':float(np.median(curvs)/scale),
        'separation_curvature_min_norm':float(min(curvs)/scale),
        'separation_mode_curvatures_norm':[float(x/scale) for x in curvs],
    }


def _state_to_components(Y,sizes):
    out=[]; o=0
    for n in sizes:
        out.append(Y[o:o+n]); o+=n
    return out


def _rhs(Y,sizes,gammas,core,backend):
    comps=_state_to_components(Y,sizes)
    return np.vstack(velocities_on_components(comps,gammas,core,True,backend=backend))


def rk4(components,gammas,core,dt,steps,backend='auto'):
    sizes=[len(c) for c in components]; Y=np.vstack(components).copy()
    for _ in range(steps):
        k1=_rhs(Y,sizes,gammas,core,backend)
        k2=_rhs(Y+0.5*dt*k1,sizes,gammas,core,backend)
        k3=_rhs(Y+0.5*dt*k2,sizes,gammas,core,backend)
        k4=_rhs(Y+dt*k3,sizes,gammas,core,backend)
        Y += dt*(k1+2*k2+2*k3+k4)/6.0
        if not np.isfinite(Y).all():
            raise FloatingPointError('non-finite RK4 state')
    return _state_to_components(Y,sizes)


def kabsch_rms(reference,current):
    X=np.vstack(reference); Y=np.vstack(current)
    Xc=X-X.mean(0); Yc=Y-Y.mean(0)
    U,S,Vt=np.linalg.svd(Yc.T@Xc); R=U@Vt
    if np.linalg.det(R)<0:
        U[:,-1]*=-1; R=U@Vt
    Ya=Yc@R
    rms=np.sqrt(np.mean(np.sum((Ya-Xc)**2,axis=1)))
    rg=np.sqrt(np.mean(np.sum(Xc*Xc,axis=1)))
    return float(rms/max(rg,1e-15))


def topology_drift(initial,final):
    if len(initial)<2: return 0.0
    A=pairwise_link_matrix(initial); B=pairwise_link_matrix(final)
    return float(np.max(np.abs(A-B)))


def centroid_separation_signature(components):
    ctr=np.array([np.asarray(c).mean(0) for c in components])
    vals=[]
    for i in range(len(ctr)):
        for j in range(i+1,len(ctr)):
            vals.append(float(np.linalg.norm(ctr[i]-ctr[j])))
    return np.asarray(vals,float)


def centroid_separation_drift(initial,final):
    a=centroid_separation_signature(initial); b=centroid_separation_signature(final)
    den=max(float(np.sqrt(np.mean(a*a))),1e-15)
    return float(np.sqrt(np.mean((b-a)**2))/den)


def circulation_vector(ncomp, sector):
    if ncomp!=3:
        raise ValueError('A054 v0.1.1 circulation ensemble is preregistered for exactly 3 components')
    signs={
      'Q0':np.array([ 1., 1., 1.]), 'Q1':np.array([-1., 1., 1.]),
      'Q2':np.array([ 1.,-1., 1.]), 'Q3':np.array([ 1., 1.,-1.]),
      'Q4':np.array([ 1., 1., 1.]), 'Q5':np.array([-1., 1., 1.]),
      'Q6':np.array([ 1.,-1., 1.]), 'Q7':np.array([ 1., 1.,-1.]),
    }
    if sector=='S0': return np.ones(3,float)
    if sector=='S1': return np.ones(3,float)/3.0
    if sector not in signs: raise ValueError(sector)
    g=signs[sector]
    return g if sector in {'Q0','Q1','Q2','Q3'} else g/3.0


def evaluate_static(components,core_ratio,sector,far_dirs=None,backend='auto',separation_epsilon=0.035):
    L=sum(np.linalg.norm(np.roll(c,-1,axis=0)-c,axis=1).sum() for c in components)
    core=core_ratio*L
    gammas=circulation_vector(len(components),sector)
    vel=velocities_on_components(components,gammas,core,True,backend=backend)
    rel,trans,omega=relative_equilibrium_residual(components,vel)
    selfvel=velocities_on_components(components,gammas,core,False,backend=backend)
    rel_self,_,_=relative_equilibrium_residual(components,selfvel)
    ani3,_=farfield_anisotropy(components,gammas,core,3.0,directions=far_dirs,backend=backend)
    ani6,_=farfield_anisotropy(components,gammas,core,6.0,directions=far_dirs,backend=backend)
    sep=separation_energy_response(components,gammas,core,epsilon=separation_epsilon)
    return {'rel_eq_residual':rel,'cross_stabilization':rel_self-rel,
            'farfield_anisotropy_r3':ani3,'farfield_anisotropy_r6':ani6,
            'fit_translation_norm':float(np.linalg.norm(trans)),
            'fit_rotation_norm':float(np.linalg.norm(omega)),'core':core,**sep}


def evaluate_dynamic(components,core_ratio,sector,dt,steps,backend='auto'):
    L=sum(np.linalg.norm(np.roll(c,-1,axis=0)-c,axis=1).sum() for c in components)
    core=core_ratio*L; gammas=circulation_vector(len(components),sector)
    fin=rk4(components,gammas,core,dt,steps,backend=backend)
    return {'shape_drift':kabsch_rms(components,fin),
            'linking_drift_max':topology_drift(components,fin),
            'centroid_separation_drift':centroid_separation_drift(components,fin),
            'finite':bool(all(np.isfinite(c).all() for c in fin)),
            'dt':float(dt),'steps':int(steps),'t_final_realized':float(dt*steps)},fin
