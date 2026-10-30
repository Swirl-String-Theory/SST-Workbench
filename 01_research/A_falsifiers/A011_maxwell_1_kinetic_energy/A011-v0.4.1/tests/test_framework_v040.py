from pathlib import Path
import json
import shutil

import pytest
from maxwell_sst_falsifier import framework_v110 as adapter

ROOT = Path(__file__).resolve().parents[1]


def test_real_admission_uses_only_three_pinned_geometry_sources():
    contract, plan, accepted = adapter.verify_admission(ROOT)
    assert contract['no_scientific_promotion'] is True
    assert len(accepted) == 3
    assert plan['resolution_ladder'] == [64, 128]
    assert {s['topology_id'] for s, _ in accepted} == {'0_1', '3_1', '4_1'}


def test_tampered_admission_contract_rejected(tmp_path):
    for name in ['provenance', 'config']:
        shutil.copytree(ROOT / name, tmp_path / name)
    for name in ['ADAPTER_INPUT_PINS.json', 'E010_SOURCE_PIN.json']:
        shutil.copy2(ROOT / name, tmp_path / name)
    path = tmp_path / 'provenance/A011_DATASET_ADMISSION.json'
    path.write_text(path.read_text() + '\n')
    with pytest.raises(adapter.AdmissionError, match='Pinned source drift'):
        adapter.verify_admission(tmp_path)


def test_source_geometry_drift_rejected_without_fallback(monkeypatch):
    source = adapter.read(ROOT / 'config/geometry_smoke_v040.json')['seeds'][0]['source_path']
    real_digest = adapter.digest
    monkeypatch.setattr(adapter, 'digest', lambda p: '0'*64 if Path(p).resolve() == Path(source).resolve() else real_digest(p))
    with pytest.raises(adapter.AdmissionError, match='raw bytes'):
        adapter.verify_admission(ROOT)


def test_existing_results_are_not_overwritten(tmp_path):
    sentinel = tmp_path / 'historical.txt'
    sentinel.write_text('retained')
    with pytest.raises(FileExistsError):
        adapter.run(ROOT, tmp_path)
    assert sentinel.read_text() == 'retained'


def test_physical_prerequisite_never_promoted_by_parity():
    adapter.qualified_framework(ROOT)
    from sst_falsifier.gates import GateLedger, GateDefinition, GateInputsUnavailable
    ledger = GateLedger([GateDefinition('G1', 'source'), GateDefinition('G3', 'physics', ('G1',)), GateDefinition('G5', 'parity', ('G3',))])
    def missing():
        raise GateInputsUnavailable('no independent physical evidence')
    ledger.run_evaluators({'G1': lambda: {'status': 'PASS'}, 'G3': missing, 'G5': lambda: {'status': 'PASS'}})
    assert ledger.status('G5') == 'PASS'
    assert ledger.qualification('G5')['qualification'] == 'DIAGNOSTIC_ONLY'
    assert ledger.qualification('G5')['allows_dependent_claim'] is False


def test_source_pin_rejects_path_escape_and_byte_drift(tmp_path):
    p = tmp_path / 'source.py'
    p.write_text('original')
    pin = {'source.py': adapter.digest(p)}
    p.write_text('changed')
    with pytest.raises(adapter.AdmissionError, match='Pinned source drift'):
        adapter.verify_file_pins(tmp_path, pin)
    with pytest.raises(adapter.AdmissionError, match='escapes'):
        adapter.bounded_path(tmp_path, '../escape')
