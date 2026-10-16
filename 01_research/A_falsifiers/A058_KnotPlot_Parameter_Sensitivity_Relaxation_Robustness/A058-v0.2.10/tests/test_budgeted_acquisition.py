from pathlib import Path
import json,math,hashlib
import pytest
ROOT=Path(__file__).resolve().parents[1]

def test_registered_budgets_and_selection_counts():
    cfg=json.loads((ROOT/'configs/default.json').read_text())
    assert cfg['response_budgets']['BASIC']['checkpoints']==[32,128,512]
    assert cfg['response_budgets']['2048']['checkpoints']==[32,128,512,2048]
    assert cfg['response_budgets']['32768']['checkpoints']==[32,128,512,2048,8192,32768]
    assert cfg['response_budgets']['32768']['max_conditions']==31
    assert len(cfg['axes'])==8 and 6+1+8*33==271
    cmd=(ROOT/'run_all.cmd').read_text().lower()
    assert 'goto budget' in cmd and 'tools\\run_budget.py %mode%' in cmd
    assert (ROOT/'run_pilot_all.cmd').read_text().startswith('@echo off')


def test_fixed_checkpoint_budget_does_not_claim_convergence():
    c=json.loads((ROOT/'science_contract.json').read_text())
    e={x['id']:x for x in c['equations']}
    assert 'matched' in e['E6']['purpose'].lower()
    assert '32768' in e['E4']['latex']
    assert c['budget_design']['heavy_max_conditions']==31
    assert c['budget_design']['registered_population']==271
    assert 'no_attractor_claim' in (ROOT/'tools/budget_acquisition.py').read_text()


def _curve(offset):
    import numpy as np
    ts=np.linspace(0,2*math.pi,300,endpoint=False)
    r=2+np.cos(3*ts)
    return np.column_stack((r*np.cos(2*ts)+offset*np.cos(ts),r*np.sin(2*ts),np.sin(3*ts)))


def test_heavy_selection_from_matched_earlier_run_only(tmp_path,monkeypatch):
    from tools import run_budget as driver
    # Reuse frozen design generation shape, do not need real KnotPlot or installer.
    from tools.generate_campaign import ladder
    conditions=[];idx=0
    for r in range(6):
        conditions.append({'condition_id':f'C{idx:04d}','role':'reference','reference_id':f'R{r}','sector_id':f'R{r}','axis_id':None,'multiplier':1.0});idx+=1
    conditions.append({'condition_id':f'C{idx:04d}','role':'activation_control','reference_id':'R2','sector_id':'R2','axis_id':None,'multiplier':1.0});idx+=1
    axes=['R0','R0','R1','R2','R2','R3','R4','R5']
    for j,rid in enumerate(axes):
        for lv in ladder():
            if lv['kind']=='log' and lv['k']==0:continue
            conditions.append({'condition_id':f'C{idx:04d}','role':'sweep','reference_id':rid,'sector_id':rid,'axis_id':f'S{j}',
                   'level_kind':lv['kind'],'multiplier':lv['multiplier'],'k':lv['k']});idx+=1
    assert len(conditions)==271
    root=tmp_path/'test_root'
    (root/'private/install_test_runtime').mkdir(parents=True)
    (root/'configs').mkdir()
    (root/'configs/default.json').write_text((ROOT/'configs/default.json').read_text())
    seedfile=root/'private/install_test_runtime/trefoil_install_test.txt';seedfile.write_text('test seed')
    sha=hashlib.sha256(seedfile.read_bytes()).hexdigest()
    (root/'private/install_test_runtime/defaults.json').write_text(json.dumps({'shared_seed_sha256':sha}))
    old=root/'campaign/runs/2048';(old/'results').mkdir(parents=True)
    rows=[]
    for c in conditions:
        cid=c['condition_id'];role=c['role']
        good=role!='sweep' or c['k'] in (-1,1,16,None)
        rows.append({'condition_id':cid,'status':'PASS' if good else 'FAIL'})
        if good:
            folder=old/'results'/cid;folder.mkdir()
            xx=_curve(0.0 if role!='sweep' else (.012 if c['k']==-1 else .04 if c['k']==1 else .08))
            (folder/'final.txt').write_text(''.join(f'{x:.15g} {y:.15g} {z:.15g}\n' for x,y,z in xx))
    (old/'runlog.json').write_text(json.dumps({'conditions':rows}))
    (old/'manifest.json').write_text(json.dumps({'conditions':conditions}))
    (old/'runtime.json').write_text(json.dumps({'iterations_per_condition':2048,'shared_seed_sha256':sha}))
    (old/'summary.json').write_text(json.dumps({'complete':False}))
    monkeypatch.setattr(driver,'ROOT',root)
    selected,sel=driver.heavy_selection({'conditions':conditions},old)
    assert len(selected)==31
    assert sel['selected_count']==31
    assert len({x['condition_id'] for x in selected})==31
    assert sum(x['role']=='reference' for x in selected)==6
    assert sum(x['role']=='activation_control' for x in selected)==1
    assert sum(x['role']=='sweep' for x in selected)==24
    assert sel['source_budget']==2048
    assert sel['source_runlog_sha256']==hashlib.sha256((old/'runlog.json').read_bytes()).hexdigest()


def test_graphics_fatal_error_detected_without_waiting_180_seconds(tmp_path):
    from tools.budget_acquisition import _fatal
    log=tmp_path/'sector.log';log.write_text('freeglut  ERROR: Function <glutSetWindow> called without first calling glutInit.')
    class Proc:
        def poll(self):return None
    class Fake:
        proc=Proc()
    with pytest.raises(RuntimeError,match='freeglut'):
        _fatal(log,Fake(),'probe')
