from __future__ import annotations
import numpy as np
from sst_falsifier.backends import cpp_pybind
from sst_falsifier.backend_contract import parity_gate,require_backend
from .traveling import signed_harmonic_powers_series


def certify(root,cfg):
    mod,build=cpp_pybind.load(root,force_build=False,require=True,verbose=False)
    info=dict(mod.backend_info())
    actual=info.get('backend',build.actual_backend)
    # Three deterministic, nonuniform-phase complex signals including mixed direction content.
    rng=np.random.default_rng(int(cfg.get('seed',5503101))); refs=[]; cands=[]
    for n in (31,64,97):
        steps=1.0+0.15*rng.normal(size=n); theta=2*np.pi*np.cumsum(steps)/np.sum(steps); theta-=theta[0]
        an=np.exp(1j*2*theta)+0.23*np.exp(-1j*theta)+0.05*(rng.normal(size=n)+1j*rng.normal(size=n))
        ab=0.4j*np.exp(1j*2*theta)-0.17*np.exp(-1j*3*theta)
        py=signed_harmonic_powers_series(theta,an,ab,3)
        cpp=np.asarray(mod.signed_harmonic_powers(theta,an.real,an.imag,ab.real,ab.imag,3),float)
        refs.append(py.ravel()); cands.append(cpp.ravel())
    ref=np.concatenate(refs); cand=np.concatenate(cands); pg=parity_gate(cand,ref,float(cfg['native_metric_relative_l2_max']))
    br={**build.to_dict(),'backend_info':info}
    if actual not in {'openmp','serial'}: pg['pass']=False; pg['backend_error']=f'unaccepted actual backend {actual}'
    return {'status':'PASS' if pg['pass'] else 'FAIL','parity':pg,'build':br,'actual_backend':actual,'authority':'CERTIFICATION'}
