import json, math, tempfile
from pathlib import Path
import numpy as np

from sst_fourier_ideal_falsifier.model import CurveSet
from sst_fourier_ideal_falsifier.geometry import resample_closed, canonicalize, align_cyclic
from sst_fourier_ideal_falsifier.workflow import _metric_logratio, pair_decision
from sst_fourier_ideal_falsifier.reveal import binom_one_sided_ge
from sst_fourier_ideal_falsifier.seal import tree_records


def circle(n=64):
    t=np.linspace(0,2*np.pi,n,endpoint=False)
    return np.c_[np.cos(t),np.sin(t),np.zeros_like(t)]


def test_resample_and_canonicalize():
    c=resample_closed(circle(27),96)
    cs,meta=canonicalize(CurveSet.from_components([c]),1.0)
    assert cs.points.shape==(96,3)
    assert abs(np.sqrt(np.mean(np.sum(cs.points**2,axis=1)))-1.0)<1e-10
    assert meta['scale']>0


def test_alignment_removes_rigid_motion_and_shift():
    c=circle(80)
    th=0.7
    R=np.array([[np.cos(th),-np.sin(th),0],[np.sin(th),np.cos(th),0],[0,0,1.]])
    d=np.roll(c@R.T+np.array([2.,-1.,0.4]),13,axis=0)
    a=CurveSet.from_components([c]);b=CurveSet.from_components([d])
    _,dist,*_=align_cyclic(a,b,2)
    assert dist<1e-10


def test_infinite_metric_is_neutral_if_both_infinite():
    a={'rpo_residual':float('inf')};b={'rpo_residual':float('inf')}
    assert abs(_metric_logratio(a,b,'rpo_residual'))<1e-15


def test_infinite_metric_loses_to_finite():
    a={'rpo_residual':float('inf')};b={'rpo_residual':1.0}
    assert _metric_logratio(a,b,'rpo_residual')>0


def test_pair_decision_direction():
    cfg={'primary_metrics':['x','y','z'],'pair_tie_log_margin':math.log(1.03)}
    a={'x':.5,'y':.5,'z':.5};b={'x':1.,'y':1.,'z':1.}
    assert pair_decision(a,b,cfg)['winner_anonymous']=='A'


def test_exact_binomial_tail():
    assert binom_one_sided_ge(5,5)==1/32
    assert binom_one_sided_ge(0,5)==1.0


def test_tree_digest_detects_bytes():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'a.txt';p.write_text('a')
        h1,_=tree_records(td);p.write_text('b');h2,_=tree_records(td)
        assert h1!=h2


def test_shape_velocity_quotients_tangential_gauge():
    from sst_fourier_ideal_falsifier.geometry import shape_velocity,tangents
    c=circle(72);cs=CurveSet.from_components([c]);T=tangents(c)
    U=np.array([.2,-.1,.3]);Om=np.array([.0,.0,.7]);xc=c-c.mean(0)
    v=U+np.cross(np.broadcast_to(Om,c.shape),xc)+1.7*T
    w,Uh,Oh=shape_velocity(cs,v)
    assert np.sqrt(np.mean(np.sum(w*w,axis=1)))<1e-10


def test_exact_segment_gap_detects_crossing_between_vertices():
    from sst_fourier_ideal_falsifier.native import min_nonlocal_segment_distance
    # Two separate square-like components whose long segments cross at the origin.
    a=np.array([[-1,0,0],[1,0,0],[1,2,0],[-1,2,0]],float)
    b=np.array([[0,-1,0],[0,1,0],[2,1,0],[2,-1,0]],float)
    cs=CurveSet.from_components([a,b])
    assert min_nonlocal_segment_distance(cs.points,cs.offsets,1)<1e-12


def test_canonical_phase_orientation_removes_roll_and_reversal():
    from sst_fourier_ideal_falsifier.geometry import canonical_phase_orientation
    c=circle(73)
    a=canonical_phase_orientation(c)
    b=canonical_phase_orientation(np.roll(c[::-1],17,axis=0))
    assert np.sqrt(np.mean(np.sum((a-b)**2,axis=1)))<1e-12
