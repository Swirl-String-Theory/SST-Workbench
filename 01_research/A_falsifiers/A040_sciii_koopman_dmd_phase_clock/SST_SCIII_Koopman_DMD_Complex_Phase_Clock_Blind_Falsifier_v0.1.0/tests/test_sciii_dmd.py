import json
from pathlib import Path
import numpy as np
from sst_modal_clock.sciii import _discovery_candidates,_q1,sciii_metrics,sciii_gates

ROOT=Path(__file__).resolve().parents[1]

def cfg(): return json.loads((ROOT/'config/basic.json').read_text())

def moving_plane(t,period=1.8,beta=.03):
    w=2*np.pi/period
    return np.c_[np.cos(w*t)*np.cos(beta*t),np.sin(w*t)*np.cos(beta*t),np.cos(w*t)*np.sin(beta*t),np.sin(w*t)*np.sin(beta*t)]

def test_moving_subspace_koopman_clock_passes():
    c=cfg(); t=np.arange(0,24.0001,.02); X=moving_plane(t); nd=np.searchsorted(t,c['sciii_discovery_time']); ds=_discovery_candidates(t[:nd],X[:nd],c); ref=next(d for d in ds if _q1(d,c)); m,q,loc=sciii_metrics(t[nd:],X[nd:],ref,c); gates=sciii_gates(ref,m,c,'natural')
    assert all(gates)
    assert m['phase_wraps']>8
    assert m['mode_overlap_median']>.95
    assert m['local_prediction_rms_median_rad']<.05

def test_local_eigenvector_gauge_is_removed_by_parallel_transport():
    c=cfg(); t=np.arange(0,24.0001,.02); X=moving_plane(t); nd=np.searchsorted(t,c['sciii_discovery_time']); ref=next(d for d in _discovery_candidates(t[:nd],X[:nd],c) if _q1(d,c)); m,q,loc=sciii_metrics(t[nd:],X[nd:],ref,c); phases=np.linspace(.2,2.5,len(loc)); m2,q2,_=sciii_metrics(t[nd:],X[nd:],ref,c,gauge_phases=phases)
    p=np.unwrap(np.angle(q)); p2=np.unwrap(np.angle(q2)); assert np.max(np.abs((p-p[0])-(p2-p2[0])))<1e-8
    assert abs(m['period']-m2['period'])<1e-8

def test_chirp_rejected_as_clock():
    c=cfg(); t=np.arange(0,24.0001,.02); w=2*np.pi/1.8; ph=w*t+.08*t*t; X=np.c_[np.cos(ph),np.sin(ph)]; nd=np.searchsorted(t,c['sciii_discovery_time']); ref=next(d for d in _discovery_candidates(t[:nd],X[:nd],c) if _q1(d,c)); m,_,_=sciii_metrics(t[nd:],X[nd:],ref,c); gates=sciii_gates(ref,m,c,'natural')
    assert gates[0] and gates[1]
    assert not gates[2]

def test_odd_channel_never_primary():
    c=cfg(); t=np.arange(0,24.0001,.02); X=moving_plane(t); nd=np.searchsorted(t,c['sciii_discovery_time']); ref=next(d for d in _discovery_candidates(t[:nd],X[:nd],c) if _q1(d,c)); m,_,_=sciii_metrics(t[nd:],X[nd:],ref,c); assert sciii_gates(ref,m,c,'odd')[-1] is False
