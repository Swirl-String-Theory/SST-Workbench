#!/usr/bin/env python3
"""Independent 3D periodic incompressible Euler pseudo-spectral RK4 qualification.

Purpose: numerical PDE benchmark and conditional projected C005 initial data.
Not a full free-space Euler vortex-core convergence/physical SST model.
"""
from __future__ import annotations
import argparse,hashlib,json,math,secrets,sys
from datetime import datetime,timezone
from pathlib import Path
import numpy as np

SCHEMA='sst.a003.g6p9.periodic-euler/1'

class EulerError(RuntimeError):pass

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def safe_write(path,obj):
 with Path(path).open('x',encoding='utf8') as f:json.dump(obj,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')

class PeriodicEuler:
 def __init__(self,n):
  if not isinstance(n,int) or n<8 or n%2:raise EulerError('Even grid N>=8 required')
  self.n=n;freq=np.fft.fftfreq(n,d=1/n);self.k=np.meshgrid(freq,freq,freq,indexing='ij')
  self.k2=sum(k*k for k in self.k);self.nonzero=self.k2>0
  self.ksafe=np.where(self.nonzero,self.k2,1.)
  self.mask=(np.abs(self.k[0])<n/3)&(np.abs(self.k[1])<n/3)&(np.abs(self.k[2])<n/3)
  self.domain=(2*math.pi)**3
 def fft(self,u):return np.fft.fftn(u,axes=(-3,-2,-1))
 def ifft(self,U):return np.fft.ifftn(U,axes=(-3,-2,-1)).real
 def project(self,u):
  U=self.fft(u);prod=sum(k*U[i] for i,k in enumerate(self.k));U=U-np.stack([k*prod/self.ksafe for k in self.k]);U*=self.mask
  return self.ifft(U)
 def derivatives(self,u):
  U=self.fft(u)*self.mask
  return np.asarray([self.ifft(1j*k*U[j]) for j in range(3) for k in self.k]).reshape((3,3,self.n,self.n,self.n))
 def nonlinear(self,u):
  grad=self.derivatives(u)
  adv=np.einsum('iabc,jiabc->jabc',u,grad,optimize=True)
  advhat=self.fft(adv)*self.mask
  divhat=sum(k*advhat[i] for i,k in enumerate(self.k))
  phat=(1j*divhat)/self.ksafe
  pressure=self.ifft(phat)
  pgrad=np.asarray([self.ifft(1j*k*phat) for k in self.k]);rhs=-self.ifft(advhat)-pgrad
  # Leray project forces derivative/divergence to roundoff
  rhs=self.project(rhs)
  # Poisson equation: delta p = - sum_{i,j} (partial_i u_j) (partial_j u_i)
  src=-np.einsum('ijabc,jiabc->abc',grad,grad,optimize=True)
  lap_p=self.ifft(-self.k2*phat)
  src_filtered=self.ifft(self.fft(src)*self.mask)
  pp_res=lap_p-src_filtered
  pp_res-=np.mean(pp_res)
  div_u=self.ifft(1j*sum(k*self.fft(u)[i] for i,k in enumerate(self.k)))
  return rhs,pressure,{'divergence_max':float(np.max(np.abs(div_u))),
    'pressure_poisson_residual_rms':float(np.sqrt(np.mean(pp_res**2))),
    'pressure_poisson_source_rms':float(np.sqrt(np.mean(src**2))),
    'momentum_equation_algebra_residual_rms':float(np.sqrt(np.mean((rhs+self.ifft(advhat)+pgrad)**2)))}
 def integrate(self,u,tf,steps):
  if steps<1 or tf<=0:raise EulerError('Positive time and steps required')
  u=self.project(u);dt=tf/steps;energies=[energy(u)];states=[]
  for q in range(steps):
   k1,_,_=self.nonlinear(u);k2,_,_=self.nonlinear(self.project(u+.5*dt*k1))
   k3,_,_=self.nonlinear(self.project(u+.5*dt*k2));k4,_,_=self.nonlinear(self.project(u+dt*k3))
   u=self.project(u+dt*(k1+2*k2+2*k3+k4)/6)
   if not np.isfinite(u).all():raise EulerError('Nonfinite Euler state')
   energies.append(energy(u))
  rhs,p,checks=self.nonlinear(u)
  checks['relative_energy_drift']=float((energies[-1]-energies[0])/max(abs(energies[0]),1e-30))
  checks['final_rhs_rms']=float(np.sqrt(np.mean(rhs**2)))
  return u,p,checks

def energy(u):return .5*float(np.mean(np.sum(u*u,axis=0)))

def field(n,kind):
 x=np.arange(n)*2*math.pi/n
 X,Y,Z=np.meshgrid(x,x,x,indexing='ij')
 if kind=='ABC':return np.array([np.sin(Z)+np.cos(Y),np.sin(X)+np.cos(Z),np.sin(Y)+np.cos(X)])
 if kind=='TaylorGreen':return np.array([np.sin(X)*np.cos(Y)*np.cos(Z),-np.cos(X)*np.sin(Y)*np.cos(Z),np.zeros_like(X)])
 raise EulerError('Unknown analytic field '+kind)

def compare_fourier(coarse,fine):
 n=coarse.shape[-1];m=fine.shape[-1]
 if m==n:return float(np.sqrt(np.mean((coarse-fine)**2)))
 # Fourier index transfer rather than point matching/interpolation.
 F=np.fft.fftshift(np.fft.fftn(fine,axes=(-3,-2,-1)),axes=(-3,-2,-1))
 s=(m-n)//2
 C=F[...,s:s+n,s:s+n,s:s+n]*(n/m)**3
 sample=np.fft.ifftn(np.fft.ifftshift(C,axes=(-3,-2,-1)),axes=(-3,-2,-1)).real
 return float(np.sqrt(np.mean((coarse-sample)**2)))

def benchmark(tf=.05,steps=8,levels=(8,12,16)):
 rows=[];final={}
 for n in levels:
  solver=PeriodicEuler(n)
  u0=field(n,'ABC');rhs,p,checks=solver.nonlinear(u0)
  p_target=-.5*np.sum(u0*u0,axis=0);p_target-=np.mean(p_target)
  abc_rhs=float(np.sqrt(np.mean(rhs**2)));abc_pres=float(np.sqrt(np.mean((p-p_target)**2)))
  x,p2,diag=solver.integrate(field(n,'TaylorGreen'),tf,steps)
  y,_,_=solver.integrate(field(n,'TaylorGreen'),tf,2*steps)
  rows.append({'grid_n':n,'ABC_stationary_rhs_rms':abc_rhs,
    'ABC_pressure_analytic_rms':abc_pres,'TaylorGreen_temporal_rms_steps_vs_double':float(np.sqrt(np.mean((x-y)**2))),
    'TaylorGreen_energy_drift':diag['relative_energy_drift'],'TaylorGreen_divergence_max':diag['divergence_max'],
    'TaylorGreen_Poisson_residual_rms':diag['pressure_poisson_residual_rms'],
    'TaylorGreen_momentum_algebra_residual_rms':diag['momentum_equation_algebra_residual_rms']})
  final[n]=y
 for q,n in enumerate(levels[:-1]):rows[q]['spatial_rms_to_next_fine']=compare_fourier(final[n],final[levels[q+1]])
 checks={'ABC_stationary':all(r['ABC_stationary_rhs_rms']<1e-10 for r in rows),
 'ABC_pressure':all(r['ABC_pressure_analytic_rms']<1e-10 for r in rows),
 'TaylorGreen_divergence':all(r['TaylorGreen_divergence_max']<1e-9 for r in rows),
 'TaylorGreen_pressure_Poisson':all(r['TaylorGreen_Poisson_residual_rms']<1e-9 for r in rows),
 'energy_short_horizon':all(abs(r['TaylorGreen_energy_drift'])<1e-5 for r in rows)}
 return {'schema':SCHEMA,'benchmark':'ABC stationary analytical pressure and Taylor-Green evolving field',
 'boundary_conditions':'triply-periodic [-pi,pi)^3','density':1.,'viscosity':0.,'method':'2/3 dealiased Fourier pseudospectral Leray-projected RK4',
 'tfinal':tf,'time_steps':steps,'levels':list(levels),'rows':rows,'checks':checks,
 'benchmark_status':'PASS_NUMERICAL_EULER_BENCHMARK' if all(checks.values()) else 'FAIL',
 'g6p9':'UNRESOLVED',
 'exclusions':['A003 source-native filament-to-volume 3D vorticity calibration','same-boundary field comparison with C005 free space','free-space Euler','core scale physical calibration','independent PDE implementation crosscheck','certified PDE truncation-error bounds']}

def projected_c005_init(xyz,c005,n=8,tf=.005,steps=4,epsilon=.05):
 from fourier_atlas_adapter import read_xyz
 if not (Path(c005)/'fermat_ext'/'core.py').is_file():raise EulerError('C005 core missing')
 import importlib
 sys.path.insert(0,str(Path(c005).resolve()))
 core=importlib.import_module('fermat_ext.core')
 if Path(core.__file__).resolve()!=Path(c005).resolve()/'fermat_ext'/'core.py' or core.PACKAGE_VERSION!='0.6.1':raise EulerError('C005 source identity failed')
 xyz=Path(xyz);coords=np.loadtxt(xyz)
 if coords.ndim!=2 or coords.shape[1]!=3 or not np.isfinite(coords).all():raise EulerError('Invalid XYZ')
 # Normalize into 2pi box, do not claim this preserves any physical length.
 coords=coords-coords.mean(axis=0)
 radius=np.max(np.linalg.norm(coords,axis=1))
 if radius<=0:raise EulerError('Degenerate source centerline')
 coords=coords*(math.pi*.5/radius)
 zz=np.arange(n)*2*math.pi/n-math.pi
 X,Y,Z=np.meshgrid(zz,zz,zz,indexing='ij');probes=np.stack([X,Y,Z],-1).reshape(-1,3)
 result,meta=core.backend_biot_savart(coords,probes,epsilon=epsilon,force_python=True,auto_build=False)
 unproj=np.asarray(result).reshape((n,n,n,3)).transpose((3,0,1,2))
 solver=PeriodicEuler(n);u0=solver.project(unproj);u1,p,checks=solver.integrate(u0,tf,steps)
 return {'schema':SCHEMA,'source_sha256':digest(xyz),'C005_core_sha256':digest(Path(core.__file__)),
  'original_n':int(len(coords)),'grid_n':n,'boundary_conditions':'periodic, INCOMPATIBLE with original C005 free-space kernel',
  'C005_backend':meta,'source_to_grid_construction':'C005 free-space probe then Fourier Helmholtz projection',
  'projection_discrepancy_rms':float(np.sqrt(np.mean((u0-unproj)**2))),
  'initial_energy':energy(u0),'final_energy':energy(u1),'checks':checks,'status':'DIAGNOSTIC_ONLY_NOT_ORIGINAL_FILAMENT_EULER_CLOSURE',
  'G6P9':'UNRESOLVED'}

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--tfinal',type=float,default=.05);p.add_argument('--steps',type=int,default=8)
 p.add_argument('--xyz',type=Path);p.add_argument('--c005',type=Path);p.add_argument('--coupled-grid',type=int,default=8)
 a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
 z=benchmark(a.tfinal,a.steps);safe_write(a.out/'G6P9_EULER_BENCHMARK.json',z)
 if a.xyz:
  if not a.c005:raise EulerError('--xyz requires --c005')
  try:safe_write(a.out/'G6P9_C005_PERIODIC_PROJECTION.json',projected_c005_init(a.xyz,a.c005,a.coupled_grid))
  except Exception as e:
   safe_write(a.out/'G6P9_C005_PERIODIC_PROJECTION_ERROR.json',{'status':'NOT_QUALIFIED','reason':str(e)})
 print(json.dumps({'output':str(a.out),'status':z['benchmark_status'],'G6P9':'UNRESOLVED','checks':z['checks']},indent=2))
 return 0 if z['benchmark_status'].startswith('PASS') else 4
if __name__=='__main__':raise SystemExit(main())
