"""Imported Borromean-source regression: provenance-first, NOT isotopy certification."""
import hashlib,json
from pathlib import Path
import numpy as np
import pytest
from src.external_links import get_registry,REGISTRY,DATADIR,read_xyz,normalized_parts,generate_imported,gauss_midpoint
from src.pipeline import create_parser,selected_families,values,stage1,stage2
from src.geometry import get_config,metrics
from src.filaments import quotient_distance,run_pair

def test_four_named_families():
    r=get_registry()
    assert set(r)=={'BORRO_FLAT','BORRO_BALANCED','BORRO_5_5_6_TIGHT','BORRO_6_6_5_SOFT'}

def test_exact_sha256_sources():
    for k,v in get_registry().items():
        for name in ('original','reference'):
            if v.get(name):
                p=DATADIR/v[name]
                assert hashlib.sha256(p.read_bytes()).hexdigest()==v[name+'_sha256']

def test_distinct_closed_components_and_actual_counts():
    expected={'BORRO_FLAT':[38,34,33],'BORRO_BALANCED':[38,34,33],
              'BORRO_5_5_6_TIGHT':[2275,2109,2048],
              'BORRO_6_6_5_SOFT':[2229,2067,2048]}
    for name in get_registry():
        parts,meta=normalized_parts(name)
        assert len(parts)==3 and [len(a) for a in parts]==expected[name]
        assert metrics(parts)['minimum_sampled_intercomponent_distance']>0
        assert np.isclose(np.max(np.linalg.norm(np.concatenate(parts),axis=1)),1,atol=1e-12)

def test_reference_resolution_provenance():
    for name,source_n in [('BORRO_5_5_6_TIGHT',[1137,1054,1024]),('BORRO_6_6_5_SOFT',[1114,1033,1024])]:
        _,x=generate_imported(name,64,reference=True)
        assert x['source_points']==source_n and x['source_variant']=='reference'

def test_perturbation_not_identity():
    orig,_=generate_imported('BORRO_BALANCED',64)
    pert,_=generate_imported('BORRO_BALANCED',64,perturbed=True)
    assert quotient_distance(orig,pert)>1e-8

def test_pairwise_gauss_small_but_no_milnor_claim():
    for name in ('BORRO_BALANCED','BORRO_FLAT'):
        p,meta=generate_imported(name,128)
        g=gauss_midpoint(p,64)
        assert max(abs(x) for x in g)<0.1
        assert meta['milnor_mu123']=='UNRESOLVED'

def test_custom_parameter_scan_has_no_b0():
    args=create_parser().parse_args(['--family','BORRO_BALANCED','--profile','fine'])
    names=selected_families(args,get_config())
    assert len(names)==1 and names['BORRO_BALANCED']['kind']=='external_link'

def test_imported_geom_and_filament_minimal(tmp_path):
    cfg=get_config()
    args=create_parser().parse_args(['--family','BORRO_BALANCED','--lambda-values','3.4','--screen-points','64','--screen-steps','1','--final-time','.0003'])
    sel=selected_families(args,cfg);bb,ll=values(args,cfg)
    geom,gate=stage1(sel,bb,tmp_path,args,cfg)
    assert len(geom)==1 and geom[0]['B0'] is None
    assert gate['imported_custom_families']==1
    rows,_=stage2(sel,bb,ll,tmp_path,args,cfg)
    assert len(rows)==1 and rows[0]['source_kind']=='IMPORTED_CUSTOM_3_COMPONENT'

def test_original_1024_is_not_actual_1024_per_component():
    r=get_registry()['BORRO_6_6_5_SOFT'];p=read_xyz(DATADIR/r['reference'])
    assert [len(x) for x in p]==[1114,1033,1024]


def test_external_source_reference_selection():
    args=create_parser().parse_args(['--family','BORRO_5_5_6_TIGHT','--external-source','reference'])
    assert args.external_source=='reference'
    p,info=generate_imported('BORRO_5_5_6_TIGHT',64,reference=True)
    assert info['source_variant']=='reference'

def test_missing_reference_refused():
    with pytest.raises(ValueError,match='no N1024 source reference'):
        generate_imported('BORRO_FLAT',128,reference=True)

def test_kind_borromean_four_and_torus_six():
    cfg=get_config()
    a=create_parser().parse_args(['--kind','borromean'])
    b=create_parser().parse_args(['--kind','torus-links'])
    assert len(selected_families(a,cfg))==4
    assert len(selected_families(b,cfg))==6
