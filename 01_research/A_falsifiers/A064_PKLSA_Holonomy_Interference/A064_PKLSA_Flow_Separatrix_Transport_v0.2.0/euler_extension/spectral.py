"""Dimensionless, periodic, de-aliased 3-D incompressible Euler model.

Scientific boundary: a modeled periodic Euler solution seeded from a raw 3D
PKLSA centerline. It is not measured flow, not an E011 DYNAMICS_READY state,
and not a certified stability result.
"""
import numpy as np
from scipy.spatial import cKDTree

class SpectralEuler3D:
    def __init__(self, n, box=2*np.pi):
        if n<16 or n%2:raise ValueError('n must be even and >=16')
        self.n=n; self.box=float(box); self.dx=box/n
        a=np.fft.fftfreq(n,d=self.dx)*2*np.pi
        self.k=np.meshgrid(a,a,a,indexing='ij')
        kk=sum(ki*ki for ki in self.k)
        self.inv_k2=np.where(kk>0,1/np.where(kk>0,kk,1),0)
        mode=np.fft.fftfreq(n)*n
        # Strict 2/3 truncation for product de-aliasing
        self.mask=np.logical_and.reduce([np.abs(x)<n/3 for x in np.meshgrid(mode,mode,mode,indexing='ij')])
        self.mask[0,0,0]=False
    def fft(self,v):return np.fft.fftn(v,axes=(0,1,2))
    def ifft(self,v):return np.fft.ifftn(v,axes=(0,1,2)).real
    def project_hat(self,uh):
        dot=sum(self.k[j]*uh[...,j] for j in range(3))*self.inv_k2
        return np.stack([(uh[...,j]-self.k[j]*dot)*self.mask for j in range(3)],axis=-1)
    def proj(self,u):return self.ifft(self.project_hat(self.fft(u)))
    def curl(self,u):
        uh=self.fft(u)
        return self.ifft(1j*np.stack([
            self.k[1]*uh[...,2]-self.k[2]*uh[...,1],
            self.k[2]*uh[...,0]-self.k[0]*uh[...,2],
            self.k[0]*uh[...,1]-self.k[1]*uh[...,0]],axis=-1))
    def velocity_from_vorticity(self,w):
        wh=self.project_hat(self.fft(w))
        uhat=1j*np.stack([
            self.k[1]*wh[...,2]-self.k[2]*wh[...,1],
            self.k[2]*wh[...,0]-self.k[0]*wh[...,2],
            self.k[0]*wh[...,1]-self.k[1]*wh[...,0]],axis=-1)*self.inv_k2[...,None]
        return self.ifft(self.project_hat(uhat))
    def rhs(self,u):
        omega=self.curl(u)
        # Euler: du/dt = P(u cross omega); gradient is eliminated by P
        return self.proj(np.cross(u,omega))
    def rk4(self,u,dt):
        k1=self.rhs(u);k2=self.rhs(u+.5*dt*k1)
        k3=self.rhs(u+.5*dt*k2);k4=self.rhs(u+dt*k3)
        return self.proj(u+(dt/6)*(k1+2*k2+2*k3+k4))
    def diagnostics(self,u):
        w=self.curl(u)
        uh=self.fft(u)
        d=1j*sum(self.k[j]*uh[...,j] for j in range(3))
        div=np.max(np.abs(self.ifft(d)))
        en=.5*np.mean(np.sum(u*u,axis=-1))
        he=np.mean(np.sum(u*w,axis=-1))
        w2=np.mean(np.sum(w*w,axis=-1))
        umax=np.max(np.linalg.norm(u,axis=-1))
        return {'energy_density_dimensionless':float(en),'helicity_density_dimensionless':float(he),
                'enstrophy_density_dimensionless':float(w2),
                'divergence_max_dimensionless':float(div),
                'umax_dimensionless':float(umax)}

def init_knotted_tube(solver,xyz,core=0.58,target_rms=1.,span=2.6):
    """Periodic Gaussian tube with closed centerline line-elements and divergence-free projection.

    Coordinates are intrinsically uncalibrated; rescale to a fixed bounded box.
    """
    pts=np.asarray(xyz,float)
    if pts.ndim!=2 or pts.shape[1]!=3 or len(pts)<20:raise ValueError('invalid polygon')
    raw_span=float(np.ptp(pts,axis=0).max())
    if not np.isfinite(raw_span) or raw_span<=0:raise ValueError('invalid extent')
    normed=(pts-pts.mean(axis=0))*span/raw_span
    # each segment contributes a tangent-vorticity line element; kernel periodic
    ds=np.roll(normed,-1,axis=0)-normed
    mids=(normed+np.roll(normed,-1,axis=0))/2
    axes=(np.arange(solver.n)-solver.n//2)*solver.dx
    coords=np.stack(np.meshgrid(axes,axes,axes,indexing='ij'),axis=-1)
    w=np.zeros((*coords.shape[:3],3),float)
    for j in range(0,len(mids),8):
        diff=coords[...,None,:]-mids[j:j+8]
        diff=(diff+solver.box/2)%solver.box-solver.box/2
        radius2=np.einsum('...i,...i->...',diff,diff)
        weights=np.exp(-.5*radius2/core**2)/(2*np.pi*core**2)**1.5
        w+=np.einsum('...s,si->...i',weights,ds[j:j+8])
    u=solver.velocity_from_vorticity(w)
    rms=float(np.sqrt(np.mean(np.sum(u*u,axis=-1))))
    if rms<1e-12:raise ValueError('degenerate initialized knotted flow')
    return u*(target_rms/rms),{'source_coordinate_span':raw_span,'centerline_extent_in_box':span,'gaussian_core_width':core,
                        'target_rms':target_rms,'periodic_box':solver.box,'source_point_count':len(pts),
                        'resolution_over_core':core/solver.dx}

def evolve(solver,u0,duration=.36,frame_count=4,cfl_limit=.16,max_steps=200):
    if duration<=0 or frame_count<3 or cfl_limit<=0:raise ValueError('bad evolution configuration')
    times=np.linspace(0,duration,frame_count)
    frames=[u0.copy()];logs=[dict(t=0.,**solver.diagnostics(u0))]
    u=u0.copy();t=0.;steps=0;worst_cfl=0.
    for target in times[1:]:
        while target-t>1e-12:
            umax=solver.diagnostics(u)['umax_dimensionless']
            dt=min(target-t,cfl_limit*solver.dx/max(umax,1e-12))
            if steps>=max_steps:raise RuntimeError('max Euler RK4 steps exceeded')
            u=solver.rk4(u,dt)
            if not np.all(np.isfinite(u)):raise FloatingPointError('nonfinite Euler state')
            worst_cfl=max(worst_cfl,umax*dt/solver.dx)
            t+=dt;steps+=1
        frames.append(u.copy());logs.append(dict(t=float(target),**solver.diagnostics(u)))
    e0=logs[0]['energy_density_dimensionless'];h0=logs[0]['helicity_density_dimensionless']
    energy_drift=max(abs(log['energy_density_dimensionless']-e0)/max(e0,1e-20) for log in logs)
    he_scale=max(abs(h0),max(abs(x['helicity_density_dimensionless']) for x in logs),1e-12)
    helicity_drift=max(abs(log['helicity_density_dimensionless']-h0)/he_scale for log in logs)
    return times,np.stack(frames),{'n_steps':steps,'max_cfl':worst_cfl,'max_energy_rel_drift':energy_drift,
        'max_helicity_rel_drift':helicity_drift,'max_divergence':max(x['divergence_max_dimensionless'] for x in logs),
        'per_frame':logs}
