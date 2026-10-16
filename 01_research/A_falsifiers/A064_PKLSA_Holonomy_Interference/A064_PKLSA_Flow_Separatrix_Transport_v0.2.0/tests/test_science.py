from pathlib import Path
import json
import numpy as np
import pytest
from a064.flow import FilamentFlow,SnapshotFlow,AnalyticFlow
from a064.analysis import curl_div,field_data,candidate_discovery,transport_audit,run


def axes(n=27):return tuple(np.linspace(-2.1,2.1,n) for _ in range(3))

def test_curl_div_solid_body():
    a=axes(11);p=np.stack(np.meshgrid(*a,indexing='ij'),-1)
    v=np.stack([-2*p[...,1],2*p[...,0],np.zeros_like(p[...,0])],-1)
    curl,div=curl_div(v,a)
    assert np.max(abs(div))<1e-12
    assert np.max(abs(curl[...,2]-4))<1e-12


def test_material_feature_and_leaky_null():
    a=axes()
    for kind in ('material','leaky'):
        f=AnalyticFlow(kind,speed=.28)
        _,s0,_=field_data(f,a,0.)
        c,alt,err=candidate_discovery(a,s0)
        assert c is not None and c['is_watertight']
        v=transport_audit(f,a,c,s0,s0,0.,.3,nseeds=80)
        assert v['status']=='MEASURED'
        if kind=='material':
            assert v['flux_p95_over_U']<.03
            assert v['tracer_cross_fraction']<.03
        else:
            assert v['flux_p95_over_U']>.08
            assert v['tracer_cross_fraction']>.07


def test_no_candidate_uniform_velocity():
    f=AnalyticFlow('none');_,s,_=field_data(f,axes(),0.)
    c,_,reason=candidate_discovery(axes(),s)
    assert c is None
    assert reason=='zero_or_nonfinite_vorticity'


def test_three_dimensional_geometry_and_dimensions():
    pts=np.array([[np.cos(t),np.sin(t),0] for t in np.linspace(0,2*np.pi,64,endpoint=False)])
    f=FilamentFlow(pts,.2,2.)
    x=np.array([[0.,0.,.5],[0.,0.,1.]])
    v=f.velocity(x)
    assert v.shape==(2,3) and np.all(np.isfinite(v))
    assert v[0,2]>0
    # v ~ Gamma / L; multiplying all lengths by 3 at fixed circulation makes v / 3.
    assert np.allclose(FilamentFlow(pts*3,.6,2.).velocity(x*3),v/3,rtol=1e-12)


def test_snapshot_shape_validation(tmp_path):
    a=axes(11);xx=np.stack(np.meshgrid(*a,indexing='ij'),-1)
    v=np.stack([-xx[...,1],xx[...,0],xx[...,2]*0],axis=-1)
    path=tmp_path/'demo.npz';np.savez_compressed(path,x=a[0],y=a[1],z=a[2],t=np.array([0.,.1]),v=np.array([v,v]))
    flow=SnapshotFlow(path)
    assert flow.velocity([[.1,.2,.3]],.05).shape==(1,3)
    assert np.allclose(flow.velocity([[0,1,0]],.05),[[-1,0,0]],atol=1e-12)


def test_discovery_seal_not_transport_selected(tmp_path):
    flow=AnalyticFlow('material',speed=.28)
    res=run(flow,axes(23),0,.2,tmp_path,'SYNTHETIC','analytical',skip_stagnation=True)
    disc=json.loads((tmp_path/'CANDIDATE_DISCOVERY.json').read_text())
    assert res['discovery_sha256'] and disc['accepted']
    assert 'flux' not in json.dumps(disc).lower()
    assert res['true_separatrix_manifold_gate'].startswith('UNRESOLVED')
    assert 'NOT_RUN_IN_THIS_PROTOTYPE' in res['framework']


def test_unqualified_xyz_input_has_no_static_authority():
    p=Path(__file__).resolve().parents[1]/'data/PKLSA_RAW_NATIVE_UNQUALIFIED'
    for name in ('knot_3.1.txt','knot_5.2.txt','knot_6.1.txt'):
        v=np.loadtxt(p/name)
        assert v.shape[1]==3 and len(v)>=30


def test_potential_strain_saddle_not_automatically_no_separatrix(tmp_path):
    f=AnalyticFlow('strain')
    r=run(f,axes(23),0.,.2,tmp_path,'SYNTHETIC','irrotational_strain',skip_stagnation=False)
    assert not r['candidate_detected']
    assert 'HYPERBOLIC' in r['dynamical_feature_status']
    assert any(x['hyperbolic_saddle'] for x in r['hyperbolic_stagnation_candidates'])
    assert 'UNRESOLVED' in r['overall_scientific_gate']


def test_builder_round_trip_and_reuse(tmp_path):
    from a064.build_npz import build_one,validate_existing,EVIDENCE
    xyz=Path(__file__).resolve().parents[1]/'data/PKLSA_RAW_NATIVE_UNQUALIFIED/knot_3.1.txt'
    dst=tmp_path/'source.npz'
    # Small grid is sufficient for the source-loader contract, not for physics gates.
    a=build_one(xyz,dst,1.,.8,10.,21,.14,3,'TEST_NOT_PHYSICAL')
    assert a['status']=='BUILT'
    with np.load(dst) as f:
        assert f['v'].shape==(3,21,21,21,3)
        assert np.array_equal(f['v'][0],f['v'][-1])
        assert str(f['source_type'])==EVIDENCE
    b=build_one(xyz,dst,1.,.8,10.,21,.14,3,'TEST_NOT_PHYSICAL')
    assert b['status']=='VERIFIED_EXISTING'
    flow=SnapshotFlow(dst)
    assert flow.evidence_class==EVIDENCE
    assert flow.source_metadata['is_physical_euler_evolution'] is False
    assert validate_existing(dst,xyz,dict(scale_m_per_unit=1.,core_m=.8,gamma_m2_s=10.,grid=21,
         duration_s=.14,time_frames=3,calibration='TEST_NOT_PHYSICAL'))


def test_builder_sidecar_tamper_detected(tmp_path):
    from a064.build_npz import build_one
    xyz=Path(__file__).resolve().parents[1]/'data/PKLSA_RAW_NATIVE_UNQUALIFIED/knot_3.1.txt'
    dst=tmp_path/'corrupt.npz'
    build_one(xyz,dst,1.,.8,10.,21,.14,3,'TEST_NOT_PHYSICAL')
    meta=dst.with_suffix('.source.json')
    j=json.loads(meta.read_text());j['npz_sha256']='bad'
    meta.write_text(json.dumps(j))
    with pytest.raises(ValueError,match='SHA-256 mismatch'):
        SnapshotFlow(dst)


def test_bundled_npz_selfcontained_and_not_upcast():
    from a064.flow import file_hash
    root=Path(__file__).resolve().parents[1]
    for name in ('3_1','5_2','6_1'):
        path=root/'data/MODEL_NPZ'/f'PKLSA_{name}_stationary_BS_DEMO.npz'
        side=path.with_suffix('.source.json')
        assert path.is_file() and side.is_file()
        meta=json.loads(side.read_text())
        assert meta['npz_sha256']==file_hash(path)
        assert meta['is_physical_euler_evolution'] is False
        assert meta['source_xyz_sha256']==file_hash(root/'data/PKLSA_RAW_NATIVE_UNQUALIFIED'/f'knot_{name.replace("_",".")}.txt')
        flow=SnapshotFlow(path)
        assert flow.evidence_class.startswith('geometry_derived_')
        assert flow.v.shape==(3,31,31,31,3)
