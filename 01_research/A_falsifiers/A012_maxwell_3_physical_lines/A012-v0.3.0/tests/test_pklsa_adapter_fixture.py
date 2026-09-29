import json,hashlib
from pathlib import Path
import numpy as np
from sst_maxwell3_blind.pklsa_adapter import PKLSARepository

def geom_hash(comps):
    h=hashlib.sha256(); h.update(b'PKLSA-GEOMETRY-SHA256-v1\0')
    for c in comps:
        a=np.asarray(c,dtype='<f8',order='C'); h.update(np.asarray(a.shape,dtype='<i8').tobytes()); h.update(a.tobytes(order='C'))
    return h.hexdigest()

def test_minimal_pklsa_fixture(tmp_path):
    wb=tmp_path/'SST-Workbench'; (wb/'10_docs/registry').mkdir(parents=True)
    rr=wb/'01_research/E_pipelines/E010_pklsa_parametric_knot_link_seed_atlas/E010-v0.3.1'
    pkg=rr/'pklsa_builder'; pkg.mkdir(parents=True); (pkg/'__init__.py').write_text('')
    (pkg/'io_geometry.py').write_text('''from pathlib import Path\nimport numpy as np\ndef load_geometry(path,representation=None,fseries_n=4096):\n a=[]\n for line in Path(path).read_text().splitlines():\n  if line.strip(): a.append([float(x) for x in line.split()[:3]])\n return [np.asarray(a,float)]\n''')
    (pkg/'hashing.py').write_text('''import hashlib,numpy as np\ndef geometry_sha256(components):\n h=hashlib.sha256();h.update(b"PKLSA-GEOMETRY-SHA256-v1\\0")\n for c in components:\n  a=np.asarray(c,dtype="<f8",order="C");h.update(np.asarray(a.shape,dtype="<i8").tobytes());h.update(a.tobytes(order="C"))\n return h.hexdigest()\n''')
    out=rr/'E010_PKLSA_Production_Knot_Link_Basis_v0.3.1-outputs'; out.mkdir()
    release={k:True for k in ['source_native_mode','source_contract_gate_pass','a001_a008_coverage_gate_pass','canonical_identity_admission_gate_pass','identity_database_gate_pass','topology_database_ingest_gate_pass','unregistered_source_gate_pass']}; release.update({'e010_version':'0.3.1','full_campaign_gate_pass':False,'publication_ready_geometry_layer':False,'topology_count':1,'failed_topology_count':0}); (out/'RELEASE.json').write_text(json.dumps(release))
    src=wb/'03_data/A_knots/x.dat'; src.parent.mkdir(parents=True)
    t=np.linspace(0,2*np.pi,64,endpoint=False); c=np.c_[np.cos(t),np.sin(t),np.zeros_like(t)]; src.write_text('\n'.join('%.17g %.17g %.17g'%tuple(x) for x in c))
    # re-read to match text roundtrip
    cc=np.loadtxt(src); raw=hashlib.sha256(src.read_bytes()).hexdigest(); gh=geom_hash([cc])
    td=out/'atlas/3_1'; (td/'qualification').mkdir(parents=True); (td/'sources').mkdir()
    (td/'qualification/summary.json').write_text(json.dumps({'qualification_gate_pass':True,'topology_id':'3_1'}))
    (td/'qualification/geometry_metrics.json').write_text(json.dumps({'carriers':[{'carrier_id':'CAR_x','catalog_id':'A001','source_family':'fixture','literature_hard_gate_pass':True,'finest_resolution':64,'finest_metrics':{'reach':0.1,'thickness':0.2},'observable_status':{'reach':'RESOLVED'},'scale_context':{'normalization_scale':1.0}}]}))
    (td/'qualification/source_independence.json').write_text(json.dumps({'entries':[{'carrier_id':'CAR_x','provider_group':'fixture','method_group':'fixture','lineage_group':'fixture','independence_group':'fixture','evidence_independence_class':'UPSTREAM_REFERENCE','raw_duplicate_of':None,'geometry_duplicate_of':None}]}))
    env={'carrier':{'carrier_id':'CAR_x','catalog_id':'A001','topology_id':'3_1','source_family':'fixture','source_role':'geometry','representation':'xyz','source_path':str(src),'raw_sha256':raw},'geometry_sha256':gh}
    (td/'sources/CAR_x.json').write_text(json.dumps(env))
    repo=PKLSARepository.open(wb,rr); carriers,adm=repo.discover({'require_topology_qualification_gate':True,'require_literature_hard_gate':True,'exclude_mirrors':True,'exclude_raw_duplicates':True,'exclude_geometry_duplicates':True})
    assert len(carriers)==1 and adm['admitted_topologies']==1
    comps,verify=repo.load_verified(carriers[0]); assert verify['raw_sha256_verified'] and verify['geometry_sha256_verified'] and len(comps)==1
