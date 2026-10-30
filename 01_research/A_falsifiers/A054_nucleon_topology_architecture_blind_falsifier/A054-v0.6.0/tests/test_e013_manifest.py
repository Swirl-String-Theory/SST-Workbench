from pathlib import Path
import pytest
from a054_state.pklsa import load_cross_manifest
from a054_state.admission import AdmissionError
ROOT=Path(__file__).resolve().parents[1]
def test_accepts_frozen_current_e013_binding():
 assert len(load_cross_manifest(ROOT/'admission/CROSS_CARRIER_MANIFEST.json')['carriers'])==5
def test_rejects_unregistered_selection(tmp_path):
 p=tmp_path/'manifest.json';p.write_text('{}')
 with pytest.raises(AdmissionError,match='external binding'):load_cross_manifest(p)
def test_rejects_missing_manifest(tmp_path):
 with pytest.raises(AdmissionError,match='missing'):load_cross_manifest(tmp_path/'missing.json')
