"""Finite-width distributed-vorticity 3-D incompressible Euler, periodic spectral cube.

Equation: d_t u = P[ u cross curl(u) + f ], div u=0.
No viscosity, reconnection, line-tension feedback or filament regularizer during evolution.
Initial omega from compact C2 smoothed curve followed by solenoidal spectral projection.
The projected periodic omega is not exactly compactly supported. Periodic images are real
part of the model. Trace marker curve is material, not a reconstructed vortex ridge.
"""
from __future__ import annotations
import math
import numpy as np


class Euler3D:
    def __init__(self,n:int,box:float=6.0,rho:float=1.0):
        if n<16 or n%2: raise ValueError('n must be even and >=16')
        self.n,self.box,self.rho=n,float(box),float(rho)
        self.dx=self.box/n
        self.axis=np.arange(n)*self.dx-self.box/2
        wave=2*np.pi*np.fft.fftfreq(n,d=self.dx)
        self.k=np.array(np.meshgrid(wave,wave,wave,indexing='ij'))
        self.k2=np.sum(self.k*self.k,axis=0)
        self.inv_k2=np.divide(1.,self.k2,out=np.zeros_like(self.k2),where=self.k2>0)
        indices=np.fft.fftfreq(n)*n
        ix,iy,iz=np.meshgrid(indices,indices,indices,indexing='ij')
        self.mask=(np.maximum.reduce([np.abs(ix),np.abs(iy),np.abs(iz)]) < n/3).astype(float)
        self.zero=np.zeros((3,n,n,n),dtype=complex)

    def fft(self,u):return np.fft.fftn(u,axes=(-3,-2,-1))
    def ifft(self,uh):return np.fft.ifftn(uh,axes=(-3,-2,-1)).real
    def project(self,uh):
        ku=np.sum(self.k*uh,axis=0)
        return (uh-self.k*(ku*self.inv_k2)[None,:,:,:])*self.mask[None,:,:,:]
    def curl_hat(self,uh):return 1j*np.cross(self.k,uh,axisa=0,axisb=0,axisc=0)
    def divhat(self,uh):return 1j*np.sum(self.k*uh,axis=0)
    def force(self,amplitude:float):
        # Body force x-direction, shear profile in z; solenoidal and zero box mean.
        # Balanced loads on two half-cells, with explicitly calculable force per half.
        arr=np.zeros((3,self.n,self.n,self.n),dtype=float)
        arr[0]=amplitude*np.sin(2*np.pi*self.axis[None,None,:]/self.box)
        return self.project(self.fft(arr))
    def nominal_half_load(self,amplitude:float)->float:
        return self.rho*float(amplitude)*self.box**3/np.pi
    def omega_initial(self,curve:np.ndarray,core:float,gamma:float=1.0):
        """C2 compact radial kernel (1-r^2/a^2)^3, normalized per line element.

        A line integral of oriented segments is deposited on the grid, then projected
        to eliminate finite-segment discretization divergence. It is an initial finite
        vorticity distribution, not a 1D filament evolution surrogate.
        """
        if core<=0 or core>self.box/6:raise ValueError('invalid core')
        x=np.asarray(curve,dtype=float)
        if x.ndim!=2 or x.shape[1]!=3 or len(x)<16:raise ValueError('curve (N,3) required')
        edge=np.roll(x,-1,axis=0)-x
        mids=x+.5*edge
        omega=np.zeros((3,self.n,self.n,self.n),dtype=float)
        reach=math.ceil(core/self.dx)+1
        off=np.arange(-reach,reach+1)
        for mid,tangent in zip(mids,edge):
            centers=np.mod(np.rint((mid+self.box/2)/self.dx).astype(int),self.n)
            inds=[(centers[j]+off)%self.n for j in range(3)]
            ds=[self.axis[inds[j]]-mid[j] for j in range(3)]
            ds=[(v+self.box/2)%self.box-self.box/2 for v in ds]
            r2=ds[0][:,None,None]**2+ds[1][None,:,None]**2+ds[2][None,None,:]**2
            w=np.maximum(0.,1.-r2/core**2)**3
            wsum=w.sum()*self.dx**3
            if wsum<=0:raise RuntimeError('core subgrid deposition')
            w=w/wsum
            ix=np.ix_(*inds)
            for c in range(3):omega[c][ix]+=gamma*tangent[c]*w
        wh=self.project(self.fft(omega))
        uh=1j*np.cross(self.k,wh,axisa=0,axisb=0,axisc=0)*self.inv_k2[None,:,:,:]
        return self.project(uh)

    def rhs(self,uh,fh=None,form='rotational'):
        u=self.ifft(uh)
        if form=='rotational':
            omega=self.ifft(self.curl_hat(uh))
            nonlinear=np.cross(u,omega,axisa=0,axisb=0,axisc=0)
        elif form=='convective':
            nonlinear=np.zeros_like(u)
            for j in range(3):
                deriv=self.ifft(1j*self.k[j][None]*uh)
                nonlinear-=u[j][None]*deriv
        else:raise ValueError('unknown form')
        nonlinear_hat=self.fft(nonlinear)
        if fh is not None:nonlinear_hat+=fh
        return self.project(nonlinear_hat)

    def timestep(self,uh,dt,fh=None,form='rotational'):
        k1=self.rhs(uh,fh,form)
        k2=self.rhs(self.project(uh+dt*.5*k1),fh,form)
        k3=self.rhs(self.project(uh+dt*.5*k2),fh,form)
        k4=self.rhs(self.project(uh+dt*k3),fh,form)
        return self.project(uh+dt*(k1+2*k2+2*k3+k4)/6)

    def sample(self,u,x):
        # periodic trilinear sampling of 3-vector at M locations
        pos=np.mod((np.asarray(x)+self.box/2)/self.dx,self.n)
        lower=np.floor(pos).astype(int);frac=pos-lower
        ans=np.zeros((len(pos),3),dtype=float)
        for i in (0,1):
            wx=frac[:,0] if i else (1-frac[:,0])
            for j in (0,1):
                wy=frac[:,1] if j else (1-frac[:,1])
                for k in (0,1):
                    wz=frac[:,2] if k else (1-frac[:,2])
                    ii=(lower[:,0]+i)%self.n
                    jj=(lower[:,1]+j)%self.n
                    kk=(lower[:,2]+k)%self.n
                    ans+=(wx*wy*wz)[:,None]*u[:,ii,jj,kk].T
        return ans
    def tracer_step(self,uh,x,dt,fh=None):
        # diagnostic advection with RK2 and time-interpolated Euler field
        u=self.ifft(uh)
        v1=self.sample(u,x)
        umid=self.ifft(self.project(uh+.5*dt*self.rhs(uh,fh)))
        v2=self.sample(umid,x+.5*dt*v1)
        return x+dt*v2

    def pressure_report(self,uh,fh=None):
        # canonical pressure Poisson from independently computed advective form
        u=self.ifft(uh)
        conv=np.zeros_like(u)
        grad=np.empty((3,3,self.n,self.n,self.n),dtype=float)
        for j in range(3):
            d=self.ifft(1j*self.k[j][None]*uh)
            for i in range(3):grad[i,j]=d[i]
            conv+=u[j][None]*d
        ch=self.fft(conv)*self.mask
        if fh is None: fh=self.zero
        p_hat=(self.rho*1j*np.sum(self.k*(ch-fh),axis=0)*self.inv_k2)*self.mask
        p=self.ifft(p_hat)
        # independent pointwise gradient-source pressure Poisson check with spectral filter
        grad_source=np.zeros((self.n,self.n,self.n))
        for i in range(3):
            for j in range(3):grad_source+=grad[i,j]*grad[j,i]
        src_hat=-self.rho*self.fft(grad_source)*self.mask
        residual=-self.k2*p_hat-src_hat
        weighted=np.linalg.norm(residual.ravel())/max(np.linalg.norm(src_hat.ravel()),1e-30)
        div_rel=np.linalg.norm(self.divhat(uh).ravel())/max(np.linalg.norm((self.k*uh).ravel()),1e-30)
        return dict(poisson_relative_residual=float(weighted),divergence_relative_residual=float(div_rel),
                    pressure_rms_Pa=float(np.sqrt(np.mean(p*p))), pressure_mean_Pa=float(p.mean()))

    def diagnostics(self,uh):
        u=self.ifft(uh);omega=self.ifft(self.curl_hat(uh))
        vol=self.box**3
        E=.5*self.rho*float(np.mean(np.sum(u*u,axis=0)))*vol
        enstrophy=.5*float(np.mean(np.sum(omega*omega,axis=0)))*vol
        helicity=float(np.mean(np.sum(u*omega,axis=0)))*vol
        vmax=float(np.max(np.sqrt(np.sum(u*u,axis=0))))
        return dict(energy_J=E,enstrophy_m3_s2=enstrophy,helicity_m4_s2=helicity,
                    velocity_max_m_s=vmax,cfl_velocity=vmax*self.dx**-1)

    def momentum_flux(self,uh):
        # x-momentum transported across z=0 (stress sigma_xz=rho*u_x*u_z).
        u=self.ifft(uh)
        iz=self.n//2
        sigma=self.rho*u[0,:,:,iz]*u[2,:,:,iz]
        return float(np.mean(sigma)*self.box**2)
