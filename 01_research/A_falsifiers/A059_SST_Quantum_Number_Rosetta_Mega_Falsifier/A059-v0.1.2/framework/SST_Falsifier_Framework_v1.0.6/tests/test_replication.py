from sst_falsifier.replication import assess_replication,ReplicationEvidenceError
import pytest

def test_synthetic_groups_do_not_close_cross_source_gate():
    rows=[
      {"source_group":"SYNTH_A","evidence_class":"synthetic_control","generator_id":"same","provenance_family":"synthetic-v1","status":"PASS"},
      {"source_group":"SYNTH_E","evidence_class":"synthetic_control","generator_id":"same","provenance_family":"synthetic-v1","status":"PASS"},
    ]
    r=assess_replication(rows)
    assert r["G5_CONTROL_REPLICATION"]=="PASS"
    assert r["G5_CROSS_SOURCE_REPLICATION"]=="NOT_RUN_PREREQUISITE"
    assert not r["joint_support_eligible"]

def test_independent_provenance_can_close_cross_source_gate():
    rows=[
      {"source_group":"PKLSA","independence_family":"pklsa","evidence_class":"independent_source","provenance_family":"archive-a","status":"PASS"},
      {"source_group":"RIDGERUNNER","independence_family":"ridgerunner","evidence_class":"independent_source","provenance_family":"archive-b","status":"PASS"},
    ]
    r=assess_replication(rows)
    assert r["G5_CROSS_SOURCE_REPLICATION"]=="PASS"
    assert r["joint_support_eligible"]

def test_same_generator_blocks_independent_claim():
    rows=[
      {"source_group":"A","independence_family":"a","evidence_class":"independent_source","provenance_family":"pa","generator_id":"same","status":"PASS"},
      {"source_group":"B","independence_family":"b","evidence_class":"independent_source","provenance_family":"pb","generator_id":"same","status":"PASS"},
    ]
    r=assess_replication(rows)
    assert r["G5_CROSS_SOURCE_REPLICATION"]=="UNRESOLVED"
    assert not r["joint_support_eligible"]

def test_evidence_class_required():
    with pytest.raises(ReplicationEvidenceError):
        assess_replication([{"source_group":"x","status":"PASS"}])
