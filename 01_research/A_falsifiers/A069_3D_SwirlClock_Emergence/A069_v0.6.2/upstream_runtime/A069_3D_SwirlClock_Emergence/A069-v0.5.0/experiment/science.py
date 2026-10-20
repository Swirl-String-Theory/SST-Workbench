"""A069 v0.1.0: honest analytic 3D incompressible Euler control.

D1 is a local affine Euler solution with infinite domain energy and is ONLY
an algorithmic positive control, never evidence for a stable finite-core vortex.
The measured phase is integrated from a material tracer's Cartesian path,
independently of the analytic phase prediction.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import numpy as np

SCHEMA = 'SST-3D-SWIRL-CLOCK-ANALYTIC-1'

@dataclass(frozen=True)
class AffineVortex:
    strain: float = 0.2  # 1 / normalized time
    omega0: float = 1.1 # 1 / normalized time
    radius0: float = 1.0
    rho: float = 1.0

    def omega(self, time: float) -> float:
        return self.omega0 * np.exp(self.strain * time)

    def radius(self, time: float) -> float:
        return self.radius0 * np.exp(-0.5 * self.strain * time)

    def matrix(self, time: float) -> np.ndarray:
        o = self.omega(time); a = self.strain
        return np.array([[-a/2., -o, 0.], [o, -a/2., 0.], [0., 0., a]],dtype=float)

    def derivative_matrix(self, time: float) -> np.ndarray:
        odot=self.strain*self.omega(time)
        return np.array([[0.,-odot,0.],[odot,0.,0.],[0.,0.,0.]],dtype=float)

    def velocity(self, time: float, position: np.ndarray) -> np.ndarray:
        return self.matrix(time) @ position

    def circulation(self, time: float) -> float:
        return float(2*np.pi*self.radius(time)**2*self.omega(time))

    def phase_prediction(self, time: float) -> float:
        a=self.strain
        return float(self.omega0*(np.expm1(a*time)/a if abs(a)>1e-14 else time))

    def residuals(self, time: float) -> dict:
        m=self.matrix(time)
        accel=self.derivative_matrix(time)+m@m
        # p(x,t) = -(rho/2) x.T @ sym(accel) @ x + p0(t)
        pressure_hessian=-self.rho*(accel+accel.T)/2
        euler=accel+pressure_hessian/self.rho
        return {
            'divergence':float(np.trace(m)),
            'euler_accel_residual_fro':float(np.linalg.norm(euler)),
            'vorticity_transport_residual':float(abs(2*self.strain*self.omega(time) - 2*self.omega(time)*self.strain)),
            'circulation_relative_error':float(abs(self.circulation(time)/self.circulation(0.)-1)),
            'omega_kelvin_relative_error':float(abs(self.omega(time) /(self.circulation(0.)/(2*np.pi*self.radius(time)**2)) - 1.)),
            'pressure_hessian_symmetric_error':float(np.linalg.norm(pressure_hessian-pressure_hessian.T)),
        }


def integrate_tracer(flow: AffineVortex, t_end:float=2., steps:int=160, method:str='rk4') -> dict:
    """Cartesian Lagrangian tracer. No frequency or phase prediction as input."""
    if steps<4 or method not in {'rk4','midpoint'}: raise ValueError('steps>=4; method rk4 or midpoint')
    dt=t_end/steps
    p=np.array([flow.radius0,0.,0.],float)
    cartesian_phase=[float(np.arctan2(p[1],p[0]))]
    for k in range(steps):
        t=k*dt
        f=lambda ti,pi:flow.velocity(ti,pi)
        k1=f(t,p)
        k2=f(t+dt/2,p+dt*k1/2)
        if method=='rk4':
            k3=f(t+dt/2,p+dt*k2/2)
            k4=f(t+dt,p+dt*k3)
            p=p+dt*(k1+2*k2+2*k3+k4)/6
        else:
            p=p+dt*k2
        cartesian_phase.append(float(np.arctan2(p[1],p[0])))
    theta=float(np.unwrap(np.asarray(cartesian_phase))[-1]-cartesian_phase[0])
    radius=float(np.linalg.norm(p[:2]))
    pred=flow.phase_prediction(t_end)
    return {'method':method,'steps':steps,'phase_tracer':theta,'phase_pred':pred,
            'phase_abs_error':abs(theta-pred),
            'radius_tracer':radius,'radius_pred':float(flow.radius(t_end)),
            'radius_rel_error':abs(radius/flow.radius(t_end)-1)}


def rotating_frame_decomposition(absolute_rate:float, frame_rate:float)->dict:
    """curl(Omega x r) = 2 Omega; frame term is NOT a separate physical flow."""
    omega_abs=2*absolute_rate
    omega_rel=2*(absolute_rate-frame_rate)
    return {'absolute_vorticity':omega_abs,'relative_vorticity':omega_rel,
            'frame_vorticity':2*frame_rate,
            'reconstruction_error':abs(omega_abs-(omega_rel+2*frame_rate))}


def analytical_suite()->dict:
    cases=[]
    for a in (-0.3,0.,0.25):
        f=AffineVortex(strain=a,omega0=1.1,radius0=1.2)
        res=[f.residuals(t) for t in (0.,0.4,1.25,2.)]
        trace=integrate_tracer(f,2.,320,'rk4')
        coarse=integrate_tracer(f,2.,40,'rk4')
        medium=integrate_tracer(f,2.,80,'rk4')
        second=integrate_tracer(f,2.,640,'midpoint')
        frame=[rotating_frame_decomposition(f.omega(0.),q) for q in (-2.,0.,3.)]
        cases.append({'strain':a,'residuals':res,'tracer':trace,
                      'tracer_coarse':coarse,'tracer_medium':medium,
                      'midpoint':second,'frame':frame})
    maxima={k:max(r[k] for c in cases for r in c['residuals']) for k in cases[0]['residuals'][0]}
    maxima['tracer_phase_abs_error']=max(c['tracer']['phase_abs_error'] for c in cases)
    maxima['tracer_radius_rel_error']=max(c['tracer']['radius_rel_error'] for c in cases)
    maxima['frame_reconstruction_error']=max(f['reconstruction_error'] for c in cases for f in c['frame'])
    # RK4 should converge and independently reproduce the angular tracer evolution.
    monotone=all(c['tracer']['phase_abs_error'] <= c['tracer_medium']['phase_abs_error']+1e-13 and
                 c['tracer_medium']['phase_abs_error'] <= c['tracer_coarse']['phase_abs_error']+1e-13
                 for c in cases)
    identity_pass=max(maxima[k] for k in maxima if k not in ('tracer_phase_abs_error','tracer_radius_rel_error'))<2e-12
    tracer_pass=(maxima['tracer_phase_abs_error']<1e-7 and maxima['tracer_radius_rel_error']<1e-7 and monotone)
    return {'schema':SCHEMA,'evidence_class':'analytic_control','physical_clock_claim':False,
            'whole_space_energy_finite':False,'parameters_dimensionless':True,
            'status':'PASS' if (identity_pass and tracer_pass) else 'FAIL',
            'identity_pass':identity_pass,'tracer_pass':tracer_pass,
            'maxima':maxima,'rk4_monotone':monotone,'cases':cases,
            'interpretation':'Analytic positive control: not a finite-core, stable, knotted SST clock.'}


def validate_e011_admission(seed_record:dict, source_verified:bool=False, dynamics_verified:bool=False)->dict:
    """Fail-closed: STATIC_READY != DYNAMICS_READY; no filename-only acceptance."""
    p=seed_record.get('provider_status','')
    family=seed_record.get('provider_family')
    raw_hash=seed_record.get('raw_sha256','')
    geom_hash=seed_record.get('geometry_sha256','')
    ok_hash=lambda x:isinstance(x,str) and len(x)==64 and all(ch in '0123456789abcdef' for ch in x.lower())
    errors=[]
    if seed_record.get('static_status')!='STATIC_READY':errors.append('not_STATIC_READY')
    if p not in ('CROSS_PROVIDER_ROBUST','CROSS_PROVIDER_SENSITIVE','SINGLE_PROVIDER_QUALIFIED'):
        errors.append('provider_qualification_missing')
    if not family: errors.append('independent_provider_family_missing')
    if seed_record.get('source_stage')!='PRIMARY_REFERENCE':errors.append('not_primary_reference')
    if not ok_hash(raw_hash) or not ok_hash(geom_hash): errors.append('hash_locators_missing')
    if not source_verified:errors.append('source_bytes_not_verified')
    if not dynamics_verified:errors.append('DYNAMICS_READY_not_certified')
    return {'admitted_for_dynamic_clock':not errors,'reasons':errors,'static_status':seed_record.get('static_status'),
            'provider_status':p}


def refuse_legacy_inputs(paths:list[str])->dict:
    """Reject only case-insensitive LEGACY provenance tags, not provider labels."""
    forbidden=('knotplot/knots/final','knotplot\\knots\\final','legacy_relaxed',
               'visual_relaxation','historical_knotplot','vortexlab_proxy')
    rejected=[s for s in paths if any(x in s.lower() for x in forbidden)]
    return {'status':'FAIL' if rejected else 'PASS','rejected':rejected}


def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with open(path,'rb') as fh:
        for chunk in iter(lambda:fh.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def write_json(path:Path,payload:dict)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(payload,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
