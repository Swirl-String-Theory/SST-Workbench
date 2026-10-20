"""A069-v0.5.0: genuinely 3D normalized Gross--Pitaevskii knot evolution.

Scientific constraints: GP is compressible (not the SST incompressible Euler
substrate). The solid-angle phase is built from a *spanning 2-chain* of the
closed curve: Ω/2 gives a 2π-winding order-parameter phase around the line.
The 2-chain may self-intersect; only the boundary, and local circulation, are
physically meaningful. No arbitrary nearest-point-angle phase is assigned.
Absolute energy includes sound emitted by a nonstationary seed. Gauge-invariant
shape diagnostics are NOT clocks unless independently spectrally qualified.
"""
from __future__ import annotations
from pathlib import Path
from functools import lru_cache
import hashlib,json,math
import numpy as np
from scipy.spatial import cKDTree
from numba import njit,prange
from .hasimoto import analytic,prepare

@njit(parallel=True,cache=True)
def _solid_angle_points(points,poly,anchor):
    m=len(poly); ans=np.empty(len(points),np.float64)
    for p in prange(len(points)):
        x,y,z=points[p,0],points[p,1],points[p,2]
        ax,ay,az=anchor[0]-x,anchor[1]-y,anchor[2]-z
        an=math.sqrt(ax*ax+ay*ay+az*az)
        total=0.0
        for j in range(m):
            b=poly[j];c=poly[(j+1)%m]
            bx,by,bz=b[0]-x,b[1]-y,b[2]-z
            cx,cy,cz=c[0]-x,c[1]-y,c[2]-z
            bn=math.sqrt(bx*bx+by*by+bz*bz)
            cn=math.sqrt(cx*cx+cy*cy+cz*cz)
            det=ax*(by*cz-bz*cy)+ay*(bz*cx-bx*cz)+az*(bx*cy-by*cx)
            denominator=an*bn*cn+(ax*bx+ay*by+az*bz)*cn+(bx*cx+by*cy+bz*cz)*an+(cx*ax+cy*ay+cz*az)*bn
            total+=2*math.atan2(det,denominator)
        ans[p]=total/2
    return ans


def _seed(kind,mirror=False,nb=160,extent=2.05):
    raw=prepare(kind, n=1200)['xyz']
    if mirror:raw[:,0]*=-1
    # Same physical maximum radius across cases, without per-case mass fits.
    raw=raw-np.mean(raw,axis=0)
    scale=extent/np.max(np.linalg.norm(raw,axis=1))
    raw*=scale
    ids=np.round(np.linspace(0,len(raw),nb,endpoint=False)).astype(int)%len(raw)
    poly=raw[ids]
    return poly,raw


def mesh(n=48,box=10.0):
    if n<16 or n%2:raise ValueError('even n>=16')
    pos=(np.arange(n)-n/2)*box/n
    return np.meshgrid(pos,pos,pos,indexing='ij')


def initialize(kind='A',mirror=False,n=48,box=10.,xi=.42,segments=160):
    if box<=0 or xi<=0 or 2*xi>=box:raise ValueError('invalid box and core')
    poly,raw=_seed(kind,mirror,segments)
    xx,yy,zz=mesh(n,box)
    pts=np.column_stack([xx.ravel(),yy.ravel(),zz.ravel()])
    anchor=np.mean(raw,axis=0)
    phase=_solid_angle_points(pts,poly,np.asarray(anchor,dtype=float))
    # nearest arclength-resolved centreline supplies ONLY modulus, not phase
    kd=cKDTree(raw)
    dist=kd.query(pts,workers=1)[0]
    amp=np.tanh(dist/(math.sqrt(2)*xi))
    psi=(amp*np.exp(1j*phase)).reshape((n,)*3)
    # Homogeneous order parameter at all periodic faces; no phase branch cut
    # may be tapered through the knotted vortex core. The compact transition
    # lies strictly outside the full centerline-plus-core envelope.
    r=np.sqrt(xx*xx+yy*yy+zz*zz)
    rin=.32*box;rout=.44*box
    if np.max(np.linalg.norm(raw,axis=1))+2*xi>=rin:
        raise ValueError('core overlaps periodic boundary taper; enlarge box or rescale knot')
    v=np.clip((rout-r)/(rout-rin),0.,1.)
    taper=v*v*v*(10-15*v+6*v*v)
    psi=1+taper*(psi-1)
    dx=box/n
    result={'source':'2015_unrelaxed_'+kind+('_mirror' if mirror else ''),'n':n,'box':box,'xi':xi,'segments':segments,'dx':dx,
      'core_cells':xi/dx,'periodic_face_gap':float(max(np.max(abs(psi[0]-psi[-1])),np.max(abs(psi[:,0]-psi[:,-1])),np.max(abs(psi[:,:,0]-psi[:,:,-1])))),
      'min_density':float(np.min(abs(psi)**2)),'model':'normalized_compressible_GP','method':'oriented_spanning_2chain_solid_angle_half_phase',
      'geometry_radius':float(np.max(np.linalg.norm(raw,axis=1)))}
    return psi,result

@lru_cache(maxsize=8)
def _kinetic(n,box,dt):
    k=2*np.pi*np.fft.fftfreq(n,d=box/n)
    k2=k[:,None,None]**2+k[None,:,None]**2+k[None,None,:]**2
    return np.exp(-.5j*dt*k2),k2


def step(psi,box,dt,kin=None):
    if kin is None:kin=_kinetic(psi.shape[0],box,dt)[0]
    a=psi*np.exp(-.5j*dt*(abs(psi)**2-1))
    a=np.fft.ifftn(np.fft.fftn(a)*kin)
    return a*np.exp(-.5j*dt*(abs(a)**2-1))


def conserved(psi,box):
    n=psi.shape[0];dx=box/n
    z=np.fft.fftn(psi);k=2*np.pi*np.fft.fftfreq(n,d=dx)
    grad2=0.
    for ax in range(3):
        shape=[1,1,1];shape[ax]=n
        grad2+=np.mean(abs(np.fft.ifftn(z*(1j*k.reshape(shape))))**2)
    return float(np.mean(abs(psi)**2)*box**3),float((.5*grad2+.5*np.mean((abs(psi)**2-1)**2))*box**3)


def plaquette_vortices(psi):
    ph=psi/(np.abs(psi)+1e-30)
    link=[np.angle(np.conj(ph)*np.roll(ph,-1,axis=ax)) for ax in range(3)]
    counts={}
    for i in range(3):
        j=(i+1)%3
        tot=link[i]+np.roll(link[j],-1,axis=i)-np.roll(link[i],-1,axis=j)-link[j]
        winding=np.rint(tot/(2*np.pi)).astype(np.int8)
        counts['xy' if (i,j)==(0,1) else ('yz' if (i,j)==(1,2) else 'zx')] = {'count':int(np.sum(abs(winding))), 'signed_sum':int(np.sum(winding)), 'positive':int(np.sum(winding>0)), 'negative':int(np.sum(winding<0))}
    return counts


def shape_observable(psi,box):
    n=psi.shape[0];dx=box/n
    # Density-only, invariant under global complex phase, translations and rigid spatial rotations.
    # This is not an internal phase; sound depletion can contaminate its time series.
    w=np.maximum(0.,1-abs(psi)**2)**2
    coords=(np.arange(n)-n/2)*dx
    X,Y,Z=np.meshgrid(coords,coords,coords,indexing='ij')
    norm=float(w.sum())
    cm=np.array([np.sum(w*X),np.sum(w*Y),np.sum(w*Z)])/max(norm,1e-30)
    vec=[X-cm[0],Y-cm[1],Z-cm[2]]
    cov=np.array([[np.sum(w*vec[i]*vec[j])/norm for j in range(3)] for i in range(3)])
    eig=np.linalg.eigvalsh(cov)
    return float((eig[-1]-eig[0])/max(eig.sum(),1e-30)),float(np.sum(w)*dx**3)


def simulate(kind='A',mirror=False,n=48,box=10.,xi=.42,dt=.006,steps=120,segments=140,diag_every=4,retain_final=False):
    psi,meta=initialize(kind,mirror,n,box,xi,segments)
    m0,e0=conserved(psi,box)
    init_vort=plaquette_vortices(psi)
    if sum(x['count'] for x in init_vort.values())<=0:raise RuntimeError('no vortex detected on initial GP lattice')
    kin=_kinetic(n,box,dt)[0]
    trace=[]
    def record(i):
        mass,energy=conserved(psi,box)
        shape,dep=shape_observable(psi,box)
        trace.append({'t':i*dt,'mass_rel':(mass-m0)/m0,'energy_rel':(energy-e0)/e0,'shape_scalar':shape,'depletion_volume':dep})
    record(0)
    for i in range(1,steps+1):
        psi=step(psi,box,dt,kin)
        if i%diag_every==0 or i==steps:record(i)
    end_vort=plaquette_vortices(psi)
    result={'schema':'A069-GP3D-KNOT-TRAJECTORY-1','kind':kind,'mirror':mirror,'parameters':meta,
       'initial_vortices':init_vort,'final_vortices':end_vort,'steps':steps,'dt':dt,'total_time':steps*dt,
       'max_mass_drift':float(max(abs(d['mass_rel']) for d in trace)),
       'max_energy_drift':float(max(abs(d['energy_rel']) for d in trace)),
       'trace':trace,'classification':'REAL_3D_GP_KNOT_INITIAL_VALUE_EVOLUTION_SIMULATION_ONLY',
       'topology_certified_over_time':False,'knotted_initial_field':True,'incompressible_euler_solution':False,
       'independent_physical_holdout':False,'physical_clock_claim':False}
    return (result,psi) if retain_final else result


def bogoliubov_bulk_control(n=24,box=12.0,dt=.01,steps=4000,amplitude=1e-3,mode_index=3):
    """Independent bulk BdG prediction with >4 complete observed cycles.

    The expected omega is used only AFTER spectral frequency extraction;
    fitting is initialized from the data FFT, never from the target.
    """
    k=mode_index*2*np.pi/box; eps=k*k/2
    omega=math.sqrt(eps*(eps+2))
    coords=np.arange(n)*box/n
    x=np.cos(k*coords)[:,None,None]
    psi=(1+amplitude*x)*np.ones((1,n,n),complex)
    kin=_kinetic(n,box,dt)[0]
    sig=[]
    for j in range(steps+1):
        den=abs(psi)**2-1
        sig.append(float(np.mean(den*np.cos(k*coords)[:,None,None])*2))
        if j<steps:psi=step(psi,box,dt,kin)
    from scipy.optimize import minimize_scalar
    ts=np.arange(steps+1)*dt;y=np.asarray(sig)
    N=len(y); frequencies=np.fft.rfftfreq(N,dt)
    spec=np.abs(np.fft.rfft((y-y.mean())*np.hanning(N)))
    spec[0]=0; peak=int(np.argmax(spec));f0=float(frequencies[peak]);binw=float(frequencies[1])
    if f0<=0:return {'status':'FAIL','reason':'no positive FFT peak'}
    def loss(w):
        mat=np.column_stack([np.cos(w*ts),np.sin(w*ts),np.ones_like(ts)])
        coeff=np.linalg.lstsq(mat,y,rcond=None)[0]
        return np.mean((y-mat@coeff)**2)
    lower=max(2*np.pi*(f0-binw*.7),1e-7);upper=2*np.pi*(f0+binw*.7)
    search=minimize_scalar(loss,bounds=(lower,upper),method='bounded',options={'xatol':1e-10})
    measured_cycles=search.x*ts[-1]/(2*np.pi)
    ok=(measured_cycles>=4 and abs(search.x/omega-1)<0.01)
    return {'status':'PASS' if ok else 'FAIL',
      'prediction_analytic':omega,'observed_fit':float(search.x),'relative_error':float(abs(search.x/omega-1)),
      'observed_cycles':float(measured_cycles),'fft_frequency_initial_guess':2*np.pi*f0,
      'fit_search_interval_rad_per_time':[lower,upper],
      'fit_is_independent_of_analytic_target':True,
      'amplitude':amplitude,'n':n,'steps':steps,'dt':dt,
      'classification':'UNIFORM_BULK_GP_BOGOLIUBOV_MODE_CONTROL_NOT_KNOT_EIGENMODE'}


def tangent_step(psi,dpsi,box,dt):
    """Exact real-Fréchet derivative of one 3D GP Strang step.

    The two-component (δψ,δψ*) BdG tangent evolution is a well-defined
    finite-time linear-response diagnostic even when the knot is NOT a
    relative equilibrium. Its propagator is not an intrinsic eigenmode.
    """
    def nonlinear(z,dz,h):
        fac=np.exp(-1j*h*(abs(z)**2-1))
        return z*fac,fac*(dz-1j*2*h*z*np.real(np.conj(z)*dz))
    kin=_kinetic(psi.shape[0],box,dt)[0]
    a,da=nonlinear(psi,dpsi,dt/2)
    a=np.fft.ifftn(np.fft.fftn(a)*kin)
    da=np.fft.ifftn(np.fft.fftn(da)*kin)
    return nonlinear(a,da,dt/2)


def tangent_validation(kind='A',n=24,box=10.,xi=.5,dt=.004,segments=80,steps=8,eps=1e-6):
    psi,_=initialize(kind,n=n,box=box,xi=xi,segments=segments)
    X,Y,Z=mesh(n,box)
    delta=(np.cos(1.3*X+.45*Z)+1j*np.sin(.5*Y-1.2*Z))*np.exp(-.5*(X*X+Y*Y+Z*Z)/2**2)
    delta=delta/np.linalg.norm(delta.ravel())
    p=np.array(psi);t=np.array(delta)
    pert=psi+eps*delta
    for _ in range(steps):
        p,t=tangent_step(p,t,box,dt)
        pert=step(pert,box,dt)
    finite_difference=(pert-p)/eps
    err=float(np.linalg.norm((finite_difference-t).ravel())/max(np.linalg.norm(t.ravel()),1e-12))
    return {'schema':'A069-GP3D-BDG-TANGENT-CHECK-1','status':'PASS' if err<1e-4 else 'FAIL',
            'relative_linearization_error':err,'epsilon':eps,'n':n,'steps':steps,
            'classification':'LINEARIZED_TIME_DEPENDENT_3D_GP_NOT_STATIONARY_EIGENMODE'}


def candidate_frequency(trace, min_cycles=4, min_snr=8):
    """Falsifiable, conservative non-claim for intrinsic mode identifiability.

    A scalar shape trace is rotation/global-phase/translation neutral but not
    source-independent; sound contamination and rigid deformation are possible.
    No calibration against a particle clock is allowed.
    """
    from scipy.signal import detrend
    t=np.array([d['t'] for d in trace]);y=np.array([d['shape_scalar'] for d in trace]);
    if len(t)<16:return {'status':'UNRESOLVED','reason':'too_few_samples','frequency':None}
    dt=float(np.median(np.diff(t)));N=len(y)
    if np.max(np.abs(np.diff(t)-dt))>dt*.05:
        return {'status':'UNRESOLVED','reason':'nonuniform_trace_timing','frequency':None}
    # Train only on first half, evaluate the full later half as a holdout.
    Ntrain=N//2
    if Ntrain<12:return {'status':'UNRESOLVED','reason':'insufficient_training_window','frequency':None}
    ytrain=detrend(y[:Ntrain],type='linear');fft=np.fft.rfft(ytrain*np.hanning(Ntrain))
    strength=abs(fft);freq=np.fft.rfftfreq(Ntrain,d=dt)
    if len(strength)<3:return {'status':'UNRESOLVED','reason':'short_train_fft','frequency':None}
    strength[0]=0.
    dominant=int(np.argmax(strength))
    cycles=float(freq[dominant]*(t[Ntrain-1]-t[0]));snr=float(strength[dominant]/max(np.median(strength[1:]),1e-30))
    # Never declare a clock from fewer than four unambiguous shape oscillations.
    if cycles<min_cycles:
        return {'status':'UNRESOLVED','reason':'insufficient_complete_internal_cycles',
                'diagnostic_train_cycles':cycles,'diagnostic_spectral_snr':snr,'frequency':None}
    if snr<min_snr:return {'status':'UNRESOLVED','reason':'low_spectral_signal','diagnostic_snr':snr,'frequency':None}
    # Sufficient cycles are NECESSARY but NOT SUFFICIENT. No physical eigenmode
    # is claimed until a converged co-moving stationary reference exists.
    return {'status':'UNRESOLVED','reason':'mode_requires_stationary_base_floquet_and_grid_core_holdout',
            'diagnostic_frequency':float(2*np.pi*freq[dominant]),'diagnostic_cycles':cycles,'frequency':None}
