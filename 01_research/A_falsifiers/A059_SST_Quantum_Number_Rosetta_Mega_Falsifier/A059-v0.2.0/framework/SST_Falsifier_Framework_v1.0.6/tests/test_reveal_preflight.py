from pathlib import Path
import json
from sst_falsifier.runner import reveal_eligibility,_purge_stale_reveal_artifacts
from sst_falsifier.gates import GateDefinition, GateLedger, GateRecord
from sst_falsifier.outputs import make_output_manifest
from sst_falsifier.util import write_json


def _write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(obj),encoding='utf-8')


def _case(tmp_path,g2='FAIL',g3='NOT_RUN_PREREQUISITE',unresolved=False):
    root=tmp_path/'i'; out=root/'X_v0.0.1-outputs'; out.mkdir(parents=True)
    _write(root/'blind_policy.json',{'reveal_allowed_after_modes':['FULL'],'reveal_requires_gate':'G3','reveal_requires_gate_status':['PASS','FAIL'],'block_reveal_on_unresolved':True})
    defs=[GateDefinition('G0','q',()),GateDefinition('G1','q',('G0',)),GateDefinition('G2','q',('G1',)),GateDefinition('G3','q',('G2',)),GateDefinition('G5','q',('G3',)),GateDefinition('G9','q',('G5',))]
    led=GateLedger(defs)
    for gid,status in [('G0','PASS'),('G1','PASS'),('G2',g2),('G3',g3)]:
        led.records.append(GateRecord(gid,status,'q',{},''))
    if unresolved: led.records.append(GateRecord('G5','UNRESOLVED','q',{},''))
    led.write(out/'GATE_LEDGER.json')
    ledger_hash=led.to_dict()['ledger_sha256']
    write_json(out/'RUN_SUMMARY.json',{'mode':'FULL','protocol_bundle_sha256':'abc','gate_ledger_sha256':ledger_hash,'revealed':False})
    make_output_manifest(out,out/'OUTPUT_MANIFEST.json')
    return root,out


def test_not_run_discovery_withholds_without_reclassifying(tmp_path):
    root,out=_case(tmp_path)
    d=reveal_eligibility(root,{},out,{'bundle_sha256':'abc'})
    assert d['eligible'] is False and 'G3 status=NOT_RUN_PREREQUISITE' in d['reason']


def test_completed_negative_discovery_can_reveal(tmp_path):
    root,out=_case(tmp_path,g2='PASS',g3='FAIL')
    d=reveal_eligibility(root,{},out,{'bundle_sha256':'abc'})
    assert d['eligible'] is True


def test_unresolved_gate_still_blocks_reveal(tmp_path):
    root,out=_case(tmp_path,g2='PASS',g3='PASS',unresolved=True)
    d=reveal_eligibility(root,{},out,{'bundle_sha256':'abc'})
    assert d['eligible'] is False and d['unresolved_gates']==['G5']


def test_gate_ledger_self_hash_tamper_blocks_reveal(tmp_path):
    root,out=_case(tmp_path,g2='PASS',g3='PASS')
    payload=json.loads((out/'GATE_LEDGER.json').read_text())
    payload['records'][0]['reason']='tampered'
    write_json(out/'GATE_LEDGER.json',payload)
    # Regenerate manifest so the ledger-specific check, not only file-manifest check, is exercised.
    make_output_manifest(out,out/'OUTPUT_MANIFEST.json')
    d=reveal_eligibility(root,{},out,{'bundle_sha256':'abc'})
    assert not d['eligible'] and 'self-hash mismatch' in d['reason']


def test_summary_ledger_hash_mismatch_blocks_reveal(tmp_path):
    root,out=_case(tmp_path,g2='PASS',g3='PASS')
    summary=json.loads((out/'RUN_SUMMARY.json').read_text()); summary['gate_ledger_sha256']='0'*64
    write_json(out/'RUN_SUMMARY.json',summary); make_output_manifest(out,out/'OUTPUT_MANIFEST.json')
    d=reveal_eligibility(root,{},out,{'bundle_sha256':'abc'})
    assert not d['eligible'] and 'RUN_SUMMARY.json gate_ledger_sha256' in d['reason']


def test_output_manifest_tamper_blocks_reveal(tmp_path):
    root,out=_case(tmp_path,g2='PASS',g3='PASS')
    (out/'extra.txt').write_text('unexpected',encoding='utf-8')
    d=reveal_eligibility(root,{},out,{'bundle_sha256':'abc'})
    assert not d['eligible'] and 'OUTPUT_MANIFEST' in d['reason']


def test_new_blind_run_purges_post_reveal_artifacts_and_parent_pdf(tmp_path):
    root,out=_case(tmp_path,g2='PASS',g3='PASS')
    (out/'revealed').mkdir(); (out/'revealed'/'reveal.json').write_text('{}')
    (out/'report').mkdir(); (out/'report'/'POST_RUN_DISCUSSION.tex').write_text('post')
    for n in ('GATE_LEDGER_REVEALED.json','RUN_SUMMARY_REVEALED.json','REVEAL_VERIFICATION.json','REVEAL_DECISION.json'):
        (out/n).write_text('{}')
    cfg={'project':{'name':'X','version':'v0.0.1'}}
    z=root.parent/'X_v0.0.1-outputs_REVEALED.zip'; z.write_bytes(b'z')
    pdf=root.parent/f'{root.name}_FALSIFIER_REPORT.pdf'; pdf.write_bytes(b'pdf')
    _purge_stale_reveal_artifacts(root,cfg,out)
    assert not (out/'revealed').exists()
    assert not (out/'report'/'POST_RUN_DISCUSSION.tex').exists()
    assert not z.exists() and not pdf.exists()
    for n in ('GATE_LEDGER_REVEALED.json','RUN_SUMMARY_REVEALED.json','REVEAL_VERIFICATION.json','REVEAL_DECISION.json'):
        assert not (out/n).exists()


def test_finalize_reveal_writes_decision_before_revealed_zip(tmp_path):
    import zipfile
    from sst_falsifier.runner import _finalize_reveal
    root=tmp_path/'A900-v0.1.0'; root.mkdir(); out=root/'Demo_v0.1.0-outputs'; out.mkdir()
    (out/'GATE_LEDGER.json').write_text('{}',encoding='utf-8')
    cfg={'project':{'name':'Demo','version':'v0.1.0'}}
    decision={'schema':'SST-REVEAL-DECISION-2','eligible':True,'performed':False,'reason':'eligible'}
    assert _finalize_reveal(root,cfg,out,decision)==0
    z=root.parent/'Demo_v0.1.0-outputs_REVEALED.zip'
    assert z.is_file()
    with zipfile.ZipFile(z) as archive:
        names=set(archive.namelist())
        assert 'REVEAL_DECISION.json' in names
        assert 'OUTPUT_MANIFEST.json' in names
        stored=json.loads(archive.read('REVEAL_DECISION.json'))
        assert stored['performed'] is True
