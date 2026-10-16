\
from __future__ import annotations
from pathlib import Path
import argparse, hashlib, json, math, shutil
ROOT=Path(__file__).resolve().parents[1]

def loadj(p): return json.loads(p.read_text(encoding='utf-8'))
def kp_path(p:Path): return p.resolve().as_posix()
def ladder():
    return [{'kind':'zero','k':None,'x_log2':None,'multiplier':0.0}] + [
        {'kind':'log','k':k,'x_log2':k/4.0,'multiplier':2.0**(k/4.0)} for k in range(-16,17)
    ]
def checkpoint_block(rdir:Path,it:int):
    tag=f'i{it:06d}'
    return '\n'.join(['safe','dowker','length','distance','angle','acn','lnknum','rog','energy',f'save {kp_path(rdir/tag)}.txt ascii'])
def _value_text(v:float): return format(float(v),'.17g')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--tier',choices=['pilot'],default='pilot'); a=ap.parse_args()
    cfg=loadj(ROOT/'configs/default.json'); priv=loadj(ROOT/'private/axis_map.json')
    scripts=ROOT/'private'/'campaign_scripts'/a.tier
    if scripts.exists(): shutil.rmtree(scripts)
    scripts.mkdir(parents=True)
    results=ROOT/'campaign'/'results'
    if results.exists(): shutil.rmtree(results)
    results.mkdir(parents=True)
    top=priv['topology']['T00']; levels=ladder(); conds=[]; counter=0
    # reset-all master baseline; no relaxation parameter is overridden.
    designs=[('BASE',None,1.0,0.0,None)]
    for axis in cfg['axes']:
        meta=priv['axes'][axis]
        for lv in levels:
            # active-default axes share BASE at m=1; conditional axis needs its own m=1 reference.
            if meta.get('default_enable',False) and lv['kind']=='log' and lv['k']==0: continue
            designs.append((axis,lv['kind'],lv['multiplier'],lv['x_log2'],lv['k']))
    for axis,kind,mult,x,k in designs:
        cid=f'C{counter:04d}'; counter+=1; rdir=results/cid; rdir.mkdir(parents=True)
        lines=[f'% A058-v0.2.0 condition {cid}','reset all',f"load {top['spec']}",f"refine nbeads {top['baseline_n']}",'version','parameters']
        default_value=None; applied_value=None
        if axis!='BASE':
            meta=priv['axes'][axis]; default_value=float(meta['default']); applied_value=default_value*float(mult)
            if meta.get('enable'): lines.append(meta['enable'])
            lines.append(meta['setter'].format(value=_value_text(applied_value)))
        cps=[int(x) for x in cfg['topology']['checkpoints']]; prev=0; lines.append(checkpoint_block(rdir,0))
        for cp in cps[1:]:
            lines.append(f'ago {cp-prev}'); lines.append(checkpoint_block(rdir,cp)); prev=cp
        text='\n'.join(lines)+'\n'; sp=scripts/f'{cid}.kpc'; sp.write_text(text,encoding='utf-8')
        conds.append({'condition_id':cid,'topology_id':'T00','axis_id':axis,'level_kind':kind,'multiplier':mult,'x_log2':x,'k':k,'nbeads':top['baseline_n'],'default_value':default_value,'applied_value':applied_value,'script':sp.relative_to(ROOT).as_posix(),'script_sha256':hashlib.sha256(text.encode()).hexdigest()})
    if len(conds)!=101: raise RuntimeError(f'Expected exactly 101 conditions, got {len(conds)}')
    man={'schema':'A058-STRENGTH-MANIFEST-2','tier':a.tier,'condition_count':len(conds),'checkpoint_count':len(cfg['topology']['checkpoints']),'conditions':conds}
    (ROOT/'campaign'/'manifest_pilot.json').write_text(json.dumps(man,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    (ROOT/'campaign'/'active_tier.json').write_text(json.dumps({'tier':'pilot'},indent=2)+'\n',encoding='utf-8')
    print('Generated 101 trefoil strength-response scripts for tier=pilot')
if __name__=='__main__': main()
