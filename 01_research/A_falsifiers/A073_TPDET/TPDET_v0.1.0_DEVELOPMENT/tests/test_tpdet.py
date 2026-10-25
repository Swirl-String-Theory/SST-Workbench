import hashlib, json, sys
from pathlib import Path
import numpy as np
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tpdet import load_source, ring, hamiltonian, linking_matrix, run, blind, native_available
from euler_energy_flux import control


def test_seed_source_provenance():
    manifest=json.loads((ROOT/'references/provenance.json').read_text())
    for case,field,name in (
        ('trefoil_3_1','raw_sha256','trefoil_3_1_source.xyz'),
        ('torus_2_5','cache_sha256','torus_2_5_native.npz'),
        ('borromean_ideal','cache_sha256','borromean_ideal_native.npz'),
    ):
        p=ROOT/'seeds'/name
        assert p.exists()
        assert hashlib.sha256(p.read_bytes()).hexdigest()==manifest[case][field]


def test_all_seed_shapes():
    for label,expected in [('analytic_leapfrog',2),('trefoil_3_1',2),('torus_2_5',2),('borromean_ideal',4)]:
        cs,gg,_=load_source(label,32)
        assert len(cs)==expected==len(gg)
        assert all(x.shape==(32,3) and np.isfinite(x).all() for x in cs)


def test_hamiltonian_translation_invariance():
    cs=[ring(48,.9,-.2),ring(48,1.1,.2)]
    hh,_,_,_=hamiltonian(cs,[1.,1.],.12)
    tr=np.array([14.8,-9.1,10.0])
    hh2,_,_,_=hamiltonian([x+tr for x in cs],[1.,1.],.12)
    assert np.isclose(hh,hh2,rtol=2e-13)


def test_control_velocity_reversal_energy():
    cs=[ring(48,.9,-.2),ring(48,1.1,.2)]
    h1,_,_,_=hamiltonian(cs,[1,1],.12)
    h2,_,_,_=hamiltonian(cs,[-1,-1],.12)
    assert np.isclose(h1,h2,rtol=1e-13)


def test_baseline_position_swaps_not_flux():
    res=run('analytic_leapfrog',64,.03,4.,.12,10)
    assert res['completed_horizon']
    assert res['leapfrog_swaps']>=2
    assert res['energy_drift']<1e-3
    assert res['gates']['G7_blind_directed_Euler_flux']=='NOT_RUN'


def test_exact_affine_euler_energy_flux():
    for t in [0.,.5,1.]:
        r=control(t)
        assert r['relative_energy_balance_residual']<1e-7
        assert r['status'].startswith('PASS')


def test_blind_seal_no_leak_and_immutable(tmp_path):
    root=tmp_path/'fixed'
    rows=blind(root,32,.06,.18,.12,1)
    assert len(rows)==4
    mapping=json.loads((root/'SEALED/mapping.json').read_text())['mapping']
    assert set(mapping)=={r['blind_id'] for r in rows}
    for p in (root/'BLIND').glob('BX_*.json'):
        data=json.loads(p.read_text())
        for k in ('case','geometry_mode','components','gamma','leapfrog_swaps','swap_times','initial_links_proxy','final_links_proxy'):
            assert k not in data
        assert data['gates']['G9_topology_certification']=='WITHHELD_UNTIL_REVEAL'
        assert 'z_centroids' not in json.dumps(data['history'])
    with pytest.raises(FileExistsError):blind(root,32,.06,.18,.12,1)


def test_exact_polygon_crossing_detector():
    from segment_geometry import segment_pair_distance
    # Crossing two straight edges (non-coplanar except at their intersection).
    a=np.array([[-1.,0.,0.],[1.,0.,0.],[1.,2.,1.],[-1.,2.,1.]])
    b=np.array([[0.,-1.,0.],[0.,1.,0.],[2.,1.,1.],[2.,-1.,1.]])
    assert segment_pair_distance(a,b)<1.e-12
    assert segment_pair_distance(a,b+np.array([0.,0.,3.]))>1.
