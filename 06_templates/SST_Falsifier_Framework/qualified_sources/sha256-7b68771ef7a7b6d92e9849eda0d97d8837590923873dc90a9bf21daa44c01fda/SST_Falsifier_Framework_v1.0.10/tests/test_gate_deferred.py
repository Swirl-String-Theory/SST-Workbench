from sst_falsifier.gates import GateDefinition,GateLedger

def test_deferred_reveal_record_allowed():
    l=GateLedger([GateDefinition("G0","a"),GateDefinition("G9","r",("G0",))]);l.record("G9","DEFERRED",reason="blind")
    assert l.status("G9")=="DEFERRED"
