from copy import deepcopy
import hashlib
import json
from pathlib import Path
import pytest
from a054_state.admission import AdmissionError, validate_manifest, digest

ROOT=Path(__file__).resolve().parents[1]
WB=ROOT.parents[3]


def setup(tmp_path):
    pins=json.loads((ROOT/'admission/RUNTIME_PINS.json').read_text())
    doc=json.loads((ROOT/'admission/CROSS_CARRIER_MANIFEST.json').read_text())
    return pins,doc,tmp_path/'manifest.json'


def seal(pins,doc,path,recompute=True):
    if recompute:
        core={k:v for k,v in doc.items() if k!='content_sha256_without_self_field'}
        doc['content_sha256_without_self_field']=hashlib.sha256(json.dumps(core,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    path.write_text(json.dumps(doc),encoding='utf-8')
    pins['expected_manifest_sha256']=digest(path)


def test_valid_current_binding():
    pins=json.loads((ROOT/'admission/RUNTIME_PINS.json').read_text())
    result=validate_manifest(ROOT/'admission/CROSS_CARRIER_MANIFEST.json',WB,pins)
    assert len(result['source_paths'])==5
    assert not result['cross_provider_science_ready']


@pytest.mark.parametrize('field,value,reason',[
    ('selected_carrier_count',999,'carrier count'),
    ('sklsa_release_id','E011-v0.2.0','release'),
    ('legacy_falsifier_outputs_used_as_evidence',True,'legacy'),
    ('sklsa_static_index_sha256','0'*64,'manifest binding'),
    ('sklsa_provider_anchors_sha256','0'*64,'manifest binding'),
    ('schema','LEGACY','schema'),
])
def test_rejects_manifest_drift(tmp_path,field,value,reason):
    pins,doc,path=setup(tmp_path);doc[field]=value;seal(pins,doc,path)
    with pytest.raises(AdmissionError,match=reason):validate_manifest(path,WB,pins)


def test_rejects_self_hash_tamper_even_with_new_external_hash(tmp_path):
    pins,doc,path=setup(tmp_path);doc['selected_carrier_count']=999;seal(pins,doc,path,recompute=False)
    with pytest.raises(AdmissionError,match='self hash'):validate_manifest(path,WB,pins)


def test_rejects_unregistered_external_manifest(tmp_path):
    pins,doc,path=setup(tmp_path);path.write_text('{}')
    with pytest.raises(AdmissionError,match='external binding'):validate_manifest(path,WB,pins)


@pytest.mark.parametrize('field,value,reason',[
    ('static_seed_id','OTHER_SEED','anchor join'),
    ('provider_group','OTHER_PROVIDER','anchor join'),
    ('carrier_id','OTHER_CARRIER','anchor join'),
    ('geometry_sha256','0'*64,'geometry_sha256 binding'),
    ('raw_sha256','0'*64,'raw_sha256 binding'),
])
def test_rejects_carrier_drift(tmp_path,field,value,reason):
    pins,doc,path=setup(tmp_path);doc['carriers'][0][field]=value;seal(pins,doc,path)
    with pytest.raises(AdmissionError,match=reason):validate_manifest(path,WB,pins)


def test_rejects_duplicate_seed(tmp_path):
    pins,doc,path=setup(tmp_path);doc['carriers'].append(deepcopy(doc['carriers'][0]));doc['selected_carrier_count']+=1;seal(pins,doc,path)
    with pytest.raises(AdmissionError,match='duplicate'):validate_manifest(path,WB,pins)


def test_rejects_locator_drift(tmp_path):
    pins,doc,path=setup(tmp_path);doc['carriers'][0]['source_locator']['source_path']='OTHER.vect';seal(pins,doc,path)
    with pytest.raises(AdmissionError,match='locator join'):validate_manifest(path,WB,pins)


@pytest.mark.parametrize('key',['e011_index','e011_anchors'])
def test_rejects_current_e011_drift(tmp_path,key):
    pins,doc,path=setup(tmp_path);pins[key]['sha256']='0'*64;seal(pins,doc,path)
    with pytest.raises(AdmissionError,match='hash mismatch'):validate_manifest(path,WB,pins)


def test_rejects_loader_drift(tmp_path):
    pins,doc,path=setup(tmp_path);pins['e010_loader_files'][next(iter(pins['e010_loader_files']))]='0'*64;seal(pins,doc,path)
    with pytest.raises(AdmissionError,match='loader.*hash mismatch'):validate_manifest(path,WB,pins)


def test_successor_not_globally_enabled():
    member=json.loads((ROOT/'cross_falsifier_contract.json').read_text())
    assert member['enabled'] is False and member['stage']==30


def test_scientific_source_contract_resolves_admitted_bytes():
    from a054_state.migration import qualified_framework
    qualified_framework(ROOT)
    from sst_falsifier.source_registry import assert_source_contract,resolve_source_contract
    contract=assert_source_contract(ROOT/'source_contract.json')
    sources=resolve_source_contract(ROOT/'source_contract.json',root=WB)['sources']
    assert len(sources)==5
    assert all(actual['exists'] and actual.get('sha256')==expected['raw_sha256'] for expected,actual in zip(contract['sources'],sources))


def test_source_contract_rejects_wrong_path_field(tmp_path):
    from a054_state.migration import qualified_framework
    qualified_framework(ROOT)
    from sst_falsifier.source_registry import assert_source_contract,SourceContractError
    contract=json.loads((ROOT/'source_contract.json').read_text())
    contract['sources'][0]['path']=contract['sources'][0].pop('relative_path')
    p=tmp_path/'sources.json';p.write_text(json.dumps(contract))
    with pytest.raises(SourceContractError,match='relative_path'):assert_source_contract(p)


def test_protocol_excludes_mutable_publication_pointers():
    protocol=json.loads((ROOT/'preregistration/MIGRATION_PROTOCOL.json').read_text())
    paths={row['path'] for row in protocol['files']}
    assert 'LATEST_RUN.json' not in paths and 'PUBLICATIONS.jsonl' not in paths
    assert not any('_outputs' in part for name in paths for part in Path(name).parts)
