from e012_dynamic.reporting import render_report

def test_report_lists_all_a052_blockers():
    blockers=['RPO_BACKGROUND_NOT_QUALIFIED:gilbert','CROSS_PROVIDER_DYNAMIC_AGREEMENT_FAILED','NO_PHYSICAL_SCALE_CONTRACT']
    txt=render_report(verdict='DYNAMIC_EIGENBRANCH_NOT_QUALIFIED',preset='full',
        providers=[{'provider_group':'gilbert','qualified_mode_count':2,'rpo_accepted':False,'numerical_branch_ok':False}],
        cross_provider_ok=False,branch_ok=False,handoff_status='A052_PHYSICAL_HANDOFF_BLOCKED',handoff_blockers=blockers)
    assert all(x in txt for x in blockers)
