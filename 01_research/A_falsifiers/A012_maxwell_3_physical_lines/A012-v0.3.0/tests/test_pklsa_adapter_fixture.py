import json,hashlib,sys,gzip
from pathlib import Path
import numpy as np
from sst_maxwell3_blind.pklsa_adapter import PKLSARepository

def geom_hash(comps):
    h=hashlib.sha256(); h.update(b'PKLSA-GEOMETRY-SHA256-v1\0')
    for c in comps:
        a=np.asarray(c,dtype='<f8',order='C'); h.update(np.asarray(a.shape,dtype='<i8').tobytes()); h.update(a.tobytes(order='C'))
    return h.hexdigest()

def _clear_pklsa_modules():
    for name in list(sys.modules):
        if name == 'pklsa_builder' or name.startswith('pklsa_builder.'):
            sys.modules.pop(name, None)

def _write_common_pkg(pkg):
    pkg.mkdir(parents=True); (pkg/'__init__.py').write_text('')
    (pkg/'hashing.py').write_text('''import hashlib,numpy as np\ndef geometry_sha256(components):\n h=hashlib.sha256();h.update(b"PKLSA-GEOMETRY-SHA256-v1\\0")\n for c in components:\n  a=np.asarray(c,dtype="<f8",order="C");h.update(np.asarray(a.shape,dtype="<i8").tobytes());h.update(a.tobytes(order="C"))\n return h.hexdigest()\n''')
    (pkg/'gilbert.py').write_text('''import numpy as np\ndef find_gilbert_record(path,canonical_id):\n return {"canonical_id":canonical_id}\ndef sample_gilbert_components(record,n=4096):\n t=np.linspace(0,2*np.pi,int(n),endpoint=False)\n return [np.c_[np.cos(t),np.sin(t),np.zeros_like(t)]]\n''')

def _write_release(out, topology_count=1):
    out.mkdir()
    release={k:True for k in ['source_native_mode','source_contract_gate_pass','a001_a008_coverage_gate_pass','canonical_identity_admission_gate_pass','identity_database_gate_pass','topology_database_ingest_gate_pass','unregistered_source_gate_pass']}
    release.update({'e010_version':'0.3.1','full_campaign_gate_pass':False,'publication_ready_geometry_layer':False,'topology_count':topology_count,'failed_topology_count':0})
    (out/'RELEASE.json').write_text(json.dumps(release))

def _write_topology(out,topology,carrier_id,catalog_id,source_family,provider,method,lineage,group,representation,source_path,raw,gh,reach=0.1):
    td=out/'atlas'/topology; (td/'qualification').mkdir(parents=True); (td/'sources').mkdir()
    (td/'qualification/summary.json').write_text(json.dumps({'qualification_gate_pass':True,'topology_id':topology}))
    (td/'qualification/geometry_metrics.json').write_text(json.dumps({'carriers':[{'carrier_id':carrier_id,'catalog_id':catalog_id,'source_family':source_family,'literature_hard_gate_pass':True,'finest_resolution':4096,'finest_metrics':{'reach':reach,'thickness':2*reach},'observable_status':{'reach':'RESOLVED'},'scale_context':{'normalization_scale':1.0}}]}))
    (td/'qualification/source_independence.json').write_text(json.dumps({'entries':[{'carrier_id':carrier_id,'provider_group':provider,'method_group':method,'lineage_group':lineage,'independence_group':group,'evidence_independence_class':'UPSTREAM_REFERENCE','raw_duplicate_of':None,'geometry_duplicate_of':None}]}))
    env={'carrier':{'carrier_id':carrier_id,'catalog_id':catalog_id,'topology_id':topology,'source_family':source_family,'source_role':'independent_ideal_reference_geometry' if provider=='gilbert' else 'geometry','representation':representation,'source_path':str(source_path),'raw_sha256':raw},'geometry_sha256':gh}
    (td/'sources'/f'{carrier_id}.json').write_text(json.dumps(env))

def test_minimal_pklsa_fixture(tmp_path):
    _clear_pklsa_modules()
    wb=tmp_path/'SST-Workbench'; (wb/'10_docs/registry').mkdir(parents=True)
    rr=wb/'01_research/E_pipelines/E010_pklsa_parametric_knot_link_seed_atlas/E010-v0.3.1'
    pkg=rr/'pklsa_builder'; _write_common_pkg(pkg)
    (pkg/'io_geometry.py').write_text('''from pathlib import Path\nimport numpy as np\ndef load_geometry(path,representation=None,fseries_n=4096):\n a=[]\n for line in Path(path).read_text().splitlines():\n  if line.strip(): a.append([float(x) for x in line.split()[:3]])\n return [np.asarray(a,float)]\n''')
    out=rr/'E010_PKLSA_Production_Knot_Link_Basis_v0.3.1-outputs'; _write_release(out)
    src=wb/'03_data/A_knots/x.dat'; src.parent.mkdir(parents=True)
    t=np.linspace(0,2*np.pi,64,endpoint=False); c=np.c_[np.cos(t),np.sin(t),np.zeros_like(t)]; src.write_text('\n'.join('%.17g %.17g %.17g'%tuple(x) for x in c))
    cc=np.loadtxt(src); raw=hashlib.sha256(src.read_bytes()).hexdigest(); gh=geom_hash([cc])
    _write_topology(out,'3_1','CAR_x','A001','fixture','fixture','fixture','fixture','fixture','xyz',src,raw,gh)
    repo=PKLSARepository.open(wb,rr); carriers,adm=repo.discover({'require_topology_qualification_gate':True,'require_literature_hard_gate':True,'exclude_mirrors':True,'exclude_raw_duplicates':True,'exclude_geometry_duplicates':True})
    assert len(carriers)==1 and adm['admitted_topologies']==1
    comps,verify=repo.load_verified(carriers[0]); assert verify['raw_sha256_verified'] and verify['geometry_sha256_verified'] and len(comps)==1

def test_gilbert_ab_record_dispatch_uses_e010_parser(tmp_path):
    _clear_pklsa_modules()
    wb=tmp_path/'SST-Workbench'; (wb/'10_docs/registry').mkdir(parents=True)
    rr=wb/'01_research/E_pipelines/E010_pklsa_parametric_knot_link_seed_atlas/E010-v0.3.1'
    pkg=rr/'pklsa_builder'; _write_common_pkg(pkg)
    (pkg/'io_geometry.py').write_text('''def load_geometry(*a,**k):\n raise RuntimeError("generic loader must not receive gilbert_ab_record")\n''')
    out=rr/'E010_PKLSA_Production_Knot_Link_Basis_v0.3.1-outputs'; _write_release(out)
    src=wb/'03_data/A_knots/Ideal.txt.gz'; src.parent.mkdir(parents=True)
    with gzip.open(src,'wt',encoding='utf-8') as f: f.write('synthetic gilbert catalog')
    t=np.linspace(0,2*np.pi,4096,endpoint=False); c=np.c_[np.cos(t),np.sin(t),np.zeros_like(t)]
    raw=hashlib.sha256(src.read_bytes()).hexdigest(); gh=geom_hash([c])
    _write_topology(out,'3_1','CAR_g','A004','gilbert_ideal','gilbert','gilbert-fourier-ideal','gilbert:3_1','gilbert-ideal:3_1','gilbert_ab_record',src,raw,gh)
    repo=PKLSARepository.open(wb,rr); carriers,_=repo.discover({'require_topology_qualification_gate':True,'require_literature_hard_gate':True,'exclude_mirrors':True,'exclude_raw_duplicates':True,'exclude_geometry_duplicates':True})
    comps,verify=repo.load_verified(carriers[0],fseries_n=4096)
    assert verify['raw_sha256_verified'] and verify['geometry_sha256_verified'] and len(comps)==1 and len(comps[0])==4096
