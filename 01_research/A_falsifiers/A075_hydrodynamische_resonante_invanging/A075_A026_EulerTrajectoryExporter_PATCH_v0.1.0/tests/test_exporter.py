import importlib.util
from pathlib import Path
import numpy as np

def module():
    p=Path(__file__).resolve().parents[1]/'export_a026_trajectories.py'
    spec=importlib.util.spec_from_file_location('exporter',p)
    a=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(a)
    return a

def test_seeds_are_distinct():
    seeds=np.random.SeedSequence(500).spawn(80)
    vals=[np.random.default_rng(s).normal() for s in seeds]
    assert len(set(vals))==80

def test_rk4_marker_linear_exact():
    # For a spatially constant velocity field, dX/dt=v is solved exactly.
    m=module()
    class Constant:
        def rhs(self,uh):return np.zeros_like(uh)
        def probe_u(self,uh,pos):return np.array([3.,-2.,1.])
        def project(self,x):return x
    uh=np.ones((1,1,1,3),dtype=complex)
    x=np.array([1.,2.,3.]);dt=.125
    u,z=m.rk4_field_marker(Constant(),uh,x,dt)
    assert np.array_equal(u,uh)
    assert np.allclose(z,[1.375,1.75,3.125],atol=1e-14)

def test_perturbation_nonzero_sourcefree():
    m=module()
    class Simple:
        c=type('cfg',(),{'n':4})
        k2=np.ones((4,4,4))
        def project(self,x):return x
        def fft(self,x):return np.fft.fftn(x,axes=(0,1,2))
    u=np.ones((4,4,4,3),dtype=complex)
    out=m.seeded_perturbation(Simple(),u,np.random.default_rng(4),.02,.2)
    assert np.isfinite(out).all() and np.linalg.norm(out-u)>0

def test_mismatched_source_refused(tmp_path):
    m=module()
    p=tmp_path/'experiment';p.mkdir()
    (p/'euler3d.py').write_text('invalid file')
    (p/'ruban.py').write_text('invalid file')
    try:
        m.checksum_manifest(tmp_path)
    except RuntimeError as ex:
        assert 'A075_SOURCE_DRIFT' in str(ex)
    else:
        raise AssertionError('Source drift must be refused')


def test_metadata_format_validator(tmp_path):
    p=Path(__file__).resolve().parents[1]/'validate_a026_npz.py'
    spec=importlib.util.spec_from_file_location('format_validator',p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    import json
    from numpy.random import default_rng
    rng=default_rng(17)
    n=80;t=12
    s=rng.normal(0,.01,n)
    times=np.linspace(0,1,t)
    q=s[:,None]*np.sin(2*times)[None,:]
    vel=2*s[:,None]*np.cos(2*times)[None,:]
    meta={x:'fixture' for x in ('solver_name','solver_revision','source_manifest_sha256',
                                  'geometry_manifest_sha256','observable_definition','core_model','boundary_conditions')}
    f=tmp_path/'sample.npz'
    np.savez_compressed(f,times_s=times,q_m=q,qdot_m_s=vel,
                        trial_ids=np.asarray([f'trial_{i}' for i in range(n)]),
                        metadata_json=np.asarray(json.dumps(meta)))
    assert m.validate(f)['format']=='PASS_NOT_PHYSICS_CERTIFICATION'
