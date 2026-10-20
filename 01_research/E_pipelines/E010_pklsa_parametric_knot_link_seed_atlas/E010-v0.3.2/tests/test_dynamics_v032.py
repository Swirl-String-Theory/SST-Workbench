from __future__ import annotations
import hashlib,json,os,sys,zipfile
from pathlib import Path
import numpy as np
import pytest
# installed as an extension inside E010-v0.3.2
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pklsa_builder.dynamics_ready import (
   E011SeedContract,AdmissionError,bs_velocity,bs_energy_proxy,evolve,rk4,qualify,
   pre_registered_policy,arclength_n,nonlocal_midpoint_gap,native_geometry,source_path)

def circle(n=64,r=1.0):
 t=np.linspace(0,2*np.pi,n,endpoint=False)
 return np.column_stack((r*np.cos(t),r*np.sin(t),np.zeros_like(t)))

def contract_fixture(tmp_path):
 src=tmp_path/'source.xyz';src.write_text('\n'.join(' '.join(map(str,r)) for r in circle(72))+'\n')
 raw=hashlib.sha256(src.read_bytes()).hexdigest()
 seed={'topology_id':'0_1','provider_group':'synthetic','static_ready':True,'seed_role':'PRIMARY_REFERENCE',
       'evidence_class':'UPSTREAM_INDEPENDENT','static_seed_id':'SEED_1','carrier_id':'CAR_1',
       'capabilities':{'curvature_rms_ready':True,'reach_ready':True},
       'literature_gate_status':{'G1_isotopy_safe_sampling':'PASS',
             'G2_writhe_quadratic_convergence':'PASS','G3_signed_frenet_chirality_completeness':'PASS'},
       'source_locator':{'raw_sha256':raw,'representation':'xyz','source_path':'C:\\workspace\\projects\\SST-Workbench\\03_data\\A_knots\\test.xyz'}}
 z=tmp_path/'e011.zip';prefix='E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs/'
 with zipfile.ZipFile(z,'w') as f:
  f.writestr(prefix+'SEED_CONTRACT_SCHEMA.json',json.dumps({'schema':'E011-STATIC-SEED-CONTRACT-1','atlas_version':'0.3.0','dynamics_ready':False}))
  f.writestr(prefix+'STATIC_READY_PROVIDER_ANCHORS.jsonl',json.dumps(seed)+'\n')
 return src,z,seed

def test_ring_translation_symmetry():
 v=bs_velocity(circle(64),0.1)
 assert np.max(abs(v[:,0]))<1e-11
 assert np.max(abs(v[:,1]))<1e-11
 assert np.std(v[:,2])<1e-11
 assert abs(float(v[0,2]))>0.01

def test_winding_reversal_changes_velocity_sign():
 p=circle(64);vp=bs_velocity(p,.1)
 # reversed node order starts at same original point at index 0; reversing the filament flips v
 reverse=p[(-np.arange(64))%64];vm=bs_velocity(reverse,.1)
 assert np.max(abs(vp+vm))<1e-11

def test_kernel_finite_and_positive_energy():
 p=circle(32);assert np.isfinite(bs_velocity(p,.06)).all()
 assert np.isfinite(bs_energy_proxy(p,.06)) and bs_energy_proxy(p,.06)>0

def test_rk4_shape_and_dt():
 p=circle(32);a=rk4(p,.001,.05);b=evolve(p,.002,2,.05)
 assert a.shape==p.shape and np.isfinite(b).all() and np.linalg.norm(a-p)>0

def test_invalid_core():
 with pytest.raises(ValueError):bs_velocity(circle(32),0)
 with pytest.raises(ValueError):bs_velocity(circle(32),float('nan'))

def test_arclength_closes():
 p=arclength_n(circle(36),64);assert p.shape==(64,3)
 assert 0.01<nonlocal_midpoint_gap(p)<2.1

def test_mock_contract_is_admissible_and_hash_verified(tmp_path):
 src,z,seed=contract_fixture(tmp_path);c=E011SeedContract(z,hashlib.sha256(z.read_bytes()).hexdigest())
 selected=c.select('0_1','synthetic')
 assert selected['static_seed_id']==seed['static_seed_id']
 p,h=source_path(selected,tmp_path,override=src)
 assert p==src and h==seed['source_locator']['raw_sha256']

def test_source_tampering_is_rejected(tmp_path):
 src,z,_=contract_fixture(tmp_path);c=E011SeedContract(z)
 seed=c.select('0_1','synthetic');src.write_text(src.read_text()+'tamper\n')
 with pytest.raises(AdmissionError,match='hash mismatch'):source_path(seed,tmp_path,override=src)

def test_bad_e011_zip_hash_rejected(tmp_path):
 _,z,_=contract_fixture(tmp_path)
 with pytest.raises(AdmissionError,match='SHA256 mismatch'):E011SeedContract(z,'0'*64)

def test_static_not_dynamics(tmp_path):
 src,z,_=contract_fixture(tmp_path)
 with zipfile.ZipFile(z,'r') as f:
  seeds=f.read('E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs/STATIC_READY_PROVIDER_ANCHORS.jsonl')
 with zipfile.ZipFile(z,'w') as f:
  prefix='E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs/'
  f.writestr(prefix+'SEED_CONTRACT_SCHEMA.json',json.dumps({'schema':'E011-STATIC-SEED-CONTRACT-1','atlas_version':'0.3.0','dynamics_ready':True}))
  f.writestr(prefix+'STATIC_READY_PROVIDER_ANCHORS.jsonl',seeds)
 with pytest.raises(AdmissionError):E011SeedContract(z)

def test_reject_generated_control(tmp_path):
 src,z,seed=contract_fixture(tmp_path)
 seed['evidence_class']='GENERATED_OR_CONTROL'
 with zipfile.ZipFile(z,'w') as f:
  prefix='E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs/'
  f.writestr(prefix+'SEED_CONTRACT_SCHEMA.json',json.dumps({'schema':'E011-STATIC-SEED-CONTRACT-1','atlas_version':'0.3.0','dynamics_ready':False}))
  f.writestr(prefix+'STATIC_READY_PROVIDER_ANCHORS.jsonl',json.dumps(seed))
 with pytest.raises(AdmissionError,match='independent upstream'):E011SeedContract(z).select('0_1','synthetic')

def test_reject_failed_e010_hard_gate(tmp_path):
 src,z,seed=contract_fixture(tmp_path)
 seed['literature_gate_status']['G2_writhe_quadratic_convergence']='FAIL'
 with zipfile.ZipFile(z,'w') as f:
  prefix='E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs/'
  f.writestr(prefix+'SEED_CONTRACT_SCHEMA.json',json.dumps({'schema':'E011-STATIC-SEED-CONTRACT-1','atlas_version':'0.3.0','dynamics_ready':False}))
  f.writestr(prefix+'STATIC_READY_PROVIDER_ANCHORS.jsonl',json.dumps(seed))
 with pytest.raises(AdmissionError,match='literature gate'):E011SeedContract(z).select('0_1','synthetic')

def test_basic_never_dynamics_ready():
 p=circle(36)
 r=qualify(p,core=.05,tfinal=.0005,steps=4,fine_n=32,full=False)
 assert r['status']=='DYNAMICS_NOT_READY'
 assert r['claims']['three_d_Euler'] is False

def test_registered_full_not_promoted_with_unqualified_grid():
 p=circle(36)
 r=qualify(p,core=.017,tfinal=.004,steps=8,fine_n=32,full=True)
 assert r['status']=='DYNAMICS_NOT_READY'
 assert not r['registered_full_protocol']

def test_gilbert_parser_native_fixture(tmp_path):
 # This test never invents E011 provenance; only confirms the native parser branch.
 from pklsa_builder.gilbert import find_gilbert_record, sample_gilbert_record
 f=tmp_path/'Ideal.txt'
 f.write_text('<AB Id="3:1:1" L="16.37" D="1.0">\n<Coeff I="1" A="1,0,0" B="0,1,0" />\n<Coeff I="2" A="0.1,0,0" B="0,0.1,0" />\n</AB>\n')
 r=find_gilbert_record(f,'3_1');g=sample_gilbert_record(r,48)
 assert g.shape==(48,3) and r['attrs']['Id']=='3:1:1'

def test_e011_real_archive_optional():
 p=os.environ.get('PKLSA_TEST_E011_ZIP')
 if not p:pytest.skip('optional real E011 output ZIP not supplied')
 x=E011SeedContract(p);anchors=x.anchors('3_1');assert len(anchors)>=2
 s=x.select('3_1','gilbert')
 assert s['source_locator']['raw_sha256']=='274a4ce111607a6295e280f3f8369c665e7de82ac33afcd4cb227eb61568d530'
 assert s['literature_gate_status']['B1_ideal_trefoil_ropelength']=='FAIL'

def test_native_vect_parser_without_duplicating_geometry_code(tmp_path):
 from pklsa_builder.io_geometry import load_vect
 from pklsa_builder.geometry import clean_closed
 p=circle(16)
 src=tmp_path/'knot.vect'
 rows=['VECT','1 17 0','-17','0']+[' '.join(map(str,x)) for x in np.vstack([p,p[:1]])]
 src.write_text('\n'.join(rows)+'\n')
 components=load_vect(src)
 assert len(components)==1 and clean_closed(components[0]).shape==(16,3)


def test_reject_noncanonical_local_path_outside_workbench(tmp_path):
 src,z,_=contract_fixture(tmp_path)
 seed=E011SeedContract(z).select('0_1','synthetic')
 # A filesystem source with the right hash is fine ONLY if explicitly overridden.
 with pytest.raises(AdmissionError):source_path(seed,tmp_path)
 assert source_path(seed,tmp_path,override=src)[1]==hashlib.sha256(src.read_bytes()).hexdigest()
