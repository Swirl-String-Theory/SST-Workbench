from __future__ import annotations
import hashlib
import json
import shutil
from pathlib import Path

import pytest
from sst_falsifier.outputs import make_science_evidence_manifest, verify_science_evidence_manifest
from sst_falsifier.outputs import make_output_manifest, verify_output_manifest
from sst_falsifier.protocol import build_protocol_bundle, portable_protocol_fingerprint, verify_frozen
from sst_falsifier.report import write_auto_results_tex, compile_report_pdf
from sst_falsifier.output_policy import new_run_id, report_revision_path


def test_science_evidence_manifest_stable_across_rendered_report(tmp_path):
    root = tmp_path / 'out'; root.mkdir()
    (root/'GATE_LEDGER.json').write_text('gate')
    frozen = make_science_evidence_manifest(root, root/'SCIENCE_EVIDENCE_MANIFEST.json')
    (root/'report').mkdir()
    (root/'report/AUTO_RESULTS.tex').write_text('report changed')
    (root/'REPORT_RENDER_BLIND.json').write_text('rendered')
    make_output_manifest(root,root/'OUTPUT_MANIFEST.json')
    assert verify_science_evidence_manifest(root,root/'SCIENCE_EVIDENCE_MANIFEST.json')[0]
    assert verify_output_manifest(root,root/'OUTPUT_MANIFEST.json')[0]
    assert frozen['manifest_sha256'] == json.loads((root/'SCIENCE_EVIDENCE_MANIFEST.json').read_text())['manifest_sha256']
    (root/'GATE_LEDGER.json').write_text('tampered')
    assert not verify_science_evidence_manifest(root,root/'SCIENCE_EVIDENCE_MANIFEST.json')[0]


def test_science_evidence_manifest_is_create_once(tmp_path):
    p=tmp_path/'SCIENCE_EVIDENCE_MANIFEST.json'
    make_science_evidence_manifest(tmp_path,p)
    with pytest.raises(FileExistsError): make_science_evidence_manifest(tmp_path,p)


def test_auto_results_never_embed_interim_output_manifest_digest(tmp_path):
    root=tmp_path/'instance';out=tmp_path/'out';root.mkdir();out.mkdir()
    (root/'science_contract.json').write_text('{}')
    from unittest.mock import patch
    (out/'OUTPUT_MANIFEST.json').write_text(json.dumps({'manifest_sha256':'WRONG_INTERIM_DIGEST'}))
    (out/'SCIENCE_EVIDENCE_MANIFEST.json').write_text(json.dumps({'manifest_sha256':'stable-science-sha'}))
    with patch('sst_falsifier.report.assert_science_contract',return_value={'research_question':'a','objective':'b','null_hypothesis':'c','alternative_hypothesis':'d'}):
        write_auto_results_tex(root,out,out/'AUTO_RESULTS.tex')
    text=(out/'AUTO_RESULTS.tex').read_text()
    assert 'stable-science-sha' in text.replace(r'-\allowbreak{}','-')
    assert 'WRONG_INTERIM_DIGEST' not in text
    assert 'Final output manifest' in text


def test_portable_hash_normalizes_crlf_only_and_retains_strict_sha(tmp_path):
    a=tmp_path/'a';b=tmp_path/'b';a.mkdir();b.mkdir()
    (a/'c.json').write_bytes(b'{"n": 1}\n')
    (b/'c.json').write_bytes(b'{"n": 1}\r\n')
    h1=build_protocol_bundle(a,['c.json']);h2=build_protocol_bundle(b,['c.json'])
    assert h1['schema'] == h2['schema'] == 'SST-FALSIFIER-PROTOCOL-2'
    assert h1['bundle_sha256'] != h2['bundle_sha256']
    assert h1['portable_bundle_sha256'] == h2['portable_bundle_sha256']
    (b/'c.json').write_text('{"n": 2}\n')
    assert build_protocol_bundle(a,['c.json'])['portable_bundle_sha256'] != build_protocol_bundle(b,['c.json'])['portable_bundle_sha256']


def test_report_only_revision_paths_never_reuse_old_pdf(tmp_path):
    rid=new_run_id()
    first=report_revision_path(tmp_path/'A123-v0.1.0',rid,'BLIND')
    second=report_revision_path(tmp_path/'A123-v0.1.0',rid,'BLIND')
    assert first!=second
    assert rid in first.name and 'RERENDER_' in first.name
    assert report_revision_path(tmp_path/'A123',rid,'REVEALED') != first


def test_long_gate_columns_are_fixed_width_and_breakable(tmp_path):
    root=tmp_path/'inst';out=tmp_path/'out';root.mkdir();out.mkdir()
    (root/'science_contract.json').write_text('{}')
    ledger={'records':[{'gate_id':'G5_SUPER_LONG_GATE_IDENTIFIER_WITH_MANY_COMPONENTS', 'status':'NOT_RUN_PREREQUISITE',
        'question':'Very long descriptive question about cross platform protocol bundle hashing and scientific provenance',
        'reason':'no_independent_source_family_'*7}]}
    (out/'GATE_LEDGER.json').write_text(json.dumps(ledger))
    with __import__('unittest.mock',fromlist=['patch']).patch('sst_falsifier.report.assert_science_contract',return_value={'research_question':'a','objective':'b','null_hypothesis':'c','alternative_hypothesis':'d'}):
        write_auto_results_tex(root,out,out/'AUTO_RESULTS.tex')
    text=(out/'AUTO_RESULTS.tex').read_text()
    assert r'p{0.07\linewidth}p{0.19\linewidth}' in text
    assert r'\allowbreak{}' in text
    assert r'\begin{longtable}{llll}' not in text
    if shutil.which('pdflatex'):
        tex=out/'report.tex'
        tex.write_text('\\documentclass{article}\n\\usepackage{longtable,booktabs,array}\n\\begin{document}\n\\input{AUTO_RESULTS.tex}\n\\end{document}\n')
        result=compile_report_pdf(tex,tmp_path/'report.pdf',strict=True,engine='pdflatex')
        assert result['success']


def test_report_pdf_engine_selection_strict(tmp_path):
    from sst_falsifier.report import _latex_engine
    with pytest.raises(ValueError):_latex_engine('../pdflatex')


def test_reveal_preflight_requires_immutable_science_manifest(tmp_path):
    from sst_falsifier.runner import reveal_eligibility
    from sst_falsifier.outputs import make_output_manifest
    from sst_falsifier.gates import GateLedger, GateDefinition, GateRecord
    from sst_falsifier.util import write_json
    root=tmp_path/'inst';out=root/'Demo_v0.1.0-outputs';out.mkdir(parents=True)
    write_json(root/'blind_policy.json',{'reveal_allowed_after_modes':['FULL'], 'reveal_requires_gate':'G3',
        'reveal_requires_gate_status':['PASS','FAIL'], 'block_reveal_on_unresolved':True})
    definitions=[GateDefinition('G3','q',())]
    led=GateLedger(definitions);led.records.append(GateRecord('G3','FAIL','q',{},'complete negative discovery'))
    led.write(out/'GATE_LEDGER.json')
    write_json(out/'RUN_SUMMARY.json',{'mode':'FULL','protocol_bundle_sha256':'abc','gate_ledger_sha256':led.to_dict()['ledger_sha256']})
    make_output_manifest(out,out/'OUTPUT_MANIFEST.json')
    decision=reveal_eligibility(root,{},out,{'bundle_sha256':'abc'})
    assert decision['eligible'] is False and 'immutable science evidence manifest' in decision['reason']
