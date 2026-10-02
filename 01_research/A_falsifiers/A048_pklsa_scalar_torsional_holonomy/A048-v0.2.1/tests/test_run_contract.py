import json
from pathlib import Path
import numpy as np
import pytest
from sst_torsion.run_contract import create_run, commit_preparation, seal_run, verify_seal, scan_blind, write_json
from sst_torsion.pipeline import prepare, analyze, reveal

ROOT=Path(__file__).resolve().parents[1]


def sealed(tmp_path):
    run=create_run(ROOT,'0.1.1','integrity',{},tmp_path)
    commit_preparation(run,{'cases':{}})
    write_json(run/'BLIND'/'evidence.json',{'value':42})
    seal_run(run)
    return run


@pytest.mark.parametrize('mutation',['extra','missing','changed','empty-seal','key','config','identity'])
def test_exact_inventory_and_commitments_reject_corruption(tmp_path,mutation):
    run=sealed(tmp_path)
    if mutation=='extra':
        (run/'BLIND'/'new.txt').write_text('unexpected')
    elif mutation=='missing':
        (run/'BLIND'/'evidence.json').unlink()
    elif mutation=='changed':
        (run/'BLIND'/'evidence.json').write_text('{"value":43}')
    elif mutation=='empty-seal':
        (run/'BLIND'/'BLIND_SEAL_SHA256.json').write_text('{}')
    else:
        path={'key':'PRIVATE/reveal_key.json','config':'BLIND/frozen_config.json','identity':'RUN_IDENTITY.json'}[mutation]
        (run/path).write_text('{}')
    with pytest.raises((RuntimeError,KeyError,ValueError)):
        verify_seal(run)


@pytest.mark.parametrize('value',[1093845.63,'1093845.6300','1.09384563E+06',{'1.40897017e-15':False},{'r_c':0.1}])
def test_scan_catches_equivalent_numbers_and_keys(tmp_path,value):
    write_json(tmp_path/'nested.json',{'nested':[value]})
    with pytest.raises(ValueError):
        scan_blind(tmp_path)


def test_scan_npz_and_clean_digest(tmp_path):
    write_json(tmp_path/'clean.json',{'digest':'a'*64,'scope':'instrument'})
    assert scan_blind(tmp_path)['status']=='PASS'
    np.savez(tmp_path/'array.npz',values=np.array([1.40897017e-15]))
    with pytest.raises(ValueError):
        scan_blind(tmp_path)


def test_repeated_runs_are_unique_and_sealed_evidence_is_immutable(tmp_path):
    a,b=sealed(tmp_path),sealed(tmp_path)
    assert a!=b and a.exists() and b.exists()
    verify_seal(a)
    with pytest.raises(RuntimeError):
        seal_run(a)


def test_actual_pipeline_reveal_and_idempotent_integrity(tmp_path):
    run=prepare(ROOT,'regression',tmp_path)
    analyze(run,'python')
    seal_run(run)
    report=reveal(run)
    assert report['physics_status'].startswith('NOT_YET_TESTED')
    assert reveal(run)==report
    (run/'REVEALED'/'extra.json').write_text('{}')
    with pytest.raises(RuntimeError):
        reveal(run)
