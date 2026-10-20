"""Small periodic, unforced, inviscid Euler pseudo-spectral screening pilot.

Builds a smooth divergence-free vortex tube from a polygonal knot; computes
RK4 Euler on a periodic cube and advects material centerline markers. Dimensionless
source geometry is box-normalized: this is NOT a calibrated SST physical prediction,
NOT a converged stability/reconnection study, and NOT native framework qualification.
"""
from __future__ import annotations
import math
from pathlib import Path
import numpy as np
from .topology3d import knot_signature
from .physics import static_geometry

class EulerBox:
    def __init__(self,n):
        self.n=n;self.h=2*np.pi/n
        k=np.fft.fftfreq(n,d=1/n)
        self.K=np.stack(np.broadcast_arrays(k[:,None,None],k[None,:,None],k[None,None,:]),axis=-1)
        self.K2=(self.K*self.K).sum(-1)
        self.invK2=np.divide(1.,self.K2,out=np.zeros_like(self.K2),where=self.K2!=0)
        self.dealias=np.max(np.abs(self.K),axis=-1)<n/3
        gx=np.arange(n)*self.h
        self.grid=np.stack(np.broadcast_arrays(gx[:,None,None],gx[None,:,None],gx[None,None,:]),axis=-1)
    def fft(self,a):return np.fft.fftn(a,axes=(0,1,2))
    def ifft(self,a):return np.fft.ifftn(a,axes=(0,1,2)).real
    def project(self,fh):
        fh=fh - self.K*np.sum(self.K*fh,axis=-1)[...,None]*self.invK2[...,None]
        fh[0,0,0]=0
        return fh*self.dealias[...,None]
    def velocity_from_vorticity(self,omega):
        wh=self.project(self.fft(omega))
        return self.ifft(self.project(1j*np.cross(self.K,wh)*self.invK2[...,None]))
    def curl(self,uh):return self.ifft(1j*np.cross(self.K,uh))
    def rhs(self,uh):
        u=self.ifft(uh);w=self.curl(uh)
        return self.project(self.fft(np.cross(u,w)))
    def sample(self,u,points):
        # Periodic trilinear interpolation; no scipy dependency.
        xp=(np.asarray(points)%(2*np.pi))/self.h
        i0=np.floor(xp).astype(int)%self.n
        d=xp-np.floor(xp)
        value=np.zeros_like(points,dtype=float)
        for a in (0,1):
            wa=(1-d[...,0]) if a==0 else d[...,0]
            for b in (0,1):
                wb=(1-d[...,1]) if b==0 else d[...,1]
                for c in (0,1):
                    wc=(1-d[...,2]) if c==0 else d[...,2]
                    ix=(i0[...,0]+a)%self.n;iy=(i0[...,1]+b)%self.n;iz=(i0[...,2]+c)%self.n
                    value+=((wa*wb*wc)[...,None])*u[ix,iy,iz]
        return value
    def step(self,uh,pts,dt):
        k1=self.rhs(uh);v1=self.sample(self.ifft(uh),pts)
        u2=uh+dt*k1/2;k2=self.rhs(u2);v2=self.sample(self.ifft(u2),pts+dt*v1/2)
        u3=uh+dt*k2/2;k3=self.rhs(u3);v3=self.sample(self.ifft(u3),pts+dt*v2/2)
        u4=uh+dt*k3;k4=self.rhs(u4);v4=self.sample(self.ifft(u4),pts+dt*v3)
        un=self.project(uh+dt*(k1+2*k2+2*k3+k4)/6)
        xn=(pts+dt*(v1+2*v2+2*v3+v4)/6)%(2*np.pi)
        return un,xn

def normalize_curve(p):
    p=np.asarray(p,dtype=float)
    if p.ndim!=2 or p.shape[1]!=3 or not np.isfinite(p).all() or len(p)<32:
        raise ValueError('expected finite Nx3 input')
    w=p-p.mean(axis=0)
    scale=1.75/max(np.max(abs(w)),1e-30)
    return w*scale+np.pi,{'source_center':p.mean(axis=0).tolist(),'source_to_box_factor':float(scale),
       'conversion':'DIMENSIONLESS; physical length scale not calibrated'}

def tube_omega(box,curve,sigma):
    out=np.zeros((box.n,box.n,box.n,3),dtype=float)
    n=len(curve)
    normalizer=1/((2*np.pi)**1.5*sigma**3)
    for i in range(n):
        d=curve[(i+1)%n]-curve[i]
        # Do not use wrapped segment tangents across periodic boundary; initial curve is central.
        midpoint=(curve[i]+curve[(i+1)%n])/2
        r=(box.grid-midpoint+np.pi)%(2*np.pi)-np.pi
        weights=np.exp(-np.sum(r*r,axis=-1)/(2*sigma**2))*normalizer
        out+=weights[...,None]*d
    return out

def run_pilot(curve,grid=24,steps=4,cfl=0.1,duration_model=None,sigma_model=None):
    p,transform=normalize_curve(curve)
    B=EulerBox(grid)
    sigma=float(sigma_model) if sigma_model is not None else max(1.8*B.h,0.22)
    if sigma<=0:raise ValueError("sigma_model must be positive")
    omega=tube_omega(B,p,sigma=sigma)
    u=B.velocity_from_vorticity(omega)
    uh=B.project(B.fft(u))
    umax=float(np.linalg.norm(u,axis=-1).max())
    if umax<1e-12:raise RuntimeError('Zero initial velocity')
    dt=cfl*B.h/umax
    if duration_model is not None:
        proposed=float(duration_model)/steps
        if proposed>dt:raise ValueError(f"Required fixed-time step {proposed} exceeds CFL cap {dt}; raise steps")
        dt=proposed
    times=[];curves=[];fields=[];sampled_vel=[];energies=[];hel=[]
    material=p.copy()
    for i in range(steps+1):
        uv=B.ifft(uh);w=B.curl(uh)
        times.append(i*dt);curves.append(material.copy());fields.append(uv.copy())
        sampled_vel.append(B.sample(uv,material))
        energies.append(float(0.5*np.mean(np.sum(uv*uv,axis=-1))))
        hel.append(float(np.mean(np.sum(uv*w,axis=-1))))
        if i<steps:uh,material=B.step(uh,material,dt)
    # Diagnose with the same spectral differentiation and dealiasing as the solver,
    # avoiding an erroneous 'divergent' flag from finite-difference postprocessing.
    div_spectral=[]
    for field in fields:
        fh=B.fft(field)
        div_spectral.append(B.ifft(1j*np.einsum('...i,...i->...',B.K,fh)))
    div_rms=float(np.sqrt(np.mean(np.square(div_spectral))))
    projected_rhs=[]
    for field in fields:
        projected_rhs.append(B.ifft(B.rhs(B.project(B.fft(field)))))
    fd_rhs=(np.array(fields)[2:]-np.array(fields)[:-2])/(np.array(times)[2:,None,None,None,None]-np.array(times)[:-2,None,None,None,None])
    rhs=np.array(projected_rhs)[1:-1]
    residual_rms=float(np.sqrt(np.mean(np.square(fd_rhs-rhs))))
    rhs_rms=float(np.sqrt(np.mean(np.square(rhs))))
    results={'status':'EXPLORATORY_PERIODIC_EULER_NOT_CERTIFIED',
      'spectral_divergence_rms_model_units':div_rms,
      'euler_rhs_central_difference_residual_rms_model_units':residual_rms,
      'euler_rhs_relative_residual':residual_rms/max(rhs_rms,1e-30),
      'grid':int(grid),'steps':int(steps),'dt_model':float(dt),
      'duration_model':float(dt*steps),'sigma_model':float(sigma),
      'min_grid_points_per_core_sigma':float(sigma/B.h),
      'energy_relative_drift':float((energies[-1]-energies[0])/energies[0]),
      'helicity_relative_drift':float((hel[-1]-hel[0])/max(abs(hel[0]),1e-30)),
      'initial_knot':knot_signature(curves[0]),'final_knot':knot_signature(curves[-1]),
      'geometry_transform':transform,
      'model_assumptions':['Periodic 3D incompressible inviscid Euler',
        'Gaussian-smoothed centerline circulation; not a calibrated SST finite core',
        'Spectral 2/3 dealias; RK4 in time, trilinear passive-marker advection',
        'Knot marker topology tested over short evolution only',
        'Grid resolution and temporal refinement must be qualified before physical claims']}
    data=dict(t=np.array(times),filaments=np.array(curves)[:,None,:,:],
      present=np.ones((len(times),1),dtype=bool),gamma=np.ones((len(times),1)),
      material_ids=np.array(['loop0']),u_vertices=np.array(sampled_vel)[:,None,:,:],
      x_m=np.arange(grid)*B.h,y_m=np.arange(grid)*B.h,z_m=np.arange(grid)*B.h,
      u_grid=np.array(fields))
    return results,data


def dt_tag(v):
    return f"{v:.6g}".replace('.', 'p').replace('-', 'm')


def pilot_from_npz(path,output,grid=24,steps=4,duration_model=None,sigma_model=None):
    source=static_geometry(path)
    if source['status']!='STATIC_TOPOLOGY_DIAGNOSTIC':raise ValueError(source['status'])
    with np.load(path,allow_pickle=False) as d:p=d[source['source_key']]
    result,data=run_pilot(p,grid,steps,duration_model=duration_model,sigma_model=sigma_model)
    result['source_sha256']=source['source_sha256']
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    tag=f'N{grid}_S{steps}_T{dt_tag(result["duration_model"])}_SIG{dt_tag(result["sigma_model"])}'
    out=output/f'EULER_PILOT_{tag}.npz'
    np.savez_compressed(out,**data)
    import json
    (output/f'EULER_PILOT_{tag}.json').write_text(json.dumps(result,indent=2))
    return {'output':str(out),'summary':result}
