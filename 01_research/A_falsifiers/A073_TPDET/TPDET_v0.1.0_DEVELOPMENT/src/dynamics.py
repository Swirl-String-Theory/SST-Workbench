"""Multicomponent midpoint Rosenhead Biot-Savart filament surrogate.
This is NOT an Euler PDE solver, nor reconnecting GP dynamics.
"""
from __future__ import annotations
import numpy as np
import ctypes, sys
from pathlib import Path
from geometry import arclength_resample, q_curvature, perimeter, shape_error, point_clearance, perturb_shape

PI4=4*np.pi
_NATIVE=None
_native_path=Path(__file__).resolve().parents[1]/'native'/'bin'/('bs_native.dll' if sys.platform=='win32' else 'libbs_native.so')
if _native_path.exists():
    try:
        _NATIVE=ctypes.CDLL(str(_native_path))
        _NATIVE.bs_velocity.argtypes=[ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_double),ctypes.c_int,ctypes.c_int,ctypes.c_double,ctypes.POINTER(ctypes.c_double)]
        _NATIVE.bs_velocity.restype=None
    except OSError:_NATIVE=None

def native_available():return _NATIVE is not None


def velocity(components, gamma, core):
    """Advect each vortex vertex by summed source segments from ALL components."""
    if not core>0:raise ValueError('core must be positive')
    if _NATIVE is not None:
        xyz=np.ascontiguousarray(np.concatenate(components),dtype=np.float64)
        starts=np.asarray([0]+list(np.cumsum([len(x) for x in components])),dtype=np.int32)
        gg=np.ascontiguousarray(gamma,dtype=np.float64)
        out=np.zeros_like(xyz)
        _NATIVE.bs_velocity(xyz.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            starts.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
            gg.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            len(components),len(xyz),float(core),
            out.ctypes.data_as(ctypes.POINTER(ctypes.c_double)))
        return list(np.split(out,np.cumsum([len(x) for x in components])[:-1]))
    mids=[];dl=[]; weights=[]
    for c,g in zip(components,gamma):
        e=np.roll(c,-1,axis=0)-c
        mids.append(.5*(np.roll(c,-1,axis=0)+c))
        dl.append(e)
        weights.append(np.full(len(c),g))
    mids=np.concatenate(mids);dl=np.concatenate(dl); weights=np.concatenate(weights)
    v=[]
    # Chunk target vertices to avoid N^2 temporary memory growth.
    for c in components:
        vc=[]
        for k in range(0,len(c),64):
            r=c[k:k+64,None,:]-mids[None,:,:]
            denom=(np.einsum('ijk,ijk->ij',r,r)+core*core)**1.5
            cross=np.cross(dl[None,:,:],r)
            vc.append(np.sum((weights[None,:,None]*cross)/denom[:,:,None],axis=1)/PI4)
        v.append(np.vstack(vc))
    return v

def rk4(components,gamma,core,dt):
    def add(y,k,fac):return [a+fac*b for a,b in zip(y,k)]
    k1=velocity(components,gamma,core)
    k2=velocity(add(components,k1,dt*.5),gamma,core)
    k3=velocity(add(components,k2,dt*.5),gamma,core)
    k4=velocity(add(components,k3,dt),gamma,core)
    return [x+dt*(a+2*b+2*c+d)/6 for x,a,b,c,d in zip(components,k1,k2,k3,k4)]

def evolve(components,gamma,core,tmax,steps,record=True):
    if steps<1 or not tmax>0:raise ValueError('invalid evolution window')
    initial=[c.copy() for c in components]
    c=[x.copy() for x in initial]
    q=[ [q_curvature(x) for x in c] ];sh=[[0.]*len(c)];lengths=[[perimeter(x) for x in c]]
    clearance=[min([point_clearance(c[i],c[j]) for i in range(len(c)) for j in range(i+1,len(c))],default=None)]
    for step in range(steps):
        c=rk4(c,gamma,core,tmax/steps)
        if not all(np.isfinite(x).all() for x in c):raise FloatingPointError('nonfinite filament')
        if record:
            q.append([q_curvature(x) for x in c]);sh.append([shape_error(x,y) for x,y in zip(c,initial)])
            lengths.append([perimeter(x) for x in c])
            clearance.append(min([point_clearance(c[i],c[j]) for i in range(len(c)) for j in range(i+1,len(c))],default=None))
    if not record:
        q.append([q_curvature(x) for x in c]);sh.append([shape_error(x,y) for x,y in zip(c,initial)])
        lengths.append([perimeter(x) for x in c])
        clearance.append(min([point_clearance(c[i],c[j]) for i in range(len(c)) for j in range(i+1,len(c))],default=None))
    return dict(t=np.linspace(0,tmax,len(q)).tolist(),q=np.asarray(q).tolist(),shape=np.asarray(sh).tolist(),lengths=np.asarray(lengths).tolist(),clearance=clearance,final=c)

def run_controls(triple,gamma,core,tmax,steps,arms=('triple','single','pair','unlinked')):
    out={}
    if 'single' in arms:
        for i in range(3):
            r=evolve([triple[i]],[gamma[i]],core,tmax,steps)
            out[f'single_{i}']=result_metrics(r,initial=[triple[i]])
    if 'pair' in arms:
        for i,j in ((0,1),(0,2),(1,2)):
            r=evolve([triple[i],triple[j]],[gamma[i],gamma[j]],core,tmax,steps)
            out[f'pair_{i}{j}']=result_metrics(r,initial=[triple[i],triple[j]])
    if 'triple' in arms:
        r=evolve(triple,gamma,core,tmax,steps)
        out['triple']=result_metrics(r,initial=triple)
    if 'unlinked' in arms:
        # Translation-only control: preserve individual shapes, remove proximity.
        far=[x+np.array([8.*i,0,0]) for i,x in enumerate(triple)]
        r=evolve(far,gamma,core,tmax,steps)
        out['unlinked']=result_metrics(r,initial=far)
    if 'triple' in out and 'single_0' in out:
        out['comparison']={'shape_retention_ratio_triple_to_single':[
            out['triple']['final_shape_error'][i]/max(out[f'single_{i}']['final_shape_error'][0],1e-15) for i in range(3)],
            'interpretation':'<1 means less deformation over this horizon, NOT proven stability',
            'matched_geometry':True,'physical_stability':'UNRESOLVED'}
    return out

def result_metrics(run,initial):
    q=np.asarray(run['q']);s=np.asarray(run['shape']);le=np.asarray(run['lengths'])
    return {'times':run['t'],'q':run['q'],'shape':run['shape'],
        'final_shape_error':s[-1].tolist(),'max_shape_error':np.max(s,axis=0).tolist(),
        'max_relative_length_change':np.max(np.abs(le/le[0]-1),axis=0).tolist(),
        'min_intercomponent_clearance_proxy':min([x for x in run['clearance'] if x is not None],default=None)}

def clock_diagnostic(result, minimum_cycles=5):
    """No frequency inference unless several cycles within time horizon."""
    q=np.asarray(result['q']); t=np.asarray(result['times'])
    if len(t)<16:return {'status':'UNRESOLVED_SHORT_SERIES'}
    dt=t[1]-t[0]; total=t[-1]-t[0]
    candidates=[]
    for i in range(q.shape[1]):
        signal=q[:,i]
        signal=signal-np.linspace(signal[0],signal[-1],len(signal))
        amp=float(np.std(signal))
        if amp<1e-10:continue
        spectrum=np.abs(np.fft.rfft(signal*np.hanning(len(signal))))
        freq=np.fft.rfftfreq(len(signal),d=dt)
        if len(spectrum)<3:continue
        spectrum[0]=0.; k=int(np.argmax(spectrum))
        cycles=float(freq[k]*total)
        if k and cycles>=minimum_cycles:
            candidates.append({'component':i,'frequency_star':float(freq[k]),'cycles_observed':cycles,
              'peak_prominence':float(spectrum[k]/max(np.median(spectrum[1:]),1.e-20))})
    return {'status':'NUMERICAL_FREQUENCY_CANDIDATE' if candidates else 'UNRESOLVED_NO_QUALIFIED_CYCLES',
            'candidates':candidates,'minimum_cycles_required':minimum_cycles,
            'qualified_clock':False,'reason':'Requires independent observables, spatial/time convergence, holdout and long-horizon phase stability'}

def perturbation_growth(X,gamma,core,tmax,steps,eps):
    """Matched tangent-response of same geometry in isolated and triple systems.
    Measures endpoint perturbation amplification relative to initial perturbation.
    Not Lyapunov stability: short horizon, finite perturbation, finite discretization.
    """
    result=[]
    for j in range(3):
        changes={}
        for arm in ('isolated','triple'):
            source=[X[j]] if arm=='isolated' else X
            g=[gamma[j]] if arm=='isolated' else gamma
            target=0 if arm=='isolated' else j
            end=[];initial=[]
            for sign in (+1,-1):
                coords=[a.copy() for a in source]
                coords[target]=perturb_shape(coords[target],sign*eps)
                initial.append(coords[target].copy())
                end.append(evolve(coords,g,core,tmax,steps,record=False)['final'][target])
            d0=np.linalg.norm(initial[0]-initial[1]);d1=np.linalg.norm(end[0]-end[1])
            changes[arm]=float(d1/max(d0,1e-30))
        ratio=changes['triple']/max(changes['isolated'],1e-30)
        result.append({'component':j,'amplification_isolated':changes['isolated'],
                       'amplification_linked':changes['triple'],
                       'linked_to_isolated_amplification_ratio':float(ratio),
                       'interpretation':'ratio<1 -> less growth of this component perturbation over this horizon; NOT asymptotic stability'})
    return {'method':'balanced finite shape perturbations; induced differences measured on originally perturbed component',
        'perturbation_amplitude':eps,'per_component':result,
        'stabilization_claim':'UNRESOLVED_WITHOUT_LONG_TIME_SPATIAL_TEMPORAL_AND_TOPOLOGY_CHECKS'}
