from e012_dynamic.reporting import render_report

def test_report_lists_all_a052_blockers():
    blockers=["DIMENSIONLESS_DYNAMIC_BRANCH_NOT_CONVERGED","NO_PHYSICAL_SCALE_CONTRACT"]
    txt=render_report(version="0.1.1",verdict="DYNAMIC_EIGENBRANCH_NOT_CONVERGED",
        seed_id="S",provider="gilbert",c006_version="0.3.0",preset="full",
        sample_count=5,branch_ok=False,handoff_status="A052_PHYSICAL_HANDOFF_BLOCKED",
        handoff_blockers=blockers)
    assert all(x in txt for x in blockers)
    assert "A052 handoff blockers:" in txt
