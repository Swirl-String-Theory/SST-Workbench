import json
import numpy as np
import pytest
from euler_extension.spectral import SpectralEuler3D,init_knotted_tube,evolve
from euler_extension.cli import build_one,validate,_paths,ROOT

def test_abc_beltrami_stationary_euler():
    sol=SpectralEuler3D(16)
    x=(np.arange(16)-8)*sol.dx
    X,Y,Z=np.meshgrid(x,x,x,indexing='ij')
    v=np.stack([np.sin(Z)+np.cos(Y),np.sin(X)+np.cos(Z),np.sin(Y)+np.cos(X)],axis=-1)
    assert np.max(np.abs(sol.curl(v)-v))<2e-14
    assert np.max(np.abs(sol.rhs(v)))<2e-13
    vv=sol.rk4(v,.03)
    assert np.max(np.abs(vv-v))<3e-13

def test_divergence_energy_helix():
    solver=SpectralEuler3D(16)
    pts=np.loadtxt(ROOT/'data'/'PKLSA_RAW_NATIVE_UNQUALIFIED'/'knot_3.1.txt')
    v,_=init_knotted_tube(solver,pts)
    assert solver.diagnostics(v)['divergence_max_dimensionless']<1e-12
    assert np.max(np.abs(solver.rhs(v)))>1e-3
    t,frames,d=evolve(solver,v,duration=.08,frame_count=3)
    assert len(t)==len(frames)==3
    assert np.linalg.norm(frames[-1]-frames[0])>1e-4
    assert d['max_energy_rel_drift']<1e-5
    assert d['max_helicity_rel_drift']<1e-5

def test_euler_step_refinement():
    solver=SpectralEuler3D(16)
    pts=np.loadtxt(ROOT/'data'/'PKLSA_RAW_NATIVE_UNQUALIFIED'/'knot_5.2.txt')
    v,_=init_knotted_tube(solver,pts)
    coarse=solver.rk4(v,.025)
    half=solver.rk4(solver.rk4(v,.0125),.0125)
    quarter=v.copy()
    for _ in range(4):quarter=solver.rk4(quarter,.00625)
    ec=np.linalg.norm(coarse-half)
    ef=np.linalg.norm(half-quarter)
    assert ec>ef*5

def test_source_classifier_and_hashed_npz(tmp_path,monkeypatch):
    from a064.flow import SnapshotFlow
    # Don't overwrite packaged model; use copy in temporary folder
    import shutil
    origsrc,out=_paths('3_1')
    if not out.exists():build_one('3_1')
    shadow=tmp_path/out.name
    shutil.copyfile(out,shadow)
    shutil.copyfile(out.with_suffix('.source.json'),shadow.with_suffix('.source.json'))
    f=SnapshotFlow(shadow)
    assert f.evidence_class=='geometry_initialized_periodic_3d_euler_model'
    z=np.load(shadow,allow_pickle=False)
    assert not np.array_equal(z['v'][0],z['v'][-1])
    with open(shadow,'ab') as ff:ff.write(b'X')
    with pytest.raises(ValueError,match='SHA-256'):SnapshotFlow(shadow)

def test_euler_metadata_is_not_independent_evidence():
    build_one('3_1')
    metadata=validate('3_1')
    assert not metadata['is_independent_measurement']
    assert not metadata['is_dynamics_ready']
    assert 'RAW_NATIVE_UNQUALIFIED' in metadata['geometry_provider']
    assert metadata['is_numerically_evolved']

def test_interpolated_flow_is_not_steady():
    from a064.flow import SnapshotFlow
    build_one('3_1')
    _,f=_paths('3_1');flow=SnapshotFlow(f)
    mid=tuple(np.mean(a) for a in flow.axes)
    from scipy.ndimage import map_coordinates
    assert np.max(abs(flow.v[0]-flow.v[-1]))>1e-4
    assert flow.times[-1] > flow.times[0]
