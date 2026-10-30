"""v1.0.10 non-short-circuit gate execution and independent scientific authority."""
import json
from pathlib import Path

import pytest

from sst_falsifier.gates import (GateAlreadyRecordedError, GateDefinition,
                                GateDependencyError, GateError, GateInputsUnavailable,
                                GateLedger)
from sst_falsifier.outputs import make_output_manifest, make_science_evidence_manifest
from sst_falsifier.runner import reveal_eligibility
from sst_falsifier.util import write_json


def chain():
    return [GateDefinition(f'G{i}',f'Question {i}', () if i==0 else (f'G{i-1}',)) for i in range(9)] + [GateDefinition('G9','reveal',('G8',))]


def test_all_evaluators_run_after_middle_failure():
    led=GateLedger(chain())
    called=[]
    def fn(gid):
        def run():
            called.append(gid)
            return {'status':'FAIL' if gid=='G2' else 'PASS','metrics':{'test':gid},'reason':'tested'}
        return run
    led.run_evaluators({f'G{i}':fn(f'G{i}') for i in range(9)})
    assert called==[f'G{i}' for i in range(9)]
    assert [led.status(f'G{i}') for i in range(9)]==['PASS','PASS','FAIL']+['PASS']*6
    assert led.qualification('G2')['qualification']=='QUALIFIED'  # authoritative negative finding
    assert led.qualification('G3')['qualification']=='DIAGNOSTIC_ONLY'
    assert led.qualification('G8')['qualification']=='DIAGNOSTIC_ONLY'  # transitive dependency
    assert led.status('G9') is None  # reveal never occurs during blind execution
    assert all(r.execution_status=='EXECUTED' for r in led.records)
    data=led.to_dict()
    assert data['execution_policy']=='FULL_DIAGNOSTIC'
    assert next(r for r in data['records'] if r['gate_id']=='G7')['blocked_by']==['G6']
    copy=GateLedger.from_dict(json.loads(json.dumps(data)))
    assert copy.qualification('G8')['qualification']=='DIAGNOSTIC_ONLY'
    assert copy.to_dict()['ledger_sha256']==data['ledger_sha256']


def test_unresolved_gate_does_not_abort_following_evaluators():
    led=GateLedger([GateDefinition('G0','a'),GateDefinition('G1','b',('G0',)),GateDefinition('G2','c',('G1',))])
    called=[]
    led.run_evaluators({'G0':lambda:{'status':'UNRESOLVED'},
                        'G1':lambda:(called.append('G1') or {'status':'FAIL'}),
                        'G2':lambda:(called.append('G2') or {'status':'PASS'})})
    assert called==['G1','G2']
    assert led.qualification('G2')['qualification']=='DIAGNOSTIC_ONLY'


def test_no_evaluator_is_not_pretended_scientific_execution():
    led=GateLedger([GateDefinition('G1','x'),GateDefinition('G2','y',('G1',))])
    led.run_evaluators({'G2':lambda:{'status':'PASS'}})
    assert led.status('G1')=='UNRESOLVED'
    assert led.records[0].execution_status=='NOT_EXECUTED'
    assert led.records[1].execution_status=='EXECUTED'
    assert led.qualification('G2')['qualification']=='DIAGNOSTIC_ONLY'


def test_truly_missing_inputs_are_not_run_but_following_independent_gate_runs():
    led=GateLedger([GateDefinition('G0','x'),GateDefinition('G1','y',('G0',)),GateDefinition('G2','independent')])
    called=[]
    def data_missing():
        called.append('G1')
        raise GateInputsUnavailable('missing finite-core NPZ input')
    led.run_evaluators({'G0':lambda:{'status':'FAIL'},'G1':data_missing,
                        'G2':lambda:(called.append('G2') or {'status':'PASS'})})
    assert called==['G1','G2']
    assert led.status('G1')=='NOT_RUN_PREREQUISITE'
    assert 'finite-core NPZ' in led.records[1].reason
    assert led.qualification('G2')['qualification']=='QUALIFIED'


def test_unexpected_exceptions_fail_loudly_not_as_scientific_fail():
    led=GateLedger([GateDefinition('G0','a')])
    def bad(): raise ZeroDivisionError('bug')
    with pytest.raises(ZeroDivisionError):led.run_evaluators({'G0':bad})
    assert led.records==[]


def test_disabled_gate_is_transparent_only_when_its_upstream_qualifies():
    defs=[GateDefinition('G0','a'),GateDefinition('G1','disabled',('G0',),False),GateDefinition('G2','child',('G1',))]
    good=GateLedger(defs);good.run_evaluators({'G0':lambda:{'status':'PASS'},'G2':lambda:{'status':'PASS'}})
    assert good.qualification('G2')['qualification']=='QUALIFIED'
    bad=GateLedger(defs);bad.run_evaluators({'G0':lambda:{'status':'FAIL'},'G2':lambda:{'status':'PASS'}})
    assert bad.qualification('G2')['qualification']=='DIAGNOSTIC_ONLY'
    assert bad.records[1].execution_status=='DISABLED'


def test_strict_dependency_mode_remains_opt_in():
    defs=[GateDefinition('G0','a'),GateDefinition('G1','b',('G0',))]
    default=GateLedger(defs);default.record('G0','FAIL');default.record('G1','PASS')
    assert default.qualification('G1')['qualification']=='DIAGNOSTIC_ONLY'
    strict=GateLedger(defs,strict_dependencies=True);strict.record('G0','FAIL')
    with pytest.raises(GateDependencyError):strict.record('G1','PASS')


def test_invalid_evaluator_result_and_duplicate_gate_rejected():
    led=GateLedger([GateDefinition('G0','a')])
    with pytest.raises(GateError):led.run_evaluators({'G0':lambda:{'status':'FAKE'}})
    led.record('G0','FAIL')
    with pytest.raises(GateAlreadyRecordedError):led.record('G0','PASS')


def test_reveal_rejects_unqualified_downstream_pass_even_after_complete_blind_run(tmp_path):
    root=tmp_path/'A001';out=root/'Test_v0.1.0-outputs';out.mkdir(parents=True)
    write_json(root/'blind_policy.json',{'reveal_allowed_after_modes':['FULL'],'reveal_requires_gate':'G3',
        'reveal_requires_gate_status':['PASS','FAIL'],'block_reveal_on_unresolved':False})
    led=GateLedger([GateDefinition(f'G{i}','q',() if i==0 else (f'G{i-1}',)) for i in range(4)])
    led.run_evaluators({f'G{i}':(lambda i=i:{'status':'FAIL' if i==2 else 'PASS'}) for i in range(4)})
    assert led.status('G3')=='PASS' and led.qualification('G3')['qualification']=='DIAGNOSTIC_ONLY'
    led.write(out/'GATE_LEDGER.json')
    write_json(out/'RUN_SUMMARY.json',{'mode':'FULL','protocol_bundle_sha256':'abc',
        'gate_ledger_sha256':led.to_dict()['ledger_sha256'],'revealed':False})
    make_science_evidence_manifest(out,out/'SCIENCE_EVIDENCE_MANIFEST.json')
    make_output_manifest(out,out/'OUTPUT_MANIFEST.json')
    decision=reveal_eligibility(root,{},out,{'bundle_sha256':'abc'})
    assert decision['eligible'] is False
    assert decision['required_gate_qualification']=='DIAGNOSTIC_ONLY'
    assert decision['required_gate_blocked_by']==['G2']
