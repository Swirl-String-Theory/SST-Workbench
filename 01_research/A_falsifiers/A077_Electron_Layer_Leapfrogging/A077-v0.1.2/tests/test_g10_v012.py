"""A077 v0.1.2 G10 lifecycle regression: no false physics promotion."""
import importlib
import numpy as np
import pytest
from sst_falsifier.gates import GateLedger, GateDefinition, GateError
from sst_falsifier.auto_backend_matrix import assess_numeric_control
from experiment.g10_lifecycle import run_pre_backend_evaluators


def ledger():
    return GateLedger([
        GateDefinition('G0','integrity',()),
        GateDefinition('G2','numeric',('G0',)),
        GateDefinition('G3','physical',('G2',)),
        GateDefinition('G6','unused GPU',('G2',),False),
        GateDefinition('G8','spin',('G3',)),
        GateDefinition('G10','backend parity',('G2',)),
        GateDefinition('G9','reveal',('G8',))])


def pre(led):
    led.record('G0','PASS',reason='test')
    run_pre_backend_evaluators(led, {
        'G2':lambda:{'status':'PASS','reason':'numerical proxy valid'},
        'G3':lambda:{'status':'UNRESOLVED','reason':'no physical spectrum'},
        'G8':lambda:{'status':'UNRESOLVED','reason':'no spinor representation'}
    })


def matrix(reference=(1.,2.,3.),other=(1.,2.,3.),count=2):
    return {'status':'EXECUTION_CONTRACT_PASS' if count>=2 else 'UNRESOLVED',
        'counted_backend_categories':count,
        'scientific':{'py':{'scientific_execution':True,'observable':list(reference)},
                      'cpp':{'scientific_execution':count>=2,'observable':list(other)}}}


def test_g10_is_left_for_framework_runner():
    led=ledger();pre(led)
    assert led.status('G10') is None
    assert led.status('G3')=='UNRESOLVED'
    assert led.status('G6')=='NOT_APPLICABLE'
    assert led.status('G9') is None
    assert led.status('G2')=='PASS'


def test_g10_real_framework_assessment_passes_numerically_without_spin():
    led=ledger();pre(led)
    result=assess_numeric_control(matrix(other=(1,2,3+1e-12)),{'numeric_tolerance_cpp':1e-10})
    assert result['status']=='PASS'
    led.record('G10',result['status'],metrics=result,authority='NUMERIC_INTEGRATION_ONLY')
    assert led.qualification('G10')['qualification']=='QUALIFIED'
    assert led.status('G8')=='UNRESOLVED'
    assert result['physics_qualified'] is False


def test_g10_fails_measurable_backend_mismatch():
    verdict=assess_numeric_control(matrix(other=(1,2,3.2)),{'numeric_tolerance_cpp':1e-10})
    assert verdict['status']=='FAIL'
    assert verdict['relative_errors']['cpp']['passed'] is False


def test_g10_unresolved_if_only_python():
    verdict=assess_numeric_control(matrix(count=1),{'numeric_tolerance_cpp':1e-10})
    assert verdict['status']=='UNRESOLVED'


def test_g10_unresolved_invalid_tolerance():
    verdict=assess_numeric_control(matrix(),{'numeric_tolerance_cpp':-1})
    assert verdict['status']=='UNRESOLVED'


def test_g10_pre_record_is_rejected():
    led=ledger();led.record('G10','PASS')
    with pytest.raises(GateError,match='must not'):
        run_pre_backend_evaluators(led,{})


def test_upstream_fail_not_silently_reclassified_as_backend_pass():
    led=ledger();led.record('G0','PASS')
    run_pre_backend_evaluators(led,{'G2':lambda:{'status':'FAIL'},'G3':lambda:{'status':'UNRESOLVED'},'G8':lambda:{'status':'UNRESOLVED'}})
    assert led.status('G10') is None
    assert led.qualification('G10')['qualification']=='NOT_EVALUATED'


def test_missing_g10_definition_fail_closed():
    led=GateLedger([GateDefinition('G0','start',())])
    with pytest.raises(GateError,match='requires'):
        run_pre_backend_evaluators(led,{})


def test_evaluator_exception_not_silently_swallowed():
    led=ledger();led.record('G0','PASS')
    def broken():raise RuntimeError('bad source')
    with pytest.raises(RuntimeError,match='bad source'):
        run_pre_backend_evaluators(led,{'G2':broken})


def test_numeric_gate_does_not_claim_two_independent_experimental_sources():
    verdict=assess_numeric_control(matrix(),{'numeric_tolerance_cpp':1e-10})
    assert verdict['status']=='PASS' and verdict['physics_qualified'] is False
