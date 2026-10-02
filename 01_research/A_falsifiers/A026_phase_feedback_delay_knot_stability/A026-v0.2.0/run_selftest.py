import sys,tempfile,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'src'))
from sst_phase_delay_falsifier.analysis import load_cfg,predict_all,measure_all
from sst_phase_delay_falsifier.blind import prepare
from sst_phase_delay_falsifier.backend import BACKEND
cfg=load_cfg('configs/basic.json')
cfg['geometry']['n_points']=32; cfg['modal']['m_max']=4
cfg['packet'].update(modes=[2],steps=8,samples=4,total_time_to_tchar=.003,fit_r2_min=0.0,angular_span_min=0.0,coherence_min=0.0,min_valid_modes_per_candidate=1)
cfg['nonlinear'].update(modes=[2],steps=8,samples=4,total_time_to_tchar=.003)
with tempfile.TemporaryDirectory() as td:
    td=Path(td); blind=td/'blind'; reg=td/'reg.json'; reg.write_text(json.dumps({'canonical64_sha256':[]}))
    prepare('examples',blind,'*_i10000.txt',32,128,64,'legacy_audit',reg,1)
    p=predict_all(blind,cfg,td/'p.json'); m=measure_all(blind,cfg,td/'m.json')
    print('backend',BACKEND,'delay_score',p['candidates'][0]['delay_score'],'growth_dimless',m['candidates'][0]['observed_growth_dimensionless'])
    assert p['candidates'] and m['candidates']
print('SELFTEST PASS')
