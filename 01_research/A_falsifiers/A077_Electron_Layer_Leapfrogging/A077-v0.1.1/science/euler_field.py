"""Optional 3D periodic Galerkin-truncated inviscid incompressible Euler PILOT.

Unforced ∂_t u = P(u×curl(u)), div u=0. Initial smooth, finite-width
axisymmetric ring-shaped fields with independent meridional and azimuthal
velocity components. This does NOT certify a compact material vortex tube,
spinor, electron or persistent discrete levels. No external forcing/viscosity.

Explicit SI mapping is optional: x -> R0*x, t -> (R0/U0)*t; density multiplies
kinetic energy. The field solver itself evolves dimensionless absolute time.
"""
from __future__ import annotations
import argparse,json,math
from pathlib import Path
import numpy as np

class GalerkinEuler:
    def __init__(self,n=24,L=8.0):
        if n<12 or n%2: raise ValueError('even n>=12 required')
        self.n=n;self.L=float(L);self.dx=L/n
        axes=[2*math.pi*np.fft.fftfreq(n,d=self.dx) for _ in range(3)]
        self.k=np.stack(np.meshgrid(*axes,indexing='ij'))
        self.k2=np.sum(self.k*self.k,axis=0)
        self.nz=np.where(self.k2>0,self.k2,1.)
        ids=np.fft.fftfreq(n)*n
        self.mask=np.logical_and.reduce([np.abs(t)<=n/3-1e-10 for t in np.meshgrid(ids,ids,ids,indexing='ij')])

    def fft(self,u):return np.fft.fftn(u,axes=(-3,-2,-1))
    def ifft(self,uh):return np.fft.ifftn(uh,axes=(-3,-2,-1)).real
    def proj(self,uh):
        dot=np.einsum('ixyz,ixyz->xyz',self.k,uh)
        return (uh-self.k*dot[None,...]/self.nz[None,...])*self.mask[None,...]
    def curl(self,uh):
        k=self.k
        return 1j*np.stack([k[1]*uh[2]-k[2]*uh[1], k[2]*uh[0]-k[0]*uh[2], k[0]*uh[1]-k[1]*uh[0]])
    def rhs(self,uh):
        u=self.ifft(uh)
        w=self.ifft(self.curl(uh))
        cross=np.stack([u[1]*w[2]-u[2]*w[1],u[2]*w[0]-u[0]*w[2],u[0]*w[1]-u[1]*w[0]])
        return self.proj(self.fft(cross))
    def initial(self,ring_spec, meridional=1.0, azimuthal=0.0):
        x=np.arange(self.n,dtype=float)*self.dx-self.L/2
        X,Y,Z=np.meshgrid(x,x,x,indexing='ij')
        r=np.sqrt(X*X+Y*Y)
        phi_hat=np.stack([-Y/(r+1e-24),X/(r+1e-24),np.zeros_like(X)])
        ap=np.zeros_like(r);vt=np.zeros_like(r)
        for spec in ring_spec:
            R=float(spec['R']);z0=float(spec['z']);a=float(spec['a']);sgn=float(spec.get('sign',1.0))
            if not 0<a<R or max(R+4*a,abs(z0)+4*a)>=self.L/2:
                raise ValueError('ring must fit within periodic buffer')
            bubble=np.exp(-((r-R)**2+(Z-z0)**2)/(2*a*a))
            ap+=sgn*meridional*a*bubble
            vt+=sgn*azimuthal*(r/R)*bubble
        A=phi_hat*ap
        u_mer=self.ifft(self.curl(self.proj(self.fft(A))))
        u_azi=phi_hat*vt
        uh=self.proj(self.fft(u_mer+u_azi))
        return uh,{'meridional_rms':float(np.sqrt(np.mean(u_mer*u_mer))),
                   'azimuthal_rms':float(np.sqrt(np.mean(u_azi*u_azi))),
                   'input_independent_components':True,
                   'toroidal_is_velocity_component_not_quantized_circulation':True}
    def diagnostics(self,uh):
        v=self.ifft(uh);w=self.ifft(self.curl(uh))
        dV=self.dx**3
        energy=float(.5*np.sum(v*v)*dV)
        helicity=float(np.sum(v*w)*dV)
        enstrophy=float(.5*np.sum(w*w)*dV)
        div=self.ifft(1j*np.sum(self.k*uh,axis=0))
        return {'energy':energy,'helicity':helicity,'enstrophy':enstrophy,
                'divergence_Linf':float(np.max(np.abs(div))),
                'max_velocity':float(np.max(np.sqrt(np.sum(v*v,axis=0))))}
    def evolve(self,uh,t_final,dt):
        if dt<=0 or t_final<=0:raise ValueError('time must be positive')
        steps=round(t_final/dt)
        if steps<1 or not math.isclose(steps*dt,t_final,rel_tol=1e-10,abs_tol=1e-12):
            raise ValueError('t_final/dt must be integer (fixed physical final time)')
        uh=uh.copy()
        init=self.diagnostics(uh)
        if dt*init['max_velocity']/self.dx>0.2:raise ValueError('initial CFL too large')
        data=[{'t':0.0,**init}]
        for j in range(steps):
            k1=self.rhs(uh);k2=self.rhs(self.proj(uh+.5*dt*k1))
            k3=self.rhs(self.proj(uh+.5*dt*k2));k4=self.rhs(self.proj(uh+dt*k3))
            uh=self.proj(uh+(dt/6)*(k1+2*k2+2*k3+k4))
            if j==steps-1 or (j+1)%max(1,steps//10)==0:
                d=self.diagnostics(uh);d['t']=(j+1)*dt;data.append(d)
                if not np.isfinite([d['energy'],d['helicity'],d['divergence_Linf']]).all():
                    raise FloatingPointError('nonfinite Euler pilot')
                if d['max_velocity']*dt/self.dx>0.2:raise FloatingPointError('CFL exceeded')
        return uh,data

def execute(cfg,output):
    cfg=dict(cfg);out=Path(output);out.mkdir(parents=True,exist_ok=True)
    n=int(cfg['n']);T=float(cfg['t_final']);dt=float(cfg['dt'])
    sim=GalerkinEuler(n,float(cfg['box_length']))
    results=[]
    for label,amp in [('no_toroidal',0.0),('toroidal_plus',float(cfg['toroidal_amplitude'])),('toroidal_minus',-float(cfg['toroidal_amplitude']))]:
        uh,initial=sim.initial(cfg['rings'],meridional=float(cfg['meridional_amplitude']),azimuthal=amp)
        end,diagnostics=sim.evolve(uh,T,dt)
        np.savez_compressed(out/(label+'_field.npz'),velocity_start=sim.ifft(uh),velocity_final=sim.ifft(end),
                            grid_length=np.array(sim.L),t_final=np.array(T))
        E0=diagnostics[0]['energy']; H0=diagnostics[0]['helicity'];Ef=diagnostics[-1]['energy'];Hf=diagnostics[-1]['helicity']
        results.append({'case':label,'amplitude':amp,'initial':initial,'trace':diagnostics,
                        'energy_relative_drift':abs(Ef-E0)/max(E0,1e-30),
                        'helicity_relative_drift':abs(Hf-H0)/max(abs(H0),1e-12),
                        'helicity_absolute_drift':abs(Hf-H0)})
    payload={'schema':'A077-EULER-GALERKIN-PILOT-1','status':'RESEARCH_ONLY_NOT_FULLY_QUALIFIED',
       'equations':'dealiased Fourier Galerkin Euler, ∂t u = P(u×curl u), no external forcing/viscosity',
       'limitations':['periodic box, not isolated R3','band-limited and dealiasing truncation',
                      'not certified material vortex core','no spatial/temporal/width convergence certified',
                      'no spinor or charge degree of freedom'],
       'units':'dimensionless x/R0 and t U0/R0; no unique physical mapping claimed',
       'configuration':cfg,'cases':results,
       'spinorial_separate_gate':{
          'status':'UNRESOLVED',
          'physical_state_bundle':'NOT_DEFINED',
          'derived_two_pi_sign_change':'NOT_DEMONSTRATED',
          'derived_four_pi_return':'NOT_DEMONSTRATED',
          'exchange_statistics':'NOT_EVALUATED',
          'reason':'An ordinary real three-component Euler velocity field has trivial 2pi spatial return; a nontrivial physically selected spinorial representation has not been constructed.'}}
    (out/'euler_diagnostics.json').write_text(json.dumps(payload,indent=2,allow_nan=False)+'\n')
    return payload

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',default='configs/euler_pilot.json');parser.add_argument('--output',default=None)
    args=parser.parse_args();config=json.loads(Path(args.config).read_text());
    target=args.output or f"A077_euler_pilot_v0.1.1-outputs"
    p=execute(config,target)
    for c in p['cases']:
        print(c['case'],'energy drift=',c['energy_relative_drift'], 'helicity drift=',c['helicity_absolute_drift'])
