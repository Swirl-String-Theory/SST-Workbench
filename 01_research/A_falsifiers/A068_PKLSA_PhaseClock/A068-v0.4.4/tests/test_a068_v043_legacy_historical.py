"""A004 v0.2.2 immutable external-library contract tests; no physics promotion."""
from pathlib import Path
import json
import shutil
import numpy as np
import pytest
from experiment import a004_adapter as a004, historical

ROOT=Path(__file__).resolve().parents[1]

def wb():
    return a004.workbench_from_instance(ROOT)

def test_external_a004_all_40_and_release_identity():
    result=historical.audit(wb())
    assert result['valid'] and result['manifest_sha256']==a004.MANIFEST_SHA256
    assert result['verified_files']==40
    assert result['independent_physical_providers']==0
    assert result['library_version']=='0.2.2'
    assert not (ROOT/'data/historical').exists() # single owner, no copying

def test_v022_fixed_origin_orientations_and_mirror():
    for model in ('A','B'):
        a=a004.load_seed(model,'orig','ccw',600,workbench_root=wb())
        b=a004.load_seed(model,'orig','cw',600,workbench_root=wb())
        m=a004.load_seed(model,'mirrorX','ccw',600,workbench_root=wb())
        mc=a004.load_seed(model,'mirrorX','cw',600,workbench_root=wb())
        assert np.array_equal(b,np.concatenate((a[:1],a[:0:-1]),axis=0))
        assert np.array_equal(m,np.column_stack((-a[:,0],a[:,1],a[:,2])))
        assert np.array_equal(mc,np.concatenate((m[:1],m[:0:-1]),axis=0))
        assert a.shape==(600,3)

def test_A004_source_class_only_geometry():
    j=json.loads((ROOT/'source_contract.json').read_text())
    s=[item for item in j['sources'] if item['catalog_id']=='A004']
    assert len(s)==3 and all(item['relative_path'].startswith('02_libraries/') for item in s)
    assert j['replication_policy']['independent_physical_provider_count']==0
    assert j['replication_policy']['a004_external_sources_required']
    assert j['replication_policy']['a004_manifest_sha256']==a004.MANIFEST_SHA256

def test_A004_actual_3d_euler_pilot_from_external_library():
    res=historical.pilot(wb(),'BASIC')
    assert res['all_model_screens_pass']
    assert len(res['test_matrix'])==2
    assert all(x['n_steps']==10 for x in res['test_matrix'].values())
    assert res['physical_clock']=='UNRESOLVED'

def test_A004_fail_closed_manifest_tamper(tmp_path):
    target=tmp_path/'WB'/a004.LIBRARY_RELATIVE
    shutil.copytree(a004.library_root(wb()),target)
    with (target/'data/manifest.json').open('ab') as f:f.write(b'\n')
    with pytest.raises(a004.A004SourceError,match='manifest'):
        a004.audit_library(tmp_path/'WB')

def test_A004_fail_closed_XYZ_tamper(tmp_path):
    target=tmp_path/'WB'/a004.LIBRARY_RELATIVE
    shutil.copytree(a004.library_root(wb()),target)
    with (target/'data'/a004.filename('B','orig','ccw',600)).open('ab') as f:f.write(b'\n')
    with pytest.raises(a004.A004SourceError,match='SHA256'):
        a004.audit_library(tmp_path/'WB')

def test_A004_missing_library_refused(tmp_path):
    with pytest.raises(a004.A004SourceError,match='Missing'):
        a004.load_seed('A',workbench_root=tmp_path)

def test_A004_unknown_resolution_refused():
    with pytest.raises(a004.A004SourceError):
        a004.filename('A',resolution=768)

def test_a068_source_gate_fails_without_canonical_A004(tmp_path):
    from experiment import pipeline
    missing=tmp_path/'WB'/'01_research/A_falsifiers/A068_PKLSA_PhaseClock/A068-v0.4.4'
    missing.mkdir(parents=True)
    shutil.copy2(ROOT/'source_contract.json',missing/'source_contract.json')
    audit=pipeline.source_audit(missing)
    assert audit['valid'] is False
    assert audit['historical_atlas']['valid'] is False
    assert audit['files']['A004/INVALID']['match'] is False
