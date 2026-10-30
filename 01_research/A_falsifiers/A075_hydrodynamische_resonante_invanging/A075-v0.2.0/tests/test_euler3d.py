import hashlib,dataclasses
import numpy as np
import pytest
from experiment.euler3d import Config,Euler3D,curve,periodic_delta
from experiment.science import comparison

def test_centerline_closed_and_3d_trefoil():
    for k in ('0_1','3_1'):
        p,meta=curve(k,1.0,0.,nseg=48)
        assert p.shape==(48,3)
        assert np.min(np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1))>1.e-6
        assert np.isfinite(p).all()
    assert np.std(curve('3_1',1,0)[0][:,2])>0.1

def test_missing_twist_knot_fails_closed(tmp_path):
    for k in ('5_2','6_1'):
        with pytest.raises(FileNotFoundError):curve(k,.8,.6,xyz_root=str(tmp_path))

def test_3d_divergence_projection_and_energy():
    s=Euler3D(Config(n=20,final_time=.10,dt=.05))
    uh,info=s.initial_velocity()
    assert len(info)==3
    d=sum(s.k[j]*uh[...,j] for j in range(3))
    assert np.max(np.abs(d))<1e-7
    out=s.run()
    assert out['global_relative_energy_drift']<1e-7
    assert out['max_CFL']<.35

def test_control_volume_no_donor_identical():
    c=Config(n=20,final_time=.10,dt=.05,incoming=False)
    a=Euler3D(c).run(); b=Euler3D(c).run(center_track=a['center_track'])
    assert np.max([abs(x['E_window']-y['E_window']) for x,y in zip(a['timeseries'],b['timeseries'])]) < 1e-7
    cmp=comparison(a,b,1.0)
    assert abs(cmp['window_excess_final_J'])<1.e-7
    assert cmp['retention_qualified'] is False

def test_flux_sign_and_small_window_ledger():
    r=Euler3D(Config(n=24,final_time=.10,dt=.05)).run()
    assert np.isfinite(r['max_window_budget_residual_over_E0'])
    assert r['max_window_budget_residual_over_E0']<.003
    assert r['receiver_clock_qualified'] is False

def test_original_method_source_hashes():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    assert hashlib.sha256((root/'source_evidence'/'A021_README.md').read_bytes()).hexdigest()=='b615595589551dafbcabddc223e554abeb6ab5a02a064fa96522af73d533e3e9'
    assert hashlib.sha256((root/'source_evidence'/'A032_README.md').read_bytes()).hexdigest()=='e78411ee0a3a0cd770bd8293e117f44b1908bd419877b5163d5df21b71b9da0e'
