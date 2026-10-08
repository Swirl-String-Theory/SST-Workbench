from pathlib import Path
import gzip
import hashlib
import json
import numpy as np

from experiment.e011 import discover_static_ready_carriers, load_e011_geometry


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _circle(n=64, radius=1.0):
    a=np.linspace(0,2*np.pi,n,endpoint=False)
    return np.column_stack([radius*np.cos(a),radius*np.sin(a),np.zeros_like(a)])


def _write_xyz(path: Path, pts):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text('\n'.join('%.17g %.17g %.17g'%tuple(x) for x in pts)+'\n',encoding='utf8')


def _write_vect(path: Path, pts):
    path.parent.mkdir(parents=True,exist_ok=True)
    lines=['VECT',f'1 {len(pts)} 0',str(-len(pts)),'0']
    lines += ['%.17g %.17g %.17g'%tuple(x) for x in pts]
    path.write_text('\n'.join(lines)+'\n',encoding='utf8')


def _write_gilbert(path: Path):
    path.parent.mkdir(parents=True,exist_ok=True)
    txt='''<AB Id="3:1:1" L="6.283185307179586">\n<Coeff I="0" A="0,0,0" B="0,0,0"/>\n<Coeff I="1" A="2,0,0" B="0,2,0"/>\n</AB>\n'''
    with gzip.open(path,'wt',encoding='utf8') as f: f.write(txt)


def _seed(top,carrier,seed,provider,family,path,rep,geometry_sha,ref=None,lineage=None):
    raw=f'C:\\workspace\\projects\\SST-Workbench\\{path.relative_to(path.parents[3]).as_posix().replace("/", "\\\\")}'
    # parents[3] is the synthetic Workbench root for paths rooted under wb/03_data/...
    return {
      'static_ready':True,'evidence_class':'UPSTREAM_INDEPENDENT','seed_role':'PRIMARY_REFERENCE',
      'topology_id':top,'carrier_id':carrier,'static_seed_id':seed,'provider_group':provider,
      'source_family':family,'lineage_group':lineage or f'{provider}:{top}', 'method_group':family,
      'source_locator':{
        'source_path':raw,'raw_sha256':_sha(path),'geometry_sha256':geometry_sha,
        'reference_id':ref,'representation':rep,'source_family':family,
        'source_role':'independent_reference_geometry','status':'RESOLVABLE_FROM_WORKBENCH_SOURCE_METADATA'
      },
      'capabilities':{'writhe_ready':True,'acn_ready':True}
    }


def _setup(tmp_path, monkeypatch):
    wb=tmp_path/'wb'
    e011=wb/'01_research'/'E_pipelines'/'E011_sklsa_selected_knot_link_seed_atlas'/'E011-v0.3.0'
    out=e011/'E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs'; out.mkdir(parents=True)
    xyz=wb/'03_data'/'A_knots'/'04_knotplot'/'knot_3.1'/'a.txt'; _write_xyz(xyz,_circle(80,1.0))
    vect=wb/'03_data'/'A_knots'/'04_knotplot'/'knot_3.1'/'b.vect'; _write_vect(vect,_circle(96,1.1))
    gil=wb/'03_data'/'A_knots'/'01_ideal'/'ideal_sources'/'Ideal.txt.gz'; _write_gilbert(gil)
    # relative_to helper root assumed by _seed
    def win_seed(path, **kw):
        rel=path.relative_to(wb)
        raw='C:\\workspace\\projects\\SST-Workbench\\'+str(rel).replace('/','\\\\')
        d=_seed.__wrapped__ if hasattr(_seed,'__wrapped__') else None
    rows=[
      {
        'static_ready':True,'evidence_class':'UPSTREAM_INDEPENDENT','seed_role':'PRIMARY_REFERENCE','topology_id':'3_1',
        'carrier_id':'CAR_G','static_seed_id':'SEED_G','provider_group':'gilbert','source_family':'gilbert_ideal','lineage_group':'gilbert:3_1','method_group':'gilbert-fourier-ideal',
        'source_locator':{'source_path':'C:\\workspace\\projects\\SST-Workbench\\'+str(gil.relative_to(wb)).replace('/','\\\\'),'raw_sha256':_sha(gil),'geometry_sha256':'1'*64,'reference_id':'3:1:1','representation':'gilbert_ab_record','source_family':'gilbert_ideal','source_role':'independent_ideal_reference_geometry','status':'RESOLVABLE_FROM_WORKBENCH_SOURCE_METADATA'},
        'capabilities':{'writhe_ready':True,'acn_ready':True}
      },
      {
        'static_ready':True,'evidence_class':'UPSTREAM_INDEPENDENT','seed_role':'PRIMARY_REFERENCE','topology_id':'3_1',
        'carrier_id':'CAR_K1','static_seed_id':'SEED_K1','provider_group':'knotplot','source_family':'knotplot_relaxed','lineage_group':'knotplot:3_1:relaxation','method_group':'knotplot-relaxation',
        'source_locator':{'source_path':'C:\\workspace\\projects\\SST-Workbench\\'+str(xyz.relative_to(wb)).replace('/','\\\\'),'raw_sha256':_sha(xyz),'geometry_sha256':'2'*64,'reference_id':None,'representation':'xyz','source_family':'knotplot_relaxed','source_role':'relaxed_reference_geometry','status':'RESOLVABLE_FROM_WORKBENCH_SOURCE_METADATA'},
        'capabilities':{'writhe_ready':True,'acn_ready':True}
      },
    ]
    row3=json.loads(json.dumps(rows[1])); row3['carrier_id']='CAR_K2'; row3['static_seed_id']='SEED_K2'; row3['source_locator']['source_path']='C:\\workspace\\projects\\SST-Workbench\\'+str(vect.relative_to(wb)).replace('/','\\\\'); row3['source_locator']['raw_sha256']=_sha(vect); row3['source_locator']['geometry_sha256']='3'*64; row3['source_locator']['representation']='vect'
    summary={'schema':'E011-SKLSA-STATIC-READY-ATLAS-1','e011_version':'0.3.0','e010_release_version':'0.3.1','execution_gate':'PASS','operational_error_count':0,'static_ready_topology_count':1,'provider_anchor_count':2,'primary_static_seed_count':3,'cross_provider_robust_topology_count':1,'cross_provider_sensitive_topology_count':0,'single_provider_qualified_topology_count':0,'scientific_boundary':'static geometry only'}
    seed_schema={'schema':'E011-STATIC-SEED-CONTRACT-1','atlas_version':'0.3.0','dynamics_ready':False}
    parent={'schema':'E010-PKLSA-PRODUCTION-KNOT-LINK-BASIS-1','e010_version':'0.3.1','full_campaign_gate_pass':False,'publication_ready_geometry_layer':False,'source_contract_gate_pass':True,'topology_database_ingest_gate_pass':True,'identity_database_gate_pass':True,'canonical_identity_admission_gate_pass':True}
    (out/'RUN_SUMMARY.json').write_text(json.dumps(summary),encoding='utf8')
    (out/'SEED_CONTRACT_SCHEMA.json').write_text(json.dumps(seed_schema),encoding='utf8')
    (out/'PARENT_RELEASE.json').write_text(json.dumps(parent),encoding='utf8')
    (out/'STATIC_READY_PROVIDER_ANCHORS.jsonl').write_text('\n'.join(json.dumps(x) for x in rows)+'\n',encoding='utf8')
    (out/'STATIC_READY_PRIMARY_SEEDS.jsonl').write_text('\n'.join(json.dumps(x) for x in rows+[row3])+'\n',encoding='utf8')
    monkeypatch.setenv('SST_WORKBENCH_ROOT',str(wb))
    return wb


def test_e011_full_uses_provider_anchors_even_when_parent_not_publication_ready(tmp_path, monkeypatch):
    _setup(tmp_path,monkeypatch)
    root=Path(__file__).resolve().parents[1]
    carriers,meta=discover_static_ready_carriers(root,'FULL')
    assert meta['e011_execution_gate']=='PASS'
    assert meta['parent_publication_ready_geometry_layer'] is False
    assert meta['parent_full_campaign_gate_pass'] is False
    assert meta['selected_manifest']=='STATIC_READY_PROVIDER_ANCHORS.jsonl'
    assert len(carriers)==2
    assert {c.provider_group for c in carriers}=={'gilbert','knotplot'}
    for c in carriers:
        comps=load_e011_geometry(c)
        assert len(comps)==1 and len(comps[0])>=64


def test_e011_certify_uses_all_primary_static_ready_carriers(tmp_path, monkeypatch):
    _setup(tmp_path,monkeypatch)
    root=Path(__file__).resolve().parents[1]
    carriers,meta=discover_static_ready_carriers(root,'CERTIFY')
    assert meta['selected_manifest']=='STATIC_READY_PRIMARY_SEEDS.jsonl'
    assert len(carriers)==3
    vect=[c for c in carriers if c.representation=='vect'][0]
    assert len(load_e011_geometry(vect)[0])==96
