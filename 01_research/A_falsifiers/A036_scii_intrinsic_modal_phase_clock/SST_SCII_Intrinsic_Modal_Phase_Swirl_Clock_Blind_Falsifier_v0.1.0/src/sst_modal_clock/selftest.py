import re
import numpy as np
from pathlib import Path
from .geometry import synthetic_trefoil,resample_closed,normalize,broadband_probe,kabsch_align,tangential_redistribution_velocity,component_offsets_from_lengths
from .solver import backend_name,velocity_from_cores
from .modal import learn_modes,project,recurrence_metrics
from .sc2 import phase_clock_metrics,phase_clock_gates

def run():
    x,_=normalize(resample_closed(synthetic_trefoil(160),64)); p=broadband_probe(x)
    assert abs(np.sqrt(np.mean(np.sum(p*p,axis=1)))-1)<1e-12
    y=kabsch_align(x@np.array([[0,-1,0],[1,0,0],[0,0,1.]]),x); assert np.mean((y-x)**2)<1e-20
    # multi-return recurrence synthetic: six cycles, non-bin-locked frequency
    t=np.linspace(0,13.7*np.pi,401); mode=np.zeros((64,3)); mode[:,0]=np.cos(2*np.pi*np.arange(64)/64); mode/=np.linalg.norm(mode)
    resp=np.sin(.93*t+.2)[:,None,None]*mode[None,:,:]; modes,ev,center=learn_modes(resp,80,3); a=project(resp,modes,center)[:,0]; r=recurrence_metrics(t[80:],a[80:],4)
    assert r['valid'] and r['cycles']>4 and r['harmonic_r2']>.9 and r['multi_return_closure_median']<.25 and r['period_cv']<.1
    # redistribution must be tangent-only to numerical precision
    th=np.linspace(0,2*np.pi,64,endpoint=False); ring=np.c_[np.cos(th+0.20*np.sin(th)),np.sin(th+0.20*np.sin(th)),np.zeros_like(th)]
    vm=tangential_redistribution_velocity(ring,2.0); tangent=np.roll(ring,-1,axis=0)-np.roll(ring,1,axis=0); tangent/=np.linalg.norm(tangent,axis=1)[:,None]
    normal_leak=np.linalg.norm(vm-(vm*tangent).sum(1)[:,None]*tangent)/max(np.linalg.norm(vm),1e-15); assert normal_leak<1e-12
    # Indexed multi-component kernel smoke: two separate closed rings, no bridge segment.
    q=np.linspace(0,2*np.pi,20,endpoint=False); a=np.c_[.5*np.cos(q)-1,.5*np.sin(q),0*q]; b=np.c_[.5*np.cos(q)+1,.5*np.sin(q),0*q]; link=np.vstack([a,b]); off=component_offsets_from_lengths([20,20]); ul=velocity_from_cores(link,1.0,np.full(40,.08),False,off); assert np.isfinite(ul).all()
    # SC-II synthetic phase clock: persistent natural mode with predictable phase.
    tp=np.linspace(0,24,2401); yp=.2*np.cos(2*np.pi*tp/3.0+.37); scfg={'sc2_gate_min_discovery_energy':.03,'sc2_gate_min_holdout_amplitude':1e-5,'sc2_gate_min_phase_wraps':4,'sc2_gate_min_monotonic_fraction':.90,'sc2_gate_min_phase_linearity_r2':.90,'sc2_gate_max_period_cv':.15,'sc2_gate_min_spectral_power':.30,'sc2_gate_min_harmonic_r2':.50,'sc2_gate_max_phase_diffusion_rms_rad':.75,'sc2_gate_max_envelope_cv':.60,'sc2_gate_min_envelope_retention_ratio':.40,'sc2_gate_max_envelope_retention_ratio':2.5,'sc2_gate_min_envelope_reliable_fraction':.95,'sc2_gate_max_phase_prediction_rms_rad':1.0,'sc2_gate_max_phase_prediction_terminal_error_rad':1.57}; pm=phase_clock_metrics(tp,yp,scfg); pg=phase_clock_gates(pm,.8,scfg,'natural'); assert all(pg)
    native=Path(__file__).resolve().parents[2]/'cpp/native.cpp'; s=native.read_text(); bad=re.findall(r'(?<![:\w])ssize_t\b',s); assert not bad,bad
    return {'pass':True,'backend':backend_name(),'probe_rms':float(np.sqrt(np.mean(np.sum(p*p,axis=1)))),'synthetic_cycles':r['cycles'],'synthetic_harmonic_r2':r['harmonic_r2'],'synthetic_multi_return_closure_median':r['multi_return_closure_median'],'mesh_normal_leak_ratio':float(normal_leak),'multicomponent_kernel_finite':bool(np.isfinite(ul).all()),'msvc_ssize_guard':'py::ssize_t','sc2_synthetic_phase_wraps':pm['phase_wraps'],'sc2_synthetic_phase_linearity_r2':pm['phase_linearity_r2'],'sc2_synthetic_phase_prediction_rms_rad':pm['phase_prediction_rms_rad']}
