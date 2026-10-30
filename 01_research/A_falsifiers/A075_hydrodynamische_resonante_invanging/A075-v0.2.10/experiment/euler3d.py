"""A075 v0.2.8: periodic Fourier--Galerkin incompressible Euler reference provider.

This is a *3D finite-width vorticity field* (not a filament evolution), with
no enforced axisymmetry, no viscosity and no feedback forcing. Periodic-image
interactions remain a physical/numerical domain limitation. 2/3 de-aliasing.
No claims of resolved core, topology preservation or Euler convergence are
made unless independent downstream gates pass.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import hashlib
import numpy as np
from scipy import fft as scipy_fft
from scipy.signal import find_peaks

@dataclass(frozen=True)
class Config:
    n: int = 40
    box: float = 10.0
    core: float = 0.42
    rho: float = 1.0
    gamma_receiver: float = 1.0
    gamma_donor: float = 1.4
    dt: float = 0.04
    final_time: float = 1.6
    geometry: str = '0_1'
    incoming: bool = True
    receiver_on: bool = True
    xyz_root: str = 'inputs'
    steps_per_diagnostic: int = 2
    window_halfwidth: float = 1.7
    window_edge: float = 0.35
    seed: int = 7502001
    threads: int = 1
    backend: str = "cpu-scipy-fft"
    adaptive: bool = True
    cfl_target: float = 0.15
    max_core_shift: float = 0.15
    max_vorticity_turn: float = 0.12
    dt_min: float = 1.e-6
    max_steps: int = 100000
    gpu_precision: str = "fp32"
    initial_condition: str = "legacy_coupled"  # legacy_coupled | ruban_isolated | legacy_t23_isolated
    ruban_seed_path: str = ""


def periodic_delta(x, ref, box):
    return (x-ref+box/2)%box-box/2


def resample_closed(points, npts):
    points=np.asarray(points,dtype=float)
    if len(points)<12 or points.shape[1:]!=(3,) or not np.isfinite(points).all():
        raise ValueError('Need >=12 finite 3-column XYZ records')
    if np.linalg.norm(points[0]-points[-1]) < 1e-10:points=points[:-1]
    leg=np.linalg.norm(np.roll(points,-1,axis=0)-points,axis=1)
    if np.min(leg)<1e-12:raise ValueError('Degenerate XYZ segments')
    s=np.r_[0,np.cumsum(leg)]
    ss=np.linspace(0,s[-1],npts,endpoint=False)
    return np.column_stack([np.interp(ss,s,np.r_[points[:,i],points[0,i]]) for i in range(3)])


def curve(kind, radius, center_z, nseg=192, xyz_root='inputs'):
    t=2*np.pi*np.arange(nseg)/nseg
    provenance={'kind':kind,'source':'ANALYTIC'}
    if kind=='0_1':
        p=np.column_stack([radius*np.cos(t),radius*np.sin(t),np.zeros_like(t)])
    elif kind=='3_1':
        # Standard T(2,3) parametrization; knot type from topology of embedding.
        p=np.column_stack([(1+0.32*np.cos(3*t))*np.cos(2*t),
                           (1+0.32*np.cos(3*t))*np.sin(2*t),0.32*np.sin(3*t)])
        p*=radius/np.max(np.linalg.norm(p[:,:2],axis=1))
        provenance['source']='ANALYTIC_TORUS_T23_NOT_IDEAL_KNOT'
    elif kind in ('5_2','6_1'):
        file=Path(xyz_root)/f'KNOT_{kind}_N2048_ORIG.xyz'
        if not file.is_file():
            raise FileNotFoundError(f'Required real source missing: {file}. No synthetic knot substituted.')
        raw=file.read_bytes()
        arr=np.loadtxt(file,comments='#',usecols=(0,1,2))
        p=resample_closed(arr,nseg)
        p-=p.mean(axis=0)
        p*=radius/np.max(np.linalg.norm(p[:,:2],axis=1))
        provenance.update(source='USER_XYZ',source_file=file.name,sha256=hashlib.sha256(raw).hexdigest(),
                          topology_verification='REQUIRES_INDEPENDENT_CHECK')
    else: raise ValueError(f'Unsupported kind {kind}')
    p[:,2]+=center_z
    if kind in ('0_1','3_1'):p=resample_closed(p,nseg)
    return p,provenance


class Euler3D:
    def __init__(self,cfg:Config):
        n=cfg.n
        if n<16 or n%2:raise ValueError('n must be even >= 16')
        if cfg.core<=0 or cfg.box<=0 or cfg.rho<=0:raise ValueError('positive scales only')
        if not 1 <= cfg.threads <= 64:raise ValueError("threads must be 1..64")
        if cfg.backend not in ("cpu-scipy-fft", "cpu-numpy-reference", "cpp-hybrid"):
            raise RuntimeError(f"Backend {cfg.backend!r} has not passed A075 3D Euler parity; no CPU fallback is permitted")
        self.c=cfg
        self._cpp=None
        if cfg.backend == 'cpp-hybrid':
            from .native import load_cpp
            self._cpp=load_cpp()
        self.dx=cfg.box/n
        f=2*np.pi*np.fft.fftfreq(n,d=self.dx)
        self.k=np.meshgrid(f,f,f,indexing='ij')
        self.k2=sum(kk**2 for kk in self.k)
        self.k2safe=np.where(self.k2>0,self.k2,1.0)
        self.mask=(np.abs(np.fft.fftfreq(n)*n)[:,None,None]<=n/3)&(np.abs(np.fft.fftfreq(n)*n)[None,:,None]<=n/3)&(np.abs(np.fft.fftfreq(n)*n)[None,None,:]<=n/3)
        self.mask=self.mask.astype(float)
        q=(np.arange(n)+0.5)*self.dx-cfg.box/2
        self.X=np.meshgrid(q,q,q,indexing='ij')
        self.uu=np.stack(self.X,axis=-1)

    def fft(self,x):
        if self.c.backend == "cpu-numpy-reference":return np.fft.fftn(x,axes=(0,1,2))
        return scipy_fft.fftn(x,axes=(0,1,2),workers=self.c.threads)
    def ifft(self,x):
        if self.c.backend == "cpu-numpy-reference":return np.fft.ifftn(x,axes=(0,1,2)).real
        return scipy_fft.ifftn(x,axes=(0,1,2),workers=self.c.threads).real
    def project(self,vhat):
        dot=sum(self.k[j]*vhat[...,j] for j in range(3))/self.k2safe
        w=np.stack([vhat[...,j]-self.k[j]*dot for j in range(3)],axis=-1)
        w*=self.mask[...,None]
        w[0,0,0,:]=0
        return w
    def curl_hat(self,uh):
        k=self.k
        return 1j*np.stack([k[1]*uh[...,2]-k[2]*uh[...,1],
                            k[2]*uh[...,0]-k[0]*uh[...,2],
                            k[0]*uh[...,1]-k[1]*uh[...,0]],axis=-1)

    def source_curve(self, wh, curve_points, gamma):
        # Circulation-current integrated to a voxel with cloud-in-cell deposition,
        # then Gaussian spectral convolution and Leray projection.
        points=curve_points
        d=np.roll(points,-1,axis=0)-points
        mids=points+d/2
        n=self.c.n;dx=self.dx;L=self.c.box
        grid=(mids+L/2)/dx-0.5
        floor=np.floor(grid).astype(int);frac=grid-floor
        for a in (0,1):
          for b in (0,1):
           for c in (0,1):
            xyz=(floor+np.array([a,b,c]))%n
            weight=np.prod(np.where(np.array([a,b,c])[None,:]==1,frac,1-frac),axis=1)
            for j in range(3):
                np.add.at(wh[...,j],tuple(xyz.T),gamma*d[:,j]*weight/dx**3)

    def initial_velocity(self):
        c=self.c;vort=np.zeros((c.n,c.n,c.n,3),float)
        prov=[]
        # Single source-free filament initialized as finite-width vorticity.
        # Neither periodic Euler nor its Gaussian sigma is Ruban's filament model.
        if c.initial_condition in ('ruban_isolated','legacy_t23_isolated'):
            from .ruban import load_primary_seed, analytic_torus
            if c.initial_condition=='ruban_isolated':
                p,pr=load_primary_seed(c.ruban_seed_path)
            else:
                p=analytic_torus(0.32,n=2048)
                pr={'kind':'3_1','source':'LEGACY_ANALYTIC_CONTROL','B0':0.32,'R0':1.0}
            # Exactly R0=1 and r0=B0: no legacy radial normalization.
            self.source_curve(vort,p,c.gamma_receiver)
            prov.append(pr)
        elif c.initial_condition!='legacy_coupled':
            raise ValueError('Unknown initial_condition: '+str(c.initial_condition))
        else:
            # Two overlapping receiver structures and an independent incoming 0_1.
            for kind,r,z,gamma in ([('0_1',0.98,0.0,c.gamma_receiver),(c.geometry,0.82,0.65,c.gamma_receiver)] if c.receiver_on else []):
                p,pr=curve(kind,r,z,xyz_root=c.xyz_root)
                self.source_curve(vort,p,gamma);prov.append(pr)
            if c.incoming:
                p,pr=curve('0_1',0.55,-2.1,xyz_root=c.xyz_root)
                self.source_curve(vort,p,c.gamma_donor);prov.append(pr)
        omh=self.project(self.fft(vort))
        omh*=np.exp(-0.5*c.core**2*self.k2)[...,None]
        kh=self.k
        uh=1j*np.stack([kh[1]*omh[...,2]-kh[2]*omh[...,1],
                        kh[2]*omh[...,0]-kh[0]*omh[...,2],
                        kh[0]*omh[...,1]-kh[1]*omh[...,0]],axis=-1)/self.k2safe[...,None]
        uh=self.project(uh)
        return uh,prov

    def rhs(self,uh):
        uh=self.project(uh)
        u=self.ifft(uh)
        omega=self.ifft(self.curl_hat(uh))
        lamb=self._cpp.cross3(u,omega) if self._cpp is not None else np.cross(u,omega)
        return self.project(self.fft(lamb))

    def rk4(self,uh,dt):
        k1=self.rhs(uh)
        k2=self.rhs(uh+dt*k1/2)
        k3=self.rhs(uh+dt*k2/2)
        k4=self.rhs(uh+dt*k3)
        return self.project(uh+dt*(k1+2*k2+2*k3+k4)/6)

    def pressure(self,uh):
        u=self.ifft(uh)
        omg=self.ifft(self.curl_hat(uh))
        b=self.fft(np.cross(u,omg))
        q_hat=-1j*sum(self.k[j]*b[...,j] for j in range(3))/self.k2safe
        q_hat[0,0,0]=0
        return self.c.rho*(self.ifft(q_hat)-0.5*np.sum(u*u,axis=-1))

    def window(self,center):
        L=self.c.box;c=self.c
        W=np.ones((c.n,c.n,c.n))
        for ax in range(3):
            d=periodic_delta(self.X[ax],center[ax],L)
            w=0.5*(1-np.tanh((np.abs(d)-c.window_halfwidth)/c.window_edge))
            W*=w
        grad=np.stack([self.ifft(1j*self.k[j]*self.fft(W)) for j in range(3)],axis=-1)
        return W,grad

    def stats(self,uh,center,w):
        c=self.c;dx3=self.dx**3
        u=self.ifft(uh)
        omg=self.ifft(self.curl_hat(uh))
        p=self.pressure(uh)
        e=c.rho/2*np.sum(u*u,axis=-1)
        W,grad=self.window(center)
        # RHS volume ledger: - integral_boundary [e(u-w)+p u] . n dA
        flux=np.sum(grad*((e+p)[...,None]*u-e[...,None]*np.asarray(w)),axis=-1).sum()*dx3
        E=float(np.sum(e)*dx3)
        Ew=float(np.sum(W*e)*dx3)
        div=float(np.sqrt(np.mean(self.ifft(sum(1j*self.k[j]*uh[...,j] for j in range(3)))**2)))
        wm=float(np.sum(W*np.linalg.norm(omg,axis=-1))*dx3)
        receiver_signal=float(np.sum(W*omg[...,2]**2)*dx3)
        maxu=float(np.max(np.linalg.norm(u,axis=-1)))
        return {'E_global':E,'E_window':Ew,'rhs_flux':float(flux),'omega_window_l1':wm,
                'omega_z2_window':receiver_signal,'div_rms':div,'max_speed':maxu,
                'cfl':maxu*c.dt/self.dx}

    def probe_u(self,uh,center):
        """Trilinear velocity at a frame marker; not a knot centroid."""
        u=self.ifft(uh)
        grid=(np.asarray(center)+self.c.box/2)/self.dx-0.5
        idx=np.floor(grid).astype(int);fr=grid-idx;out=np.zeros(3)
        for a in (0,1):
          for b in (0,1):
           for c in (0,1):
            ind=(idx+np.array([a,b,c]))%self.c.n
            q=np.prod(np.where(np.array([a,b,c])==1,fr,1-fr))
            out+=q*u[tuple(ind)]
        return out

    def run(self, center_track=None):
        c=self.c
        steps=round(c.final_time/c.dt)
        if steps<1 or abs(steps*c.dt-c.final_time)>1e-9:raise ValueError('T/dt must be an integer')
        uh,prov=self.initial_velocity()
        E0=self.stats(uh,[0,0,0.3],[0,0,0])['E_global']
        # center follows a passive, independent marker; w is its local velocity.
        center=np.array([0.,0.,.3]);data=[]
        if center_track is not None:
            center_track=np.asarray(center_track,dtype=float)
            if center_track.shape!=(steps+1,3):raise ValueError('center_track must contain one center per time step')
        centers=[]
        for i in range(steps+1):
            t=i*c.dt
            if center_track is not None:
                center=center_track[i].copy()
                j0=max(0,i-1);j1=min(steps,i+1)
                w=periodic_delta(center_track[j1],center_track[j0],c.box)/((j1-j0)*c.dt)
            else:w=self.probe_u(uh,center)
            centers.append(center.copy())
            if i%c.steps_per_diagnostic==0 or i==steps:
                row={'t':float(t),'center':center.tolist(),'w':w.tolist(),**self.stats(uh,center,w)}
                data.append(row)
            if i!=steps:
                uh_next=self.rk4(uh,c.dt)
                if center_track is None:
                    center=(center+c.dt/2*(w+self.probe_u(uh_next,center+c.dt*w))+c.box/2)%c.box-c.box/2
                uh=uh_next
        es=np.array([x['E_global'] for x in data]);times=np.array([x['t'] for x in data]);ev=np.array([x['E_window'] for x in data]);rhs=np.array([x['rhs_flux'] for x in data]);
        resid=np.diff(ev)-.5*np.diff(times)*(rhs[:-1]+rhs[1:])
        denom=max(abs(E0),1.e-16)
        sig=np.array([x['omega_z2_window'] for x in data])
        peaks,_=find_peaks(sig,prominence=max(1e-14,.015*np.ptp(sig)))
        periods=np.diff(times[peaks]) if len(peaks)>=3 else []
        period=float(np.median(periods)) if len(periods)>=3 else None
        return {'schema':'A075-EULER3D-SCREENING-2','config':c.__dict__,'geometry_provenance':prov,'timeseries':data,'center_track':np.asarray(centers).tolist(),
                'global_relative_energy_drift':float(np.max(np.abs(es-E0))/denom),
                'max_window_budget_residual_over_E0':float(np.max(np.abs(resid))/denom) if len(resid) else None,
                'max_CFL':max(x['cfl'] for x in data),'receiver_peak_count':len(peaks),
                'receiver_period_s':period,'receiver_clock_qualified':False,
                'note':'Periodic Galerkin Euler screening: diffusion-free; no late hold / physical certification without core, box, space/time, flux and clock gates.'}


    def global_energy_hat(self,uh):
        # NumPy/SciPy forward FFTs are unnormalized; Parseval gives J on full box.
        return float(.5*self.c.rho*self.dx**3/self.c.n**3 * np.sum(np.abs(uh)**2))

    def adapt_metrics(self,uh):
        u=self.ifft(uh)
        om=self.ifft(self.curl_hat(uh))
        vmax=float(np.max(np.linalg.norm(u,axis=-1)))
        omax=float(np.max(np.linalg.norm(om,axis=-1)))
        return vmax,omax


def stable_dt(cfg, dx, umax, omax, remaining):
    """A time step bound on grid shift, initial core sigma shift, and rotation proxy.

    Vorticity magnitude is a rotation proxy, NOT a bound on full symmetric strain.
    """
    if min(cfg.cfl_target,cfg.max_core_shift,cfg.max_vorticity_turn,cfg.dt_min) <= 0:
        raise ValueError('adaptive safety factors and dt_min must be positive')
    u=max(umax,1.e-30); omg=max(omax,1.e-30)
    cap=min(cfg.dt, cfg.cfl_target*dx/u, cfg.max_core_shift*cfg.core/u,
            cfg.max_vorticity_turn/omg, remaining)
    if cap < cfg.dt_min and remaining > cfg.dt_min*1.e-6:
        # Allow tiny final-time remainders within floating point; do not ignore a real CFL failure.
        if remaining > cfg.dt_min: raise RuntimeError('ADAPTIVE_DT_FLOOR: required dt below dt_min')
    return float(cap)


def run_paired(cfg):
    """Synchronized donor/control Euler trajectories; adaptive RK4 with an exact common final time.

    The receiver window follows ONLY the reference field. Every iteration produces
    a global numerical energy ledger; physical localized flux is sampled separately.
    """
    from dataclasses import replace
    if cfg.backend in ('arc-xpu','torch-cpu-reference'):
        from .euler_torch import TorchEuler3D
        solver=TorchEuler3D
    else:
        solver=Euler3D
    src=solver(cfg)
    ref=solver(replace(cfg,incoming=False))
    hs,ps=src.initial_velocity(); hr,pr=ref.initial_velocity()
    Es0=src.global_energy_hat(hs); Er0=ref.global_energy_hat(hr)
    center=np.array([0.,0.,.3]); t=0.; iteration=0
    data_s=[];data_r=[];centers=[];steps=[]
    tiny=max(1.e-13, cfg.final_time*1.e-12)
    while True:
        done=(cfg.final_time-t <= tiny)
        if iteration > cfg.max_steps:raise RuntimeError('MAX_STEPS_EXCEEDED')
        w=ref.probe_u(hr,center)
        if iteration%cfg.steps_per_diagnostic == 0 or done:
            row_s={'t':t,'center':center.tolist(),'w':w.tolist(),**src.stats(hs,center,w)}
            row_r={'t':t,'center':center.tolist(),'w':w.tolist(),**ref.stats(hr,center,w)}
            row_s['cfl']=steps[-1]['max_shift_cells'] if steps else 0.
            row_r['cfl']=steps[-1]['max_shift_cells'] if steps else 0.
            data_s.append(row_s);data_r.append(row_r)
        centers.append([float(t),*center.tolist()])
        if done:break
        us,os=src.adapt_metrics(hs); ur,orr=ref.adapt_metrics(hr)
        vmax=max(us,ur);omega=max(os,orr)
        dt=stable_dt(cfg,src.dx,vmax,omega,cfg.final_time-t) if cfg.adaptive else min(cfg.dt,cfg.final_time-t)
        if not np.isfinite(dt) or dt<=0:raise RuntimeError('INVALID_DT')
        en_s_before=src.global_energy_hat(hs); en_r_before=ref.global_energy_hat(hr)
        # Use the stage-start bound, but verify against the accepted endpoint.
        # The endpoint check closes the loophole where a vortex accelerates
        # during a step and makes the initially safe dt too large.
        retries=0
        while True:
            hs_new=src.rk4(hs,dt);hr_new=ref.rk4(hr,dt)
            us_after,os_after=src.adapt_metrics(hs_new)
            ur_after,or_after=ref.adapt_metrics(hr_new)
            vcheck=max(vmax,us_after,ur_after)
            ocheck=max(omega,os_after,or_after)
            safe=(not cfg.adaptive or
                (vcheck*dt/src.dx<=cfg.cfl_target*(1+1e-12) and
                 vcheck*dt/cfg.core<=cfg.max_core_shift*(1+1e-12) and
                 ocheck*dt<=cfg.max_vorticity_turn*(1+1e-12)))
            if safe:break
            retries+=1
            dt*=.5
            if retries>12 or dt<cfg.dt_min:
                raise RuntimeError('ADAPTIVE_STEP_REJECT_LIMIT: repeated endpoint shift limit failure')
        vmax=vcheck;omega=ocheck
        # Tracking marker uses reference ONLY, not incoming field.
        w2=ref.probe_u(hr_new,center+dt*w)
        center=(center+dt*.5*(w+w2)+cfg.box/2)%cfg.box-cfg.box/2
        hs,hr=hs_new,hr_new
        en_s=src.global_energy_hat(hs);en_r=ref.global_energy_hat(hr)
        ds=en_s-en_s_before;dr=en_r-en_r_before
        t=min(cfg.final_time,t+dt)
        steps.append({'step':iteration+1,'t':float(t),'dt':dt,'rejected_attempts':retries,'grid':cfg.n,
           'Umax':vmax,'vorticity_max':omega,'max_shift_cells':vmax*dt/src.dx,
           'max_core_sigma_shift':vmax*dt/cfg.core,
           'vorticity_turn_proxy':omega*dt,
           'E_donor_run_J':en_s,'E_control_J':en_r,
           'dE_donor_run_J':ds,'dE_control_J':dr,
           'numerical_loss_donor_J':max(0.,-ds),'numerical_gain_donor_J':max(0.,ds),
           'numerical_loss_control_J':max(0.,-dr),'numerical_gain_control_J':max(0.,dr),
           'drift_donor_relative':(en_s-Es0)/max(abs(Es0),1e-18),
           'drift_control_relative':(en_r-Er0)/max(abs(Er0),1e-18)})
        iteration+=1
        from .heartbeat import advance
        advance(iteration,t,cfg.final_time,dt,retries)
    def assemble(data,provenance,E0,original):
        times=np.array([z['t'] for z in data]);ww=np.array([z['E_window'] for z in data]);
        fl=np.array([z['rhs_flux'] for z in data]);
        res=np.diff(ww)-.5*np.diff(times)*(fl[1:]+fl[:-1]);
        sig=np.array([z['omega_z2_window'] for z in data]);
        peaks,_=find_peaks(sig,prominence=max(1e-14,.015*np.ptp(sig)))
        intervals=np.diff(times[peaks]) if len(peaks)>=3 else np.array([])
        period=float(np.median(intervals)) if len(intervals)>=3 else None
        energy=[z['E_donor_run_J'] if original else z['E_control_J'] for z in steps]
        return {'schema':'A075-EULER3D-ADAPTIVE-3','config':cfg.__dict__,
           'geometry_provenance':provenance,'timeseries':data,'center_track':centers,
           'step_count':iteration,'global_relative_energy_drift':max([abs(e-E0)/max(abs(E0),1e-18) for e in energy]+[0]),
           'max_window_budget_residual_over_E0':float(np.max(np.abs(res))/max(abs(E0),1e-18)) if len(res) else 0.,
           'max_CFL':max((z['max_shift_cells'] for z in steps),default=0.),
           'receiver_peak_count':len(peaks),'receiver_period_s':period,
           'receiver_clock_qualified':False,
           'note':'Adaptive 3D Euler: numerical energy drift is neither physical dissipation nor proof of capture.'}
    return assemble(data_s,ps,Es0,True),assemble(data_r,pr,Er0,False),steps
