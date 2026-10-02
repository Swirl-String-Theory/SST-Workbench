import json
from pathlib import Path

from sst_modal_clock.sc2 import analyze_sc2_provenance, analyze_sc2_stage_b


def _write_json(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj), encoding='utf-8')


def test_no_candidate_preserves_stage_a_indeterminate(tmp_path, monkeypatch):
    work=tmp_path/'w'; (work/'analysis').mkdir(parents=True); (work/'private').mkdir(parents=True)
    _write_json(work/'analysis/blind_sc2_stage_a_summary.json', {'primary_gate':'INDETERMINATE_SCII_INSUFFICIENT_VALID_COVERAGE'})
    _write_json(work/'analysis/sc2_candidates.json', {'candidates':[]})
    _write_json(work/'analysis/sc2_candidates_provisional.json', {'candidates':[]})
    # Empty blind catalog is sufficient for a downstream-not-reached reporting test.
    (work/'blind_catalog.jsonl').write_text('', encoding='utf-8')
    prov=analyze_sc2_provenance(work,{})
    assert prov['primary_gate']=='INDETERMINATE_SCII_INSUFFICIENT_VALID_COVERAGE'
    assert prov['provenance_status']=='NOT_REACHED_NO_CERTIFIED_SCII_CANDIDATE'
    final=analyze_sc2_stage_b(work,{})
    assert final['primary_gate']=='INDETERMINATE_SCII_INSUFFICIENT_VALID_COVERAGE'
    assert final['overall_primary_gate']==final['primary_gate']
    assert final['stage_a_candidate_status']=='NO_SCII_PROVISIONAL_PHASE_CLOCK'
    assert final['mesh_gauge_status']=='NOT_REACHED_NO_PROVISIONAL_SCII_CANDIDATE'
    assert final['provenance_status']=='NOT_REACHED_NO_CERTIFIED_SCII_CANDIDATE'
    assert final['stage_b_status']=='NOT_REACHED_NO_CERTIFIED_SCII_CANDIDATE'
