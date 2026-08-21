import os,sys,tempfile,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'src'))
from sst_phase_delay_falsifier.analysis import load_cfg,predict_all,measure_all
from sst_phase_delay_falsifier.blind import prepare
from sst_phase_delay_falsifier.backend import BACKEND
cfg=load_cfg('configs/basic.json'); cfg['geometry']['n_points']=32; cfg['modal']['m_max']=4; cfg['nonlinear'].update(steps=8,samples=4,max_modes=1,total_time_to_tchar=.005)
with tempfile.TemporaryDirectory() as td:
    td=Path(td); blind=td/'blind'; prepare('examples',blind,'*_i10000.txt',32)
    p=predict_all(blind,cfg,td/'p.json'); m=measure_all(blind,cfg,td/'m.json')
    print('backend',BACKEND,'delay_score',p['candidates'][0]['delay_score'],'growth',m['candidates'][0]['observed_growth'])
    assert p['candidates'] and m['candidates']
print('SELFTEST PASS')
