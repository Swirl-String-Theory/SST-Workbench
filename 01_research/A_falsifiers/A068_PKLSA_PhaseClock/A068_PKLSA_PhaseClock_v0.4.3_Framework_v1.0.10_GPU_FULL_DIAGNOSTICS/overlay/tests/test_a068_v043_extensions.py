"""A068 v0.4.3 independent science diagnostic and backend method tests."""
from pathlib import Path
import json
import numpy as np
import pytest
from experiment.euler3d import Euler3D
from experiment.material import sample_vector
from experiment.mesh_refinement import material_mesh_sweep,_advect_bundle
from experiment.vortex_seed import vortex_seed_from_curve,integrate_line
from experiment.floquet_independent import manufactured_arnoldi_oracle
from experiment.shooting import fixed_symmetry_shoot,double_return
from experiment.gpu_xpu import TorchEuler3D,torch_available,parity
from experiment.pipeline import source_audit

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'data/knot_3.1.txt'

def test_g1_new_code_hashes_and_external_a004():
    audit=source_audit(ROOT)
    assert audit['valid']
    files=audit['files']
    assert 'experiment/gpu_xpu.py' in files
    assert 'experiment/shooting.py' in files
    assert sum(k.startswith('A004/') and k.endswith('.xyz') for k in files)==40


def test_registered_gpu_matrix_and_science():
    a=json.loads((ROOT/'data/V043_REGISTERED_MATRIX.json').read_text())
    assert len(a['mesh_sweep']['FULL']['meshes'])==3
    assert a['gpu_parity']['steps']>=4
    assert a['screening_thresholds']['rpo_rel_full_velocity_max']==0.025
    science=json.loads((ROOT/'science_contract.json').read_text())
    assert {'E16','E17','E18','E19','E20','E21','E22'} <= {x['id'] for x in science['equations']}


def test_material_mesh_sweep_is_separate_from_euler_mesh():
    r=material_mesh_sweep(SRC,n=8,T=.08,dt=.04)
    assert len(r['history'])==3
    assert len(r['max_volume_drifts'])==3
    assert r['max_det_F_error']<.1
    assert r['embedded_surface_certified'] is False
    assert r['material_tube_qualified'] is False
    assert r['history'][0]['det_F_max_abs_error']<1e-12


def test_surface_bundle_preserves_exact_euler_rk4():
    g=Euler3D(8)
    rng=np.random.default_rng(2)
    U=g.project(rng.normal(size=(3,8,8,8)))
    s=rng.normal(size=(4,5,3));probes=rng.normal(size=(2,7,3))
    v,_,_= _advect_bundle(g,U,[s],probes,.04)
    w,_=g.rk4(U,np.empty((0,*U.shape)),.04)
    assert np.max(abs(v-w))<1e-12


def test_vortex_line_candidate_rejects_open_seed():
    x=vortex_seed_from_curve(SRC,n=8,sections=8,sides=4,length=2)
    assert x['traced'] is True
    assert x['closed_line_screen_pass'] is False
    assert x['vortex_tube_qualified'] is False


def test_constant_vorticity_line_is_straight():
    class G:
        dx=2*np.pi/8
        n=8
    G=G()
    field=np.zeros((3,8,8,8));field[2]=1
    line=integrate_line(G,field,[1,1,1],length=2*np.pi,steps=16)
    assert np.allclose(line[-1]-line[0],[0,0,2*np.pi],atol=1e-11)


def test_manufactured_floquet_not_physical():
    x=manufactured_arnoldi_oracle()
    assert x['oracle_pass']
    assert abs(x['omega_calculated']-1.75)<1e-12


def test_shooting_null_map_no_unwarranted_certification():
    g=Euler3D(8)
    z=np.zeros((3,8,8,8))
    r=fixed_symmetry_shoot(g,z,.04,2,np.eye(3,dtype=int),[0,0,0],iterations=1)
    assert r['screen_pass']
    assert r['rpo_certified'] is False
    assert r['period_optimized'] is False
    dr=double_return(g,z,.04,2,np.eye(3,dtype=int),[0,0,0])
    assert dr['first_return']==0 and dr['second_return']==0


def test_torch_cpu_oracle_3d_rk4_parity():
    pytest.importorskip('torch')
    g=Euler3D(8);rng=np.random.default_rng(42)
    u=g.project(rng.normal(size=(3,8,8,8)))
    result=parity(u,steps=4,device='cpu')
    assert result['parity_pass']
    assert result['relative_velocity_L2']<1e-12
    assert result['hardware_gpu_executed'] is False


def test_xpu_no_fallback_when_device_absent():
    if torch_available()['xpu_available']:
        pytest.skip('Real XPU found: absence-only test not applicable')
    g=Euler3D(8);u=g.project(np.random.default_rng(45).normal(size=(3,8,8,8)))
    output=parity(u,steps=1,device='xpu')
    assert output['status']=='UNAVAILABLE_NO_FALLBACK'
    assert output['hardware_gpu_executed'] is False
    assert output['actual_backend']=='UNAVAILABLE'


def test_torch_float32_is_screening_only():
    pytest.importorskip('torch')
    g=Euler3D(8);u=g.project(np.random.default_rng(12).normal(size=(3,8,8,8)))
    result=parity(u,steps=2,device='cpu',dtype='float32')
    assert result['relative_velocity_L2']<1e-4
    assert result['hardware_gpu_executed'] is False


def test_source_integrity_tamper_fail_closed(tmp_path):
    # Test code file must be hash protected. Avoid mutating the real overlay.
    from experiment.pipeline import _sha
    src=ROOT/'experiment/gpu_xpu.py'
    copied=tmp_path/src.name
    copied.write_bytes(src.read_bytes()+b'\n# modified\n')
    assert _sha(src)!=_sha(copied)

def test_dual_precision_gpu_campaign_cpu_oracle():
    pytest.importorskip('torch')
    from experiment.gpu_xpu import gpu_parity_campaign
    g=Euler3D(8);u=g.project(np.random.default_rng(51).normal(size=(3,8,8,8)))
    out=gpu_parity_campaign(u,dt=.04,steps=2,device='cpu')
    assert out['hardware_gpu_executed'] is False
    assert out['fp32_screen']['parity_pass']
    assert out['fp64_lane']['parity_pass']
    assert out['status']=='UNAVAILABLE_NO_FALLBACK'
