import json
from pathlib import Path
from sst_finite_core_falsifier.prepare import prepare
from sst_finite_core_falsifier.workflow import run_blind
from sst_finite_core_falsifier.reveal import reveal

def test_blind_seal_reveal_smoke(tmp_path):
    root=Path(__file__).parents[1]; cfg=json.loads((root/'config'/'preset_basic.json').read_text())
    cfg.update({'require_native':False,'carriers':['TORUS_T2_3'],'axial_ratios':[-.75],'m_values':[1],'n_values':[1],'radial_levels':[18,22,26],'radial_n_dispersion':26,'phase_permutations':9})
    cp=tmp_path/'cfg.json';cp.write_text(json.dumps(cfg),encoding='utf-8');camp=tmp_path/'campaign';blind=tmp_path/'blind';rev=tmp_path/'reveal'
    p=prepare(root,camp,cp); assert p['n_pairs']==1
    b=run_blind(root,camp/'blind_catalog',blind,cp); assert b['n_pairs']==1 and b['explicit_delay_parameter_used'] is False
    r=reveal(root,blind,camp/'blind_catalog',cp,camp/'private',rev); assert r['n_pairs']==1 and r['explicit_delay_parameter_used'] is False
    assert (blind/'SEALED_MANIFEST.json').exists() and (rev/'CONCLUSIONS.md').exists()
