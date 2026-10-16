import json,sys
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from production_import import read_manifest
from holonomy import sha256

def test_import_qualified_npy(tmp_path):
    a=np.column_stack((np.cos(np.arange(20)*2*np.pi/20),np.sin(np.arange(20)*2*np.pi/20),np.zeros(20)))
    np.save(tmp_path/'geometry.npy',a)
    case=dict(topology_id='3_1',carrier_id='test',provider_group='provider1',source_role='upstream_geometry',source_path='geometry.npy',geometry_sha256=sha256(tmp_path/'geometry.npy'),qualification_gate_pass=True)
    mf=dict(schema='A064-PKLSA-MANIFEST-1',pklsa_version='0.4.0',release_schema='PKLSA-HIGH-RES-QUALIFICATION-4',publication_ready_geometry_layer=True,carriers=[case])
    (tmp_path/'manifest.json').write_text(json.dumps(mf)); assert len(read_manifest(tmp_path/'manifest.json'))==1
    case['source_role']='generated';(tmp_path/'manifest.json').write_text(json.dumps(mf))
    with pytest.raises(ValueError,match='Generated'):read_manifest(tmp_path/'manifest.json')

def test_reject_hash(tmp_path):
    (tmp_path/'geometry.npy').write_text('x')
    case=dict(topology_id='3_1',carrier_id='test',provider_group='p',source_role='upstream_geometry',source_path='geometry.npy',geometry_sha256='wrong',qualification_gate_pass=True)
    d=dict(schema='A064-PKLSA-MANIFEST-1',pklsa_version='0.4.0',release_schema='PKLSA-HIGH-RES-QUALIFICATION-4',publication_ready_geometry_layer=True,carriers=[case])
    (tmp_path/'manifest.json').write_text(json.dumps(d))
    with pytest.raises(ValueError,match='SHA-256'):read_manifest(tmp_path/'manifest.json')
