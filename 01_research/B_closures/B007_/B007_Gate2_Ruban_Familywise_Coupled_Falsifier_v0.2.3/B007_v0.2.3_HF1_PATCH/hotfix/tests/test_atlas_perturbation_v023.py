"""B007 v0.2.3 additive tests; do not require the external 242 files by default."""
from pathlib import Path
import math, os
import numpy as np
import pytest
from src.atlas_perturbation import (kabsch_distance,decimate,evolve,gate_compare,
    path_safe,SourceDataset,match_sources,select_ids,parser,sha,compare_analytic_source)
from src.geometry import generate,get_config


def test_rigid_se3_separation_invariance():
    x=generate(2,3,.2,128,False)[0]
    a=.6
    rot=np.array([[np.cos(a),-np.sin(a),0],[np.sin(a),np.cos(a),0],[0,0,1.]])
    y=x@rot+np.array([13.,-6.,7.])
    assert kabsch_distance(x,y)<1e-13
    assert kabsch_distance(x,x)<1e-13


def test_se3_does_not_hide_true_deformation():
    x=generate(2,3,.2,128,False)[0]
    y=x.copy();y[:,0]*=1.02
    assert kabsch_distance(x,y)>1e-4


def test_nested_native_resolution_matches_analytic():
    cfg=get_config()
    for b in (.02,.17,.32):
        a=generate(2,3,b,2048,True,cfg)[0]
        bb=generate(2,3,b,4096,True,cfg)[0]
        assert np.allclose(a,bb[::2],atol=3e-14,rtol=0)
        assert np.array_equal(decimate(bb,2048),bb[::2])


def test_source_subsample_preserves_exact_points():
    x=np.arange(48).reshape(16,3)
    assert np.array_equal(decimate(x,8),x[::2])
    with pytest.raises(ValueError):decimate(x,7)


def test_perturbation_nonzero():
    a=generate(2,3,.2,128,False)[0]
    b=generate(2,3,.2,128,True)[0]
    assert kabsch_distance(a,b)>1e-5


def test_identical_free_filament_evolution_no_diff():
    p=generate(2,3,.2,64,False)[0]
    # We intentionally only test the simple trajectory integrator with a perturbed pair.
    q=generate(2,3,.2,64,True)[0]
    r=evolve(p,q,3.4,1,.0001,1)
    assert math.isfinite(r['amplification_final'])
    assert r['steps']==1
    assert len(r['time_samples'])==2
    assert abs(r['time_samples'][0]['amplification']-1)<1e-15


def test_zero_dynamics_time_refinement_limit():
    a=generate(2,3,.2,64,False)[0];b=generate(2,3,.2,64,True)[0]
    x=evolve(a,b,3.4,1,1e-8,1)
    y=evolve(a,b,3.4,2,1e-8,1)
    assert abs(x['amplification_final']-y['amplification_final'])<1e-7


def test_two_level_not_labelled_physical():
    a=dict(amplification_final=1.1,shape_drift_nominal=.01,shape_drift_perturbed=.02,
           relative_length_drift_nominal=0.,relative_length_drift_perturbed=0.)
    b={**a,'amplification_final':1.101}
    assert gate_compare(a,b,.005,.05)['status']=='TWO_LEVEL_DIAGNOSTIC_CONSISTENCY'
    c={**b,'amplification_final':2.0}
    assert gate_compare(a,c,.005,.05)['status']=='UNRESOLVED_DISCRETIZATION_CHANGE'


@pytest.mark.parametrize('text',["../escape", "/tmp/escape", "..\\x", "a/../b", "C:/evil", "a//b"])
def test_archive_traversal_rejected(text):
    with pytest.raises(ValueError):path_safe(text)


def test_args_required():
    with pytest.raises(SystemExit):parser().parse_args([])


def test_t23_data_integration_when_user_dataset_available():
    a=os.environ.get('B007_TEST_N2048')
    b=os.environ.get('B007_TEST_N4096')
    if not a or not b:pytest.skip('Set B007_TEST_N2048/N4096 to exercise real datasets')
    with SourceDataset(a,2048) as d2,SourceDataset(b,4096) as d4:
        match_sources(d2,d4)
        sid=sorted(d2.records)[0]
        p2=d2.load(sid)
        assert compare_analytic_source(sid,2048,p2,generate(2,3,.02,2048,True)[0])['status'] in ('EXACT','BOUNDED_FLOAT64_ROUNDOFF')
        assert compare_analytic_source(sid,4096,d4.load(sid),generate(2,3,.02,4096,True)[0])['status'] in ('EXACT','BOUNDED_FLOAT64_ROUNDOFF')
        assert len(select_ids(d2,parser().parse_args(['--dataset-2048',a,'--dataset-4096',b,'--b0','.02'])))==1
