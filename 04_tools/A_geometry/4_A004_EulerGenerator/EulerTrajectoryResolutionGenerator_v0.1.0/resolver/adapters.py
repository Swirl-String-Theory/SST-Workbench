"""Explicit source-locked adapters. No modification of frozen A075 or A077."""
from __future__ import annotations
import hashlib, importlib, json, sys
from pathlib import Path
import numpy as np

PINS = {
 'a075': {'experiment/euler3d.py':'e66cb8430d70e2738f6ddb2505d446c47b2a11cb71d9f6310ebbb2321748a063',
          'experiment/ruban.py':'6c402e8f9928556f3593447ef85f7874d23f472f21d689261a30bafa623642f6'},
 'a077': {'science/euler_field.py':'04e45be7a79da52a018c04cf2e8144efa98e27c4931ed123af20832bd9b4f90d',
          'configs/euler_pilot.json':'38b08c59eed3e33fcd48d3d3869fcb39de7cd26ba72fe65f0860c1df63044e99'}
}

def hash_file(path:Path):return hashlib.sha256(path.read_bytes()).hexdigest()

def check_source(provider,root):
    actual={}
    for rel, expected in PINS[provider].items():
        p=root/rel
        if not p.is_file():raise FileNotFoundError(f'SOURCE_MISSING {p}')
        h=hash_file(p)
        if h!=expected:raise RuntimeError(f'SOURCE_DRIFT {p}: expected {expected}, actual {h}; no fallback')
        actual[rel]=h
    return actual

def import_pinned(provider,root):
    check_source(provider,root)
    root=str(root.resolve())
    if root not in sys.path:sys.path.insert(0,root)
    name='experiment.euler3d' if provider=='a075' else 'science.euler_field'
    if name in sys.modules and not str(Path(sys.modules[name].__file__).resolve()).startswith(root):
        raise RuntimeError('WRONG_IMPORTED_SOLVER: separate process per provider required')
    obj=importlib.import_module(name)
    if not str(Path(obj.__file__).resolve()).startswith(root):raise RuntimeError('IMPORT_PROVENANCE_MISMATCH')
    return obj

class Adapter:
    def __init__(self,provider,root,n,source_case='default',a075_core=0.42,a075_geometry='ruban'):
        self.provider=provider;self.root=Path(root).resolve();self.module=import_pinned(provider,self.root)
        if provider=='a075':
            e=self.module
            if a075_geometry=='ruban':
                from experiment import ruban as rb
                candidate=self.root/'inputs/ruban_t23'/rb.PRIMARY
                if not candidate.is_file():raise FileNotFoundError('RUBAN_SOURCE_MISSING '+str(candidate))
                self.seed_sha=hash_file(candidate)
                initial='ruban_isolated';seed_path=str(candidate)
                from experiment.ruban import load_primary_seed
                curve, provenance=load_primary_seed(candidate)
            elif a075_geometry=='coupled_ring_trefoil':
                initial='legacy_coupled';seed_path=''
                curve,provenance=e.curve('0_1',.98,0.,nseg=192)
                self.seed_sha='ANALYTIC_RING'
            else: raise ValueError('a075 geometry ruban|coupled_ring_trefoil')
            cfg=e.Config(n=n,box=10.,core=float(a075_core),gamma_receiver=2*np.pi,
                gamma_donor=0.,initial_condition=initial,ruban_seed_path=seed_path,
                incoming=False,receiver_on=True,backend='cpu-scipy-fft',threads=1)
            self.sim=e.Euler3D(cfg);self.L=cfg.box;self.dx=self.sim.dx
            self.initial_hat,self.provenance=self.sim.initial_velocity()
            self.provenance={'source':self.provenance,'seed_sha256':self.seed_sha,'geometry_source':provenance}
            self.marker_curve=np.asarray(curve,float)
        else:
            e=self.module
            spec=json.loads((self.root/'configs/euler_pilot.json').read_text())
            self.cfg_sha=hash_file(self.root/'configs/euler_pilot.json')
            self.L=float(spec['box_length']);self.sim=e.GalerkinEuler(n,self.L);self.dx=self.sim.dx
            amps={'no_toroidal':0.,'toroidal_plus':float(spec['toroidal_amplitude']),
                  'toroidal_minus':-float(spec['toroidal_amplitude'])}
            if source_case not in amps:raise ValueError('a077 case must be no_toroidal|toroidal_plus|toroidal_minus')
            self.initial_hat,pr=self.sim.initial(spec['rings'],
                meridional=float(spec['meridional_amplitude']),azimuthal=amps[source_case])
            self.provenance={'case':source_case,'init':pr,'config_sha256':self.cfg_sha,
                             'ring_spec':spec['rings']}
            pts=[]
            for ring in spec['rings']:
                theta=np.arange(64)*2*np.pi/64
                pts.extend(np.column_stack((ring['R']*np.cos(theta),ring['R']*np.sin(theta),
                         np.full(len(theta),ring['z']))))
            self.marker_curve=np.asarray(pts,float)

    def proj(self,uh):return self.sim.project(uh) if self.provider=='a075' else self.sim.proj(uh)
    def rhs(self,uh):return self.sim.rhs(uh)
    def physical_velocity(self,uh):
        out=self.sim.ifft(uh)
        return out if self.provider=='a075' else np.moveaxis(out,0,-1)
    def interp(self,uh,x):
        """Periodic vectorized trilinear interpolation at independent unwrapped tracers."""
        u=self.physical_velocity(uh);n=self.sim.c.n if self.provider=='a075' else self.sim.n
        origin=-self.L/2+(self.dx/2 if self.provider=='a075' else 0.0)
        g=(np.asarray(x)-origin)/self.dx
        lo=np.floor(g).astype(np.int64);frac=g-lo
        out=np.zeros_like(x,dtype=np.float64)
        for i in (0,1):
          for j in (0,1):
           for k in (0,1):
            offset=np.array([i,j,k]);jj=(lo+offset)%n
            weight=np.prod(np.where(offset==1,frac,1-frac),axis=1)
            out+=weight[:,None]*u[jj[:,0],jj[:,1],jj[:,2]]
        return out
    def diagnostics(self,uh):
        if self.provider=='a077':return self.sim.diagnostics(uh)
        energy=self.sim.global_energy_hat(uh)
        u=self.physical_velocity(uh);om=self.sim.ifft(self.sim.curl_hat(uh))
        helicity=float(np.sum(u*om)*self.dx**3)
        divh=sum(1j*self.sim.k[k]*uh[...,k] for k in range(3))
        div=self.sim.ifft(divh)
        return {'energy':energy,'helicity':helicity,
         'divergence_Linf':float(np.max(np.abs(div))),
         'max_velocity':float(np.max(np.linalg.norm(u,axis=-1))),
         'enstrophy':float(.5*np.sum(om*om)*self.dx**3)}
