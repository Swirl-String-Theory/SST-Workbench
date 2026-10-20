"""Independent controls; historical seeds have no physical sample independence."""
from pathlib import Path
import numpy as np
from experiment.hasimoto import prepare, analytic, curvature_torsion, audit_case, suite, hash_audit
from experiment.gp3d import gp_step,reference_suite
ROOT=Path(__file__).resolve().parents[1]

def test_exact_bytes_sources():
    a=hash_audit(ROOT)
    assert all(len(v['sha256'])==64 and v['points']==1200 and v['source_xyz_vs_analytic_max_error']<1e-6 for v in a.values())

def test_four_seeds_and_finite_geometry():
    for kind in ('A','B'):
        for mirror in (False,True):
            s=prepare(kind,256,mirror)
            assert np.all(np.isfinite(s['q0'])) and np.min(s['kappa'])>.1
            assert np.linalg.norm(analytic(np.array([0,2*np.pi]),kind,mirror)[0][0]-analytic(np.array([0,2*np.pi]),kind,mirror)[0][1])<1e-12

def test_hasimoto_exact_parity_init():
    for kind in ('A','B'):
        a=prepare(kind);m=prepare(kind,mirror=True)
        assert abs(a['phi']+m['phi'])<1e-8
        assert np.linalg.norm(a['q0'].conj()-m['q0'])<1e-8

def test_orthogonal_geometries_not_exact_mirror():
    a=prepare('A');b=prepare('B');assert abs(a['L']-b['L'])>5.

def test_analytic_derivatives_consistent():
    for kind in ('A','B'):
        t=np.linspace(0,2*np.pi,50,endpoint=False);eps=1e-5
        deriv=analytic(t,kind)[1]
        numeric=(analytic(t+eps,kind)[0]-analytic(t-eps,kind)[0])/(2*eps)
        assert np.max(abs(deriv-numeric))<1e-8

def test_hasimoto_refinement_n256():
    assert suite(ROOT,steps=400,dt=.00025)['status']=='PASS'

def test_hasimoto_refinement_n384():
    assert suite(ROOT,n=384,steps=400,dt=.00025)['status']=='PASS'

def test_sweep_hasimoto_phase_not_a_physical_clock():
    assert all(not x['intrinsic_3d_clock_detected'] for x in suite(ROOT)['cases'])

def test_3d_gp_analytic_plane_wave_control():
    assert reference_suite()['status']=='PASS'
    assert reference_suite()['knotted_field_constructed'] is False

def test_gp_rejects_invalid_grid():
    import pytest
    with pytest.raises(ValueError):gp_step(np.zeros((3,8,8),complex),.001,1.)

def test_gp_zero_not_certified():
    assert not reference_suite()['physical_clock_prediction']


def test_hash_lock_rejects_corruption(tmp_path):
    import shutil,pytest
    from experiment.hasimoto import hash_audit
    # Copy frozen science pins, but perturb original geometry with a single byte.
    base=tmp_path/'sources'/'HISTORICAL_2015';base.mkdir(parents=True)
    shutil.copy2(ROOT/'science_contract.json',tmp_path/'science_contract.json')
    for f in (ROOT/'sources'/'HISTORICAL_2015').glob('*.xyz'):shutil.copy2(f,base/f.name)
    f=next(base.glob('A_*.xyz'));raw=f.read_bytes();f.write_bytes(raw[:-2]+b'00')
    with pytest.raises(ValueError,match='SHA256'):hash_audit(tmp_path)
