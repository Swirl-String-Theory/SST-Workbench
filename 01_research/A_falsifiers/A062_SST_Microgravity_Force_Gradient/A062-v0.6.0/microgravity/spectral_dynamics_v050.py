"""A062-v0.6.0 - genuine 3D periodic incompressible Euler/Navier--Stokes
pseudo-spectral *short-time screening*, initialized from source-pinned E011 tubes.

A periodically continued Gaussian tube is an initial condition, not a stationary
solution or isolated physical SST knot. Fourier 2/3 de-aliasing, orthogonal
Helmholtz projection and RK4 integrate the *velocity* equation in Lamb form.
No full-space gravity is inferred from periodic, nonzero-mean kinetic energy.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np

@dataclass
class SpectralBox:
    n: int
    length: float=1.2
    def __post_init__(self):
        n=self.n; L=self.length
        q=2*np.pi*np.fft.fftfreq(n,d=L/n)
        self.kx,self.ky,self.kz=np.meshgrid(q,q,q,indexing='ij')
        self.k=(self.kx,self.ky,self.kz)
        self.k2=self.kx**2+self.ky**2+self.kz**2
        self.nonzero=self.k2>0
        self.denom=np.where(self.nonzero,self.k2,1)
        # strictly 2/3 cutoff (Nyquist and 1/3 edge removed)
        modes=np.fft.fftfreq(n)*n
        mx,my,mz=np.meshgrid(modes,modes,modes,indexing='ij')
        self.mask=(abs(mx)<n/3)&(abs(my)<n/3)&(abs(mz)<n/3)
        self.grid=np.stack(np.meshgrid(*([np.arange(n)*L/n-L/2]*3),indexing='ij'),axis=-1)

    @staticmethod
    def fft(u):return np.fft.fftn(u,axes=(-3,-2,-1))
    @staticmethod
    def ifft(a):return np.fft.ifftn(a,axes=(-3,-2,-1)).real

    def project(self,uh):
        u=np.stack(uh).copy()
        kd=self.kx*u[0]+self.ky*u[1]+self.kz*u[2]
        for j in range(3):u[j]-=self.k[j]*kd/self.denom
        u[:,~self.nonzero]=0
        u*=self.mask[None,:,:,:]
        return u

    def curl(self,uh):
        kx,ky,kz=self.k
        return 1j*np.stack((ky*uh[2]-kz*uh[1],kz*uh[0]-kx*uh[2],kx*uh[1]-ky*uh[0]))

    def velocity_from_vorticity(self,wh):
        kx,ky,kz=self.k
        return self.project(1j*np.stack((ky*wh[2]-kz*wh[1],kz*wh[0]-kx*wh[2],kx*wh[1]-ky*wh[0]))/self.denom)

    def rhs(self,uh,nu):
        v=self.ifft(uh)
        w=self.ifft(self.curl(uh))
        lamb=np.cross(v,w,axisa=0,axisb=0,axisc=0)
        out=self.project(self.fft(lamb))
        return out - nu*self.k2[None,:,:,:]*uh

    def step(self,uh,dt,nu):
        k1=self.rhs(uh,nu)
        k2=self.rhs(uh+dt*k1/2,nu)
        k3=self.rhs(uh+dt*k2/2,nu)
        k4=self.rhs(uh+dt*k3,nu)
        return self.project(uh+(dt/6)*(k1+2*k2+2*k3+k4))

    def diagnostics(self,uh):
        u=self.ifft(uh)
        w=self.ifft(self.curl(uh))
        div=self.ifft(1j*(self.kx*uh[0]+self.ky*uh[1]+self.kz*uh[2]))
        vol=self.length**3
        energy=float(.5*vol*np.mean(np.sum(u*u,axis=0)))
        diss=float(vol*np.mean(np.sum(w*w,axis=0)))
        helicity=float(vol*np.mean(np.sum(u*w,axis=0)))
        return dict(E=energy,omega2_integral=diss,helicity=helicity,
            div_L2=float(np.sqrt(np.mean(div*div))),u_rms=float(np.sqrt(np.mean(np.sum(u*u,axis=0)))))

    def initial_tube(self,curve,a,segments=96):
        """Finite Gaussian vorticity from tangent-directed closed polygon; periodic sum
        is negligible at the chosen large box and documented as approximation.
        Spectral projection enforces divergence-free representation after discretization.
        """
        n=len(curve)
        idx=np.linspace(0,n,segments+1,dtype=int)[:-1]
        x=curve[idx]
        d=np.roll(x,-1,axis=0)-x
        mid=x+d/2
        # exact periodic image tails are tiny since x-centered tube fits in cell
        scale=(2*np.pi*a*a)**(-1.5)
        omega=np.zeros((3,self.n,self.n,self.n),dtype=np.float64)
        # midpoint quadrature of tube line integral; no topology claim after evolution
        for pt,edge in zip(mid,d):
            rr=self.grid-pt
            rr-=self.length*np.round(rr/self.length)
            G=np.exp(-np.einsum('...i,...i->...',rr,rr)/(2*a*a))*scale
            omega+=edge[:,None,None,None]*G[None,:,:,:]
        wraw=self.fft(omega)
        uh=self.velocity_from_vorticity(wraw)
        # Representation residual measured after spectral cutoff and Helmholtz projection
        wrec=self.curl(uh)
        denom=np.linalg.norm(wraw.ravel())
        residual=float(np.linalg.norm((wraw-wrec).ravel())/max(denom,1e-300))
        return uh,{'raw_to_projected_vorticity_rel_L2':residual,
                   'gaussian_width':a,'box_size':self.length,'quadrature_segments':len(idx)}


def test_abc_decay(n=24,nu=.01,T=.25,dt=.025):
    """Exact Beltrami ABC field: curl(u)=u, nonlinear Lamb term zero,
    NS exact e^{-nu*t} (in 2pi periodic box)."""
    box=SpectralBox(n,2*np.pi)
    x,y,z=np.moveaxis(box.grid+np.pi,-1,0)
    u=np.stack((np.sin(z)+np.cos(y),np.sin(x)+np.cos(z),np.sin(y)+np.cos(x)))
    a=box.project(box.fft(u))
    target=a*np.exp(-nu*T)
    for _ in range(round(T/dt)):a=box.step(a,dt,nu)
    err=float(np.linalg.norm((a-target).ravel())/np.linalg.norm(target.ravel()))
    return {'relative_velocity_error':err,'nu':nu,'T':T,'n':n}


def integrate_e011(curve,n,nu,T=.009,dt=.0009,L=1.2,a=.11):
    box=SpectralBox(n,L)
    uh,source=box.initial_tube(curve,a)
    d0=box.diagnostics(uh)
    records=[{'t':0.,**d0}]
    nstep=int(round(T/dt))
    assert np.isclose(nstep*dt,T)
    for step in range(1,nstep+1):
        uh=box.step(uh,dt,nu)
        if not np.isfinite(uh).all():raise FloatingPointError('Nonfinite Fourier velocity')
        records.append({'t':step*dt,**box.diagnostics(uh)})
    d1=records[-1]
    diss_trap=sum((records[i-1]['omega2_integral']+records[i]['omega2_integral'])*dt/2 for i in range(1,len(records)))
    predicted=-nu*diss_trap
    delta=d1['E']-d0['E']
    # normalized to dissipated amount when nu>0, else relative to initial energy
    den=max(abs(predicted),d0['E']*1e-5)
    energy_budget_err=float(abs(delta-predicted)/den)
    div_rel=max(z['div_L2'] for z in records)/max(d0['u_rms']/L,1e-100)
    return {'n':n,'nu':nu,'T':T,'dt':dt,'initial_projection':source,
           'initial':d0,'last':d1,'energy_relative_drift':float(delta/d0['E']),
           'energy_balance_error':energy_budget_err,'div_relative_max':div_rel,
           'integrated_omega_squared':diss_trap,'record':records}


def periodic_stress_monopole(curve,n=24):
    box=SpectralBox(n,1.2)
    uh,_=box.initial_tube(curve,.11)
    u=box.ifft(uh)
    # S_C(k)=-k_i k_j FFT(u_i u_j), no fitting lambda.
    charge_k=np.zeros((n,n,n),dtype=np.complex128)
    for i in range(3):
        for j in range(3):
            charge_k-=box.k[i]*box.k[j]*np.fft.fftn(u[i]*u[j])
    charge=np.fft.ifftn(charge_k).real
    return {'source_mean':float(np.mean(charge)),
            'source_integral':float(np.mean(charge)*box.length**3),
            'L2_source':float(np.sqrt(np.mean(charge*charge))),
            'k_zero':float(abs(charge_k[0,0,0])),
            'poisson_periodic_nonzero_monopole_allowed':False}
