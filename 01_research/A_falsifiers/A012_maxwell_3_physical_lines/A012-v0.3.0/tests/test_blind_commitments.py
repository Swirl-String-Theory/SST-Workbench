import json
from pathlib import Path
from sst_maxwell3_blind.blind import verify_commitments

def test_commitment_file_has_no_reveal_values():
    root=Path(__file__).resolve().parents[1]
    c=json.loads((root/'blind'/'commitments.json').read_text())
    assert all('value' not in e and 'salt' not in e for e in c['entries'])
