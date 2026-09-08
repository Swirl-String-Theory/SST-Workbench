import json,re
from pathlib import Path
from sst_finite_core_falsifier.prepare import prepare

def test_no_free_feedback_delay_parameter_in_configs_or_source():
    root=Path(__file__).parents[1]
    forbidden=re.compile(r'\b(tau_delay|phase_delay|feedback_delay|user_delay|target_phase)\b',re.I)
    # target_phase is allowed only as a boolean audit field, never a config/dynamics parameter.
    for p in root.glob('config/*.json'):
        txt=p.read_text(encoding='utf-8'); assert not re.search(r'"(tau_delay|phase_delay|feedback_delay|user_delay|target_phase)"\s*:',txt,re.I)
    dynamics=(root/'src'/'sst_finite_core_falsifier'/'analyze.py').read_text(encoding='utf-8')+(root/'src'/'sst_finite_core_falsifier'/'eigen.py').read_text(encoding='utf-8')
    assert not forbidden.search(dynamics)

def test_prepare_hides_identity_fields(tmp_path):
    root=Path(__file__).parents[1]; cfg=json.loads((root/'config'/'preset_basic.json').read_text());cfg['carriers']=['TORUS_T2_3'];cfg['axial_ratios']=[.75];cfg['n_values']=[1];cfg['m_values']=[1]
    cp=tmp_path/'cfg.json';cp.write_text(json.dumps(cfg),encoding='utf-8');out=tmp_path/'campaign';s=prepare(root,out,cp)
    pub=(out/'blind_catalog'/'pairs_public.csv').read_text(encoding='utf-8').lower()
    for token in ('torus_t2_3','closed','offset_control','gaussian','axial_ratio'):assert token not in pub
    assert s['n_pairs']==1
