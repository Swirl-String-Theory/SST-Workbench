import pytest
from sst_falsifier.gates import GateDefinition,GateLedger,GateDependencyError,GateAlreadyRecordedError

def test_dependencies_enforced():
    l=GateLedger([GateDefinition("G0","a"),GateDefinition("G1","b",("G0",))])
    with pytest.raises(GateDependencyError): l.record("G1","PASS")
    l.record("G0","PASS"); l.record("G1","PASS"); assert l.status("G1")=="PASS"

def test_duplicate_gate_rejected():
    l=GateLedger([GateDefinition("G0","a")]);l.record("G0","PASS")
    with pytest.raises(GateAlreadyRecordedError):l.record("G0","FAIL")


def test_not_applicable_is_transparent_not_a_bypass():
    defs=[GateDefinition("G0","a"),GateDefinition("G1","b",("G0",)),GateDefinition("G2","disabled",("G1",),False),GateDefinition("G3","down",("G2",))]
    l=GateLedger(defs);l.record("G0","FAIL");l.record("G1","NOT_RUN_PREREQUISITE");l.record("G2","NOT_APPLICABLE")
    with pytest.raises(GateDependencyError): l.record("G3","PASS")
