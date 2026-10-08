from __future__ import annotations
from pathlib import Path
import argparse,itertools,json,hashlib,shutil
ROOT=Path(__file__).resolve().parents[1]

def loadj(p): return json.loads(p.read_text(encoding='utf-8'))
def b(v): return 'on' if v else 'off'

def conditions(cfg, base_n):
    base=dict(cfg['baseline']); out=[('baseline',base,base_n)]
    # full force cube except baseline all-on
    for mech,elec,bend in itertools.product([False,True],repeat=3):
        if mech and elec and bend: continue
        q=dict(base); q.update(mechforce=mech,elecforce=elec,bendforce=bend)
        out.append((f'force_m{int(mech)}e{int(elec)}b{int(bend)}',q,base_n))
    for name,vals in cfg['factor_sweeps'].items():
        for v in vals:
            q=dict(base); n=base_n
            if name=='resolution_multiplier': n=max(24,int(round(base_n*float(v))))
            else: q[name]=v
            out.append((f'{name}_{str(v).replace(".","p")}',q,n))
    return out

def kp_path(p:Path):
    # KnotPlot accepts forward slashes on Windows and this avoids backslash escaping.
    return p.resolve().as_posix()

def checkpoint_block(rdir:Path,it):
    tag=f'i{it:06d}'
    return '\n'.join(['safe','dowker','length','angle','acn','lnknum','rog','energy','data',f'save {kp_path(rdir/tag)}.txt ascii'])

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--tier',choices=['smoke','pilot','full'],default='pilot'); a=ap.parse_args()
    cfg=loadj(ROOT/'configs/default.json'); tops=loadj(ROOT/'private/topologies.json')
    scripts=ROOT/'campaign'/'scripts'/a.tier
    if scripts.exists(): shutil.rmtree(scripts)
    scripts.mkdir(parents=True)
    manifest={'schema':'A058-CAMPAIGN-MANIFEST-1','tier':a.tier,'conditions':[]}
    counter=0
    for tid in cfg['tiers'][a.tier]:
        top=tops[tid]
        for label,par,n in conditions(cfg,int(top['baseline_n'])):
            cid=f'C{counter:04d}'; counter+=1
            rdir=ROOT/'campaign'/'results'/cid; rdir.mkdir(parents=True,exist_ok=True)
            lines=[f'% A058 anonymous topology {tid}, condition {cid}', 'reset all']
            if top['kind']=='load': lines += [f"load {top['spec']}",f'refine nbeads {n}']
            else: lines += [f"torus {top['p']} {top['q']} {n}"]
            lines += ['mode cb','centre',f"fitto mindist {par['fitto_mindist']}",f"collision {par['collision']}",f"close = {par['close']}",f"max-dr = {par['max_dr']}",f"mechforce = {b(par['mechforce'])}",f"elecforce = {b(par['elecforce'])}",f"bendforce = {b(par['bendforce'])}",f"bencon = {par['bencon']}",f"stusplit = {par['stusplit']}",f"dstep = {par['dstep']}",f"bradius = {par['bradius']}",f"cradius = {par['cradius']}",f"energy model {par['energy_model']}",'version','parameters','energy',f'data open {kp_path(rdir/"metrics.csv")}','data format "/I,/N,/l,/A,/a,/L,/s,/g,/e"','data header']
            cps=cfg['checkpoints']; prev=0
            lines.append(checkpoint_block(rdir,0))
            for cp in cps[1:]:
                lines.append(f'ago {cp-prev}'); lines.append(checkpoint_block(rdir,cp)); prev=cp
            lines += ['data close']
            text='\n'.join(lines)+'\n'
            sp=scripts/f'{cid}.kpc'; sp.write_text(text,encoding='utf-8')
            manifest['conditions'].append({'condition_id':cid,'topology_id':tid,'label':label,'nbeads':n,'components':int(top.get('components',1)),'parameters':par,'script':sp.relative_to(ROOT).as_posix(),'script_sha256':hashlib.sha256(text.encode()).hexdigest()})
    (ROOT/'campaign'/f'manifest_{a.tier}.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    (ROOT/'campaign'/'active_tier.json').write_text(json.dumps({'tier':a.tier},indent=2)+'\n',encoding='utf-8')
    print(f'Generated {len(manifest["conditions"])} KnotPlot scripts for tier={a.tier}')
if __name__=='__main__': main()
