import numpy as np
from sst_gfcc_blind.temporal import memory_metrics, shuffled_memory_null
from sst_gfcc_blind.geometry import make_curve
from sst_gfcc_blind.modes import bishop_frame, kabsch_align, transverse_mode_series
from sst_gfcc_blind.floquet import detect_return


def test_memory_detects_colored_sequence():
    rng=np.random.default_rng(4); n=160; p=12; x=np.zeros((n,p)); e=rng.normal(size=(n,p))
    for i in range(1,n): x[i]=0.85*x[i-1]+e[i]
    real=memory_metrics(x,1.0,max_lag=20); null=shuffled_memory_null(x,1.0,8,rng,max_lag=20)
    assert real['memory_steps'] > null['memory_steps_mean']
    assert real['lag1'] > null['lag1_mean']


def test_bishop_frame_orthogonal():
    p=make_curve('G0002',64,1); t,n,b=bishop_frame(p)
    assert np.max(np.abs(np.sum(t*n,axis=1))) < 1e-8
    assert np.max(np.abs(np.sum(t*b,axis=1))) < 1e-8
    assert np.max(np.abs(np.sum(n*b,axis=1))) < 1e-8


def test_transverse_mode_recovers_synthetic_mode():
    p=make_curve('G0001',64,1); t,n,b=bishop_frame(p); s=np.arange(len(p)); m=4; ph=2*np.pi*m*s/len(p)
    q=p+0.03*(np.cos(ph)[:,None]*n+np.sin(ph)[:,None]*b)
    modes,c=transverse_mode_series([p,q],p,2,8)
    best=int(modes[np.argmax(np.abs(c[1]))])
    assert best==m


def test_return_detector_requires_departure():
    p=make_curve('G0001',32,1)
    r=detect_return([p.copy() for _ in range(12)],{'departure_residual_min':0.01,'min_return_steps':3,'max_return_steps':10,'return_residual_max':0.1})
    assert r['status']=='INDETERMINATE_NO_DEPARTURE'
