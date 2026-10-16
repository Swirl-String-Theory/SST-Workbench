import hashlib,json
import numpy as np
import pytest
from hopf_extension import (ROOT,CASES,geometry,audit,split_native,canonical_hash,run_case)
from three_core import gauss_lk,PeriodicEulerFlow
from a064.flow import file_hash
from euler_extension.spectral import SpectralEuler3D

@pytest.mark.parametrize('case',CASES)
def test_hopf_link_topology(case):
 curves,pr=geometry(case);q=audit(curves,pr,case)
 assert len(curves)==3
 assert q['determinant_screen_pass']
 assert q['pairwise_linking_screen_pass']
 assert q['source_chirality_matched_screen']
 assert q['pairwise_separation_screen_pass']
 assert all(len(c)==160 for c in curves)

@pytest.mark.parametrize('case',('L6n1_KNOTPLOT','T33_KNOTPLOT'))
def test_native_source_splits_and_provenance(case):
 from hopf_extension import SOURCES
 src=ROOT/'data/native'/SOURCES[case]
 p,pr=split_native(src)
 assert len(p)==3
 assert all(len(v)>=12 for v in p)
 assert file_hash(src)==pr['source_sha256']

def test_same_link_type_different_embedding():
 c1,_=geometry('L6n1_KNOTPLOT');c2,_=geometry('T33_KNOTPLOT')
 assert any(not np.allclose(a,b) for a,b in zip(c1,c2))

def test_stationary_abc_and_projection():
 s=SpectralEuler3D(16);x=(np.arange(s.n)-s.n//2)*s.dx
 x,y,z=np.meshgrid(x,x,x,indexing='ij')
 v=np.stack([np.sin(z)+np.cos(y),np.sin(x)+np.cos(z),np.sin(y)+np.cos(x)],axis=-1)
 assert np.max(np.abs(s.rhs(v)))<2e-13

@pytest.mark.parametrize('case',CASES)
def test_bundled_npz_and_blind_discovery(case):
 base=ROOT/'outputs'/f'{case}_N24';p=base/'THREE_CORE_EULER_MODEL.npz'
 if not p.exists():pytest.skip('run N24 before testing output hashes')
 side=json.loads((base/'THREE_CORE_EULER_MODEL.source.json').read_text())
 assert file_hash(p)==side['npz_sha256']
 flow=PeriodicEulerFlow(p)
 assert np.max(np.abs(flow.v[-1]-flow.v[0]))>1e-5
 disc=json.loads((base/'DISCOVERY_ONLY.json').read_text())
 seal=json.loads((base/'DISCOVERY_SEAL.json').read_text())
 assert canonical_hash(disc)==seal['canonical_discovery_sha256']
 assert not seal['transport_audit_computed_at_seal_write']
 assert 'tracer_cross' not in json.dumps(disc)
 assert side['mechanical_gear_contact_modeled'] is False
