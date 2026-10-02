import re
import numpy as np
from pathlib import Path
from .geometry import synthetic_trefoil,resample_closed,normalize,broadband_probe,kabsch_align
from .solver import segment_lengths,velocity,stretch_rate,backend_name
from .modal import learn_modes,project,recurrence_metrics,delayed_stretch_test

def run():
    x,_=normalize(resample_closed(synthetic_trefoil(160),64)); p=broadband_probe(x); assert abs(np.sqrt(np.mean(np.sum(p*p,axis=1)))-1)<1e-12; y=kabsch_align(x@np.array([[0,-1,0],[1,0,0],[0,0,1.]]),x); assert np.mean((y-x)**2)<1e-20
    t=np.linspace(0,12*np.pi,241); mode=np.zeros((64,3)); mode[:,0]=np.cos(2*np.pi*np.arange(64)/64); mode/=np.linalg.norm(mode); resp=np.sin(t)[:,None,None]*mode[None,:,:]; modes,ev=learn_modes(resp,96,3); a=project(resp,modes)[:,0]; r=recurrence_metrics(t[96:],a[96:]); assert r['valid'] and r['cycles']>2 and r['harmonic_r2']>.9
    native=Path(__file__).resolve().parents[2]/'cpp/native.cpp'; s=native.read_text(); bad=re.findall(r'(?<![:\w])ssize_t',s); assert not bad, bad
    return {'pass':True,'backend':backend_name(),'probe_rms':float(np.sqrt(np.mean(np.sum(p*p,axis=1)))),'synthetic_cycles':r['cycles'],'synthetic_harmonic_r2':r['harmonic_r2'],'msvc_ssize_guard':'py::ssize_t'}
