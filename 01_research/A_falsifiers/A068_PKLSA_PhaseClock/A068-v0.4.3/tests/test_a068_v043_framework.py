"""Requires the officially pinned SST Falsifier Framework v1.0.10 runtime.

Deliberately skip outside the canonical user Workbench, rather than substitute
an invented framework implementation.
"""
import pytest

def test_framework_v110_fail_does_not_stop_but_blocks_authority():
    try:
        from sst_falsifier.gates import GateLedger,GateDefinition
    except ImportError:
        pytest.skip('Official installed framework 1.0.10 unavailable in local build environment')
    ledger=GateLedger([
        GateDefinition('G0','source'),GateDefinition('G1','independent check',('G0',)),
        GateDefinition('G2','scientific downstream',('G1',))])
    ledger.run_evaluators({
        'G0':lambda:{'status':'PASS'},
        'G1':lambda:{'status':'FAIL'},
        'G2':lambda:{'status':'PASS','metrics':{'independent_measurement':1.0}}})
    assert ledger.status('G2')=='PASS'
    assert ledger.qualification('G2')['qualification']=='DIAGNOSTIC_ONLY'
    assert ledger.qualification('G2')['allows_dependent_claim'] is False
