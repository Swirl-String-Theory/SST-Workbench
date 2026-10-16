from pathlib import Path
import json
import tempfile
import pytest
from report_generator import extract_gates,generate


def test_real_schema_shape():
    ledger={'schema':'SST-GATE-LEDGER','definitions':[{'gate_id':'G1','question':'example question'}],
            'records':[{'gate_id':'G1','status':'FAIL','reason':'no evidence',
                        'metrics':{'number':3,'opaque_ids':['do_not_print']}}]}
    g=extract_gates(ledger)
    assert g[0]['status']=='FAIL'
    assert g[0]['question']=='example question'


def test_non_mutating_lifecycle():
    with tempfile.TemporaryDirectory() as t:
        src=Path(t)/'original';dest=Path(t)/'external';src.mkdir()
        ledger={'definitions':[{'gate_id':'G1','question':'No passage'}],
                'records':[{'gate_id':'G1','status':'FAIL','reason':'Failed by design'}],
                'ledger_sha256':'sha'}
        (src/'GATE_LEDGER.json').write_text(json.dumps(ledger))
        (src/'RUN_SUMMARY.json').write_text(json.dumps({'gate_ledger_sha256':'sha'}))
        (src/'private').mkdir();(src/'private'/'secret.json').write_text('not a public source')
        before={p.name:p.read_bytes() for p in src.iterdir() if p.is_file()}
        pdf,tex,audit,g=generate(src,dest,'A999','v0.1.0','test','reportlab')
        assert pdf.stat().st_size>2000
        assert g[0]['status']=='FAIL'
        assert 'secret' not in tex.read_text()
        assert before=={p.name:p.read_bytes() for p in src.iterdir() if p.is_file()}
        assert json.loads(audit.read_text())['declared_gate_ledger_summary_binding_matches']
        with pytest.raises(ValueError):generate(src,src/'illegal','A999','v0.1.0','test','reportlab')
