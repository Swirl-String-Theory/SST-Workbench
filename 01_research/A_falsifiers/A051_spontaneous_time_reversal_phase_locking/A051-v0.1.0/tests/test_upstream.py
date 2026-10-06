from pathlib import Path
from sst_trpl.upstream import audit_snapshot

def test_current_snapshot_is_not_physically_ready():
    root=Path(__file__).resolve().parents[1]
    r=audit_snapshot(root/'data/upstream_evidence_snapshot.json')
    assert r['status']=='INDETERMINATE'
    assert 'A048_NO_MATERIAL_PHASE_OBSERVABLE' in r['blockers']
    assert 'A031_NO_CERTIFIED_RPO' in r['blockers']
