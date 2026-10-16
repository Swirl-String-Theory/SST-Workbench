from __future__ import annotations
from pathlib import Path
import argparse,hashlib,json,math,shutil
ROOT=Path(__file__).resolve().parents[1]
def loadj(p): return json.loads(p.read_text(encoding='utf-8'))
def ladder(): return [{'kind':'zero','k':None,'x_log2':None,'multiplier':0.0}]+[{'kind':'log','k':k,'x_log2':k/4.0,'multiplier':2.0**(k/4.0)} for k in range(-16,17)]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--tier',choices=['pilot'],default='pilot');a=ap.parse_args()
    cfg=loadj(ROOT/'configs/default.json'); priv=loadj(ROOT/'private/axis_map.json'); calp=ROOT/'private/install_test_runtime/defaults.json'
    if not calp.is_file(): raise SystemExit('Campaign generation requires successful run_install.cmd first.')
    cal=loadj(calp)
    if not cal.get('pass') or not cal.get('setter_verification') or not cal.get('safe_start'): raise SystemExit('Install calibration did not certify runtime state.')
    defaults=cal['defaults']; sectors=cal['resolved_sectors']; levels=ladder(); conds=[]; counter=0
    # Five sector references, shared by sliders belonging to the same GUI sector.
    for rid in cfg['references']:
        cid=f'C{counter:04d}';counter+=1; conds.append({'condition_id':cid,'role':'reference','reference_id':rid,'axis_id':None,'sector_id':rid,'level_kind':'reference','multiplier':1.0,'x_log2':0.0,'k':0})
    for axis in cfg['axes']:
        meta=priv['axes'][axis]; rid=meta['sector_ref']
        for lv in levels:
            if lv['kind']=='log' and lv['k']==0: continue
            cid=f'C{counter:04d}';counter+=1;conds.append({'condition_id':cid,'role':'sweep','reference_id':rid,'axis_id':axis,'sector_id':rid,'level_kind':lv['kind'],'multiplier':lv['multiplier'],'x_log2':lv['x_log2'],'k':lv['k']})
    if len(conds)!=236: raise RuntimeError(f'Expected 236 conditions, got {len(conds)}')
    man={'schema':'A058-SLIDER-MANIFEST-4','tier':a.tier,'condition_count':len(conds),'axis_count':7,'reference_count':5,'runtime_defaults':{a:float(defaults[priv['axes'][a]['parameter']]) for a in cfg['axes']},'resolved_sector_parameters':sectors,'adaptive_relaxation':cfg['adaptive_relaxation'],'conditions':conds}
    camp=ROOT/'campaign'; results=camp/'results'
    if results.exists(): shutil.rmtree(results)
    results.mkdir(parents=True,exist_ok=True)
    (camp/'manifest_pilot.json').write_text(json.dumps(man,indent=2,sort_keys=True)+'\n',encoding='utf-8');(camp/'active_tier.json').write_text(json.dumps({'tier':'pilot'},indent=2)+'\n',encoding='utf-8')
    print('Generated manifest for 236 adaptive trefoil slider-response conditions (5 references + 7 x 33 perturbations)')
if __name__=='__main__':main()
