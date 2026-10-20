"""Unforced incompressible Euler plus tangent-linear dynamics on a periodic 3D grid.

This is a DIMENSIONLESS, dealiased Fourier-Galerkin numerical model (not a
physical SST phase gauge model). The signed phase is extracted only from a
fixed, documented complex receiver projection of the *computed* perturbation.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter

L = 2 * np.pi


def load_geometry(path):
    raw = Path(path).read_text(encoding='utf8')
    components, current = [], []
    for line in raw.splitlines() + ['']:
        s = line.strip()
        if not s:
            if current:
                components.append(np.asarray(current, dtype=float)); current=[]
            continue
        v = [float(t) for t in s.split()]
        if len(v) != 3 or not np.all(np.isfinite(v)):
            raise ValueError(f'Malformed XYZ in {path}')
        current.append(v)
    if not components or any(len(c) < 5 for c in components):
        raise ValueError('Insufficient closed-curve points')
    return components, hashlib.sha256(raw.encode()).hexdigest()


def normalized_components(comps):
    allpoints = np.concatenate(comps)
    center = allpoints.mean(0)
    max_radius = np.max(np.linalg.norm(allpoints-center, axis=1))
    scale = 1.82 / max_radius
    return [((c-center)*scale + L/2) % L for c in comps], float(scale)


class Euler3D:
    def __init__(self, n=24, core=0.40):
        self.n = int(n); self.core=float(core); self.dx=L/self.n
        k=np.fft.fftfreq(n, d=1.0/n).astype(float)
        self.k=np.asarray(np.meshgrid(k,k,k,indexing='ij'))
        self.k2=np.sum(self.k**2,axis=0)
        self.inv_k2=np.zeros_like(self.k2)
        self.inv_k2[self.k2>0]=1/self.k2[self.k2>0]
        cutoff=n//3
        self.mask=np.all(np.abs(self.k)<=cutoff, axis=0)
        self.mask[0,0,0]=False
        x=(np.arange(n)+0.5)*self.dx
        self.coords=np.asarray(np.meshgrid(x,x,x,indexing='ij'))

    def fft(self,x):return np.fft.fftn(x,axes=(-3,-2,-1))
    def ifft(self,x):return np.fft.ifftn(x,axes=(-3,-2,-1)).real

    def curl(self,u):
        f=self.fft(u)
        k=self.k
        o=np.stack([1j*(k[1]*f[2]-k[2]*f[1]), 1j*(k[2]*f[0]-k[0]*f[2]), 1j*(k[0]*f[1]-k[1]*f[0])])
        return self.ifft(o)

    def project(self,u):
        f=self.fft(u)*self.mask
        longitudinal=np.sum(self.k*f,axis=0)*self.inv_k2
        f=f-self.k*longitudinal
        f*=self.mask
        return self.ifft(f)

    def velocity_from_curve(self, curves, gamma=1.0):
        # Deposit the signed line current with cloud-in-cell on the periodic grid.
        w=np.zeros((3,self.n,self.n,self.n),dtype=float)
        for c in curves:
            edges=np.roll(c,-1,axis=0)-c
            edges=(edges+L/2)%L-L/2
            seg_norm=np.linalg.norm(edges,axis=1)
            if not np.all(seg_norm>1e-8):raise ValueError('Degenerate segment')
            for pt,e,d in zip(c,edges,seg_norm):
                subdivisions=max(1,int(np.ceil(d/(self.dx*0.35))))
                for q in range(subdivisions):
                    pos=(pt+(q+0.5)/subdivisions*e)%L
                    cell=pos/self.dx-0.5
                    lower=np.floor(cell).astype(int); frac=cell-lower
                    for a in (0,1):
                        for b in (0,1):
                            for cc in (0,1):
                                weights=np.array([frac[0] if a else 1-frac[0],frac[1] if b else 1-frac[1],frac[2] if cc else 1-frac[2]])
                                ix=(lower+np.array([a,b,cc]))%self.n
                                w[:,ix[0],ix[1],ix[2]]+=gamma*e/subdivisions*np.prod(weights)/self.dx**3
        w=gaussian_filter(w,sigma=(0,self.core/self.dx,self.core/self.dx,self.core/self.dx),mode='wrap')
        wf=self.fft(w)*self.mask
        k=self.k
        vf=1j*np.stack([k[1]*wf[2]-k[2]*wf[1],k[2]*wf[0]-k[0]*wf[2],k[0]*wf[1]-k[1]*wf[0]])*self.inv_k2
        return self.project(self.ifft(vf))

    def local_source(self,center,orientation=None,width=0.43):
        # Curl of localized smooth vector potential: transverse, div-free impulse.
        if orientation is None:orientation=np.array([1.,0.,0.])
        d=(self.coords-center[:,None,None,None]+L/2)%L-L/2
        env=np.exp(-np.sum(d*d,axis=0)/(2*width**2))
        A=orientation[:,None,None,None]*env
        pulse=self.project(self.curl(A))
        norm=np.sqrt(np.mean(np.sum(pulse**2,axis=0)))
        if norm < 1e-12:raise ValueError('Local excitation norm underflow')
        return pulse/norm

    def cross(self,a,b):
        return np.stack((a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]))

    def rhs(self,U,D):
        # Unforced incompressible Euler in Lamb form; exact tangent derivative.
        vort=self.curl(U)
        dU=self.project(self.cross(U,vort))
        dD=(np.stack([self.project(self.cross(d,vort)+self.cross(U,self.curl(d))) for d in D]) if len(D) else D.copy())
        return dU,dD

    def rk4(self,U,D,dt):
        k1,l1=self.rhs(U,D)
        k2,l2=self.rhs(U+dt*k1/2,D+dt*l1/2)
        k3,l3=self.rhs(U+dt*k2/2,D+dt*l2/2)
        k4,l4=self.rhs(U+dt*k3,D+dt*l3)
        U=self.project(U+dt*(k1+2*k2+2*k3+k4)/6)
        D=(np.stack([self.project(d) for d in D+dt*(l1+2*l2+2*l3+l4)/6]) if len(D) else D.copy())
        return U,D

    def divergence_relative(self,U):
        F=self.fft(U)
        div=self.ifft(1j*np.sum(self.k*F,axis=0))
        return float(np.sqrt(np.mean(div**2))/(np.sqrt(np.mean(np.sum(U**2,axis=0)))+1e-30))


def _wrap_dist(g,x):
    d=(g.coords-x[:,None,None,None]+L/2)%L-L/2
    return np.sum(d*d,axis=0)


def initial_condition(grid, geom):
    curves,scale=normalized_components(geom)
    U=grid.velocity_from_curve(curves)
    # Physical perturbation sources are placed at separated positions along the
    # *same* registered component. They are not assumed to represent two AB arms.
    c=curves[0]
    srcA=c[int(0.12*len(c))]
    srcB=c[int(0.57*len(c))]
    detector=c[int(0.34*len(c))]
    DA=grid.local_source(srcA, np.array([0.,0.,1.]))
    DB=grid.local_source(srcB, np.array([1.,0.,0.]))
    # Two pre-fixed receiver quadratures, defined independently of the evolution.
    R1=grid.local_source(detector,np.array([0.,0.,1.]),width=0.65)
    R2=grid.local_source(detector,np.array([1.,0.,0.]),width=0.65)
    # Gram-Schmidt in the Hilbert space of solenoidal fields.
    R2=R2-np.mean(np.sum(R2*R1,axis=0))*R1
    R2/=np.sqrt(np.mean(np.sum(R2**2,axis=0)))
    detector_weight=np.exp(-_wrap_dist(grid,detector)/(2*0.8**2))
    return U,np.stack((DA,DB)),(R1,R2),detector_weight,scale


def observe(grid,U,D,rec,weight):
    I=np.asarray([np.mean(weight*np.sum(d*d,axis=0)) for d in D])
    Iab=float(np.mean(weight*np.sum((D[0]+D[1])**2,axis=0)))
    Z=[]
    for d in D:
        Z.append(complex(np.mean(np.sum(d*rec[0],axis=0)),np.mean(np.sum(d*rec[1],axis=0))))
    return dict(base_energy=float(np.mean(np.sum(U*U,axis=0))/2),
                I_A=float(I[0]),I_B=float(I[1]),I_AB=Iab,
                delta_I=float(Iab-I.sum()),
                interference_fraction=float((Iab-I.sum())/(I.sum()+1e-30)),
                z_A_re=Z[0].real,z_A_im=Z[0].imag,
                z_B_re=Z[1].real,z_B_im=Z[1].imag,
                div_base=grid.divergence_relative(U))


def run_case(path, n=24,core=0.4,steps=80,dt=.018, retain_fields=False):
    geom,digest=load_geometry(path)
    grid=Euler3D(n,core)
    U,D,receiver,weight,scale=initial_condition(grid,geom)
    speed=float(np.sqrt(np.mean(np.sum(U*U,axis=0))))
    out=[]
    for i in range(steps+1):
        o=observe(grid,U,D,receiver,weight)
        o['t']=float(i*dt)
        out.append(o)
        if i<steps:U,D=grid.rk4(U,D,dt)
    import pandas as pd
    F=pd.DataFrame(out)
    for key in ('A','B'):
        z=F[f'z_{key}_re'].to_numpy()+1j*F[f'z_{key}_im'].to_numpy()
        amp=np.abs(z)
        # If projection is too small, phase is undefined, fail qualification.
        threshold=max(1e-10,1e-4*float(np.max(amp)))
        angle=np.unwrap(np.angle(z))
        F[f'phase_{key}']=np.where(amp>=threshold,angle,np.nan)
        F[f'phase_omega_{key}']=np.gradient(angle,dt)
        F[f'phase_amplitude_{key}']=amp
    ca=F.z_A_re.to_numpy()+1j*F.z_A_im.to_numpy()
    cb=F.z_B_re.to_numpy()+1j*F.z_B_im.to_numpy()
    F['receiver_phase_difference']=np.angle(ca*np.conj(cb))
    desc={
        'label':Path(path).stem,'input_sha256':digest,'n':int(n),'core_dimless':float(core),
        'dt_dimless':float(dt),'steps':int(steps),'T_dimless':float(dt*steps),
        'native_to_grid_scale_arbitrary':scale,'circulation_dimensionless':1.,
        'velocity_rms_initial_dimless':speed,
        'base_energy_rel_drift':float((F.base_energy.iloc[-1]-F.base_energy.iloc[0])/(F.base_energy.iloc[0]+1e-30)),
        'max_divergence_relative':float(F.div_base.max()),
        'initial_delta_I':float(F.delta_I.iloc[0]),'final_delta_I':float(F.delta_I.iloc[-1]),
        'max_abs_interference_fraction':float(np.max(np.abs(F.interference_fraction))),
        'phase_A_change_rad':float(F.phase_A.iloc[-1]-F.phase_A.iloc[0]),
        'phase_B_change_rad':float(F.phase_B.iloc[-1]-F.phase_B.iloc[0]),
        'max_receiver_phase_difference_rad':float(np.max(np.abs(F.receiver_phase_difference))),
        'phase_A_min_amp':float(F.phase_amplitude_A.min()),
        'phase_B_min_amp':float(F.phase_amplitude_B.min()),
        'phase_A_max_amp':float(F.phase_amplitude_A.max()),
        'phase_B_max_amp':float(F.phase_amplitude_B.max()),
        'status_note':'DIMENSIONLESS Euler-Galerkin tangent response; no AB/quantum gauge claim'
    }
    if retain_fields:return F,desc,(U,D)
    return F,desc
