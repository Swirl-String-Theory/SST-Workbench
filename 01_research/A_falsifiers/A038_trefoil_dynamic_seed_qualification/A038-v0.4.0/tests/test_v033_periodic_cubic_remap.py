import numpy as np
from sst_seed_falsifier.geometry import segment_lengths, resample_closed_periodic_cubic
from sst_seed_falsifier.metrics import shape_distance


def trefoil(n=256,R=2.0,a=.6,b=.4):
    t=np.linspace(0,2*np.pi,n,endpoint=False)
    return np.c_[(R+a*np.cos(3*t))*np.cos(2*t),(R+a*np.cos(3*t))*np.sin(2*t),b*np.sin(3*t)]


def test_periodic_cubic_preserves_phase_anchor_and_uniformizes_edges():
    x=trefoil(96)
    # deliberately distort the marker parametrisation while preserving ordering
    idx=np.floor((np.linspace(0,1,96,endpoint=False)**1.7)*96).astype(int)
    idx=np.maximum.accumulate(idx)
    # use a smooth nonuniform analytic sampling instead of duplicated indices
    u=np.linspace(0,1,96,endpoint=False)**1.7
    t=2*np.pi*u
    x=np.c_[(2+.6*np.cos(3*t))*np.cos(2*t),(2+.6*np.cos(3*t))*np.sin(2*t),.4*np.sin(3*t)]
    cv0=segment_lengths(x).std()/segment_lengths(x).mean()
    y=resample_closed_periodic_cubic(x,len(x))
    cv1=segment_lengths(y).std()/segment_lengths(y).mean()
    assert np.allclose(y[0],x[0],rtol=0,atol=1e-14)
    assert cv1 < 0.05*cv0


def test_periodic_cubic_remap_shape_error_decreases_with_resolution():
    errs=[]
    for n in (32,64,128):
        x=trefoil(n)
        y=resample_closed_periodic_cubic(x,n)
        errs.append(shape_distance(y,x,1))
    assert errs[2] < errs[1] < errs[0]
    assert errs[-1] < 5e-3
