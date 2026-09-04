import json
from pathlib import Path
from sst_modal_clock.sc2 import sync_sc2_reporting


def test_sc2_reporting_sync_preserves_stage_a_indeterminate(tmp_path: Path):
    a=tmp_path/'analysis'; a.mkdir()
    (a/'blind_sc2_stage_a_summary.json').write_text(json.dumps({'primary_gate':'INDETERMINATE_SCII_INSUFFICIENT_VALID_COVERAGE'}))
    (a/'blind_sc2_provenance_summary.json').write_text(json.dumps({'primary_gate':'NO_SCII_CERTIFIED_PHASE_CLOCK_FOR_PROVENANCE_TEST'}))
    (a/'blind_sc2_summary.json').write_text(json.dumps({'primary_gate':'NO_SCII_CERTIFIED_PHASE_CLOCK_FOR_PROVENANCE_TEST','n_stage_b_results':0,'n_sc2_mechanism_candidates':0}))
    out=sync_sc2_reporting(tmp_path)
    assert out['overall_primary_gate']=='INDETERMINATE_SCII_INSUFFICIENT_VALID_COVERAGE'
    assert out['stage_a_candidate_status']=='NO_SCII_PROVISIONAL_PHASE_CLOCK'
    assert out['provenance_status']=='NOT_REACHED_NO_CERTIFIED_SCII_CANDIDATE'
    assert out['stage_b_status']=='NOT_REACHED_NO_CERTIFIED_SCII_CANDIDATE'
    assert out['metrics_recomputed'] is False
