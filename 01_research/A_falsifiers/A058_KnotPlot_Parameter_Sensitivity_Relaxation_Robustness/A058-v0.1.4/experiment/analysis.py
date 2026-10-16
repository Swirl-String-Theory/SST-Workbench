from __future__ import annotations
from pathlib import Path
import hashlib, json, math
import numpy as np
from .metrics import read_xyz, curve_metrics, shape_distance

def _rel(a:dict,b:dict):
    vals={}
    for k in set(a)&set(b):
        aa=float(a[k]); bb=float(b[k])
        if not (math.isfinite(aa) and math.isfinite(bb)): continue
        vals[k]=abs(bb-aa)/max(abs(aa),abs(bb),1e-12)
    return (max(vals.values()) if vals else math.nan),vals

def _sha(p:Path):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''): h.update(block)
    return h.hexdigest()

def analyze(root:Path):
    cfg=json.loads((root/'configs/default.json').read_text(encoding='utf-8'))
    mp=root/'campaign'/'manifest_pilot.json'
    rp=root/'campaign'/'runlog_pilot.json'
    runtime_p=root/'campaign'/'runtime_pilot.json'
    if not mp.exists(): return {'available':False,'reason':'Recovered manifest_pilot.json missing'}
    man=json.loads(mp.read_text(encoding='utf-8'))
    conds=man.get('conditions',[])
    cps=[int(x) for x in cfg['checkpoints']]
    tags=[f'i{x:06d}' for x in cps]
    bytid={}
    for c in conds: bytid.setdefault(c['topology_id'],[]).append(c)

    runlog=json.loads(rp.read_text(encoding='utf-8')) if rp.exists() else []
    runtime=json.loads(runtime_p.read_text(encoding='utf-8')) if runtime_p.exists() else {}
    expected=len(conds)*len(cps)
    parsed=0; nonempty=0; csv_nonempty=0; csv_present=0; parse_errors=[]
    metrics={}
    for c in conds:
        cid=c['condition_id']; metrics[cid]={}
        csvp=root/'campaign'/'results'/cid/'metrics.csv'
        if csvp.exists():
            csv_present+=1
            if csvp.stat().st_size>0: csv_nonempty+=1
        for cp,tag in zip(cps,tags):
            p=root/'campaign'/'results'/cid/f'{tag}.txt'
            if p.exists() and p.stat().st_size>0:
                nonempty+=1
                try:
                    x=read_xyz(p); metrics[cid][cp]=curve_metrics(x); parsed+=1
                except Exception as e:
                    parse_errors.append({'condition_id':cid,'checkpoint':cp,'error':str(e)})
            else:
                parse_errors.append({'condition_id':cid,'checkpoint':cp,'error':'missing_or_empty'})

    baselines={tid:next((c for c in cs if c['label']=='baseline'),None) for tid,cs in bytid.items()}
    final_cp=cps[-1]
    def vec(cid,cp=final_cp):
        m=metrics.get(cid,{}).get(cp,{})
        if not m: return {}
        rg=float(m['rg'])
        return {'L_over_Rg':float(m['length'])/rg if rg else math.nan,'edge_cv':float(m['edge_cv'])}

    effects=[]; neg=[]; force=[]; numeric=[]; resolution=[]
    for tid,cs in bytid.items():
        base=baselines[tid]
        if not base or final_cp not in metrics.get(base['condition_id'],{}): continue
        bid=base['condition_id']; bx=None
        if int(base.get('components',1))==1:
            bx=read_xyz(root/'campaign'/'results'/bid/f'i{final_cp:06d}.txt')
        for c in cs:
            cid=c['condition_id']
            if cid==bid or final_cp not in metrics.get(cid,{}): continue
            sr,sp=_rel(vec(bid),vec(cid))
            sd=math.nan
            if bx is not None and int(c.get('components',1))==1:
                sd=shape_distance(bx,read_xyz(root/'campaign'/'results'/cid/f'i{final_cp:06d}.txt'),m=128)
            rec={'topology_id':tid,'condition_id':cid,'label':c['label'],'scalar_rel_max':sr,'scalar_components':sp,'shape_distance':sd}
            effects.append(rec)
            if c['label'].startswith('dstep_'): neg.append(rec)
            elif c['label'].startswith('force_'): force.append(rec)
            elif c['label'].startswith('resolution_multiplier_'): resolution.append(rec)
            elif any(c['label'].startswith(x) for x in ('max_dr_','close_','bencon_','stusplit_')): numeric.append(rec)

    def finite(xs): return [float(x) for x in xs if math.isfinite(float(x))]
    def med(xs):
        q=finite(xs); return float(np.median(q)) if q else math.nan
    def mx(xs):
        q=finite(xs); return max(q) if q else math.nan

    # Stronger null-control check: final coordinate files should be byte-identical.
    null_byte_identity=[]
    for tid,cs in bytid.items():
        base=baselines[tid]
        if not base: continue
        bpath=root/'campaign'/'results'/base['condition_id']/f'i{final_cp:06d}.txt'
        if not bpath.exists(): continue
        bh=_sha(bpath)
        for c in cs:
            if c['label'].startswith('dstep_'):
                p=root/'campaign'/'results'/c['condition_id']/f'i{final_cp:06d}.txt'
                null_byte_identity.append(bool(p.exists() and _sha(p)==bh))

    # Plateau: preserve preregistered shape <= .005 and scalar <=1%, but use scale-free L/Rg only.
    plateaus=[]; plateau_bools=[]
    for tid,base in baselines.items():
        if not base or int(base.get('components',1))!=1: continue
        bid=base['condition_id']
        if 10000 not in metrics.get(bid,{}) or 15000 not in metrics.get(bid,{}): continue
        a=read_xyz(root/'campaign'/'results'/bid/'i010000.txt')
        b=read_xyz(root/'campaign'/'results'/bid/'i015000.txt')
        sd=shape_distance(a,b,m=128)
        sr,_=_rel(vec(bid,10000),vec(bid,15000))
        # edge_cv is a mesh-regularity diagnostic, not a physical scale-invariant shape scalar.
        lr10=metrics[bid][10000]['length']/metrics[bid][10000]['rg']
        lr15=metrics[bid][15000]['length']/metrics[bid][15000]['rg']
        lrrel=abs(lr15-lr10)/max(abs(lr10),abs(lr15),1e-12)
        ok=sd<=cfg['thresholds']['plateau_shape'] and lrrel<=cfg['thresholds']['plateau_scalar_rel']
        plateaus.append({'topology_id':tid,'shape_10k_15k':sd,'L_over_Rg_rel_10k_15k':lrrel,'pass':ok})
        plateau_bools.append(ok)

    # Same-topology anonymous dual-generator pair.
    gp={'available':False,'shape_distance':math.nan,'L_over_Rg_rel':math.nan}
    if baselines.get('T00') and baselines.get('T01'):
        ca=baselines['T00']['condition_id']; cb=baselines['T01']['condition_id']
        try:
            xa=read_xyz(root/'campaign'/'results'/ca/f'i{final_cp:06d}.txt')
            xb=read_xyz(root/'campaign'/'results'/cb/f'i{final_cp:06d}.txt')
            _,parts=_rel(vec(ca),vec(cb))
            gp={'available':True,'shape_distance':shape_distance(xa,xb,m=128),'L_over_Rg_rel':parts.get('L_over_Rg',math.nan)}
        except Exception: pass

    # Relaxation trajectory relative to final for single-component baselines.
    trajectories=[]
    for tid,base in baselines.items():
        if not base or int(base.get('components',1))!=1: continue
        bid=base['condition_id']
        try: xf=read_xyz(root/'campaign'/'results'/bid/f'i{final_cp:06d}.txt')
        except Exception: continue
        for cp in cps[:-1]:
            try:
                x=read_xyz(root/'campaign'/'results'/bid/f'i{cp:06d}.txt')
                trajectories.append({'topology_id':tid,'checkpoint':cp,'shape_to_final':shape_distance(x,xf,m=128)})
            except Exception: pass

    return {
      'schema':'A058-RECOVERY-ANALYSIS-1','available':True,
      'conditions':len(conds),'checkpoints_per_condition':len(cps),
      'expected_coordinate_files':expected,'nonempty_coordinate_files':nonempty,'parseable_coordinate_files':parsed,
      'coordinate_complete_fraction':parsed/expected if expected else 0.0,'parse_errors':parse_errors,
      'metrics_csv_present':csv_present,'metrics_csv_nonempty':csv_nonempty,
      'runlog_entries':len(runlog),'runlog_nonzero_exits':sum(int(r.get('returncode',1))!=0 for r in runlog),
      'runtime':runtime,'effects':effects,
      'negative_control_max_scalar':mx([r['scalar_rel_max'] for r in neg]),
      'negative_control_max_shape':mx([r['shape_distance'] for r in neg]),
      'negative_control_all_final_byte_identical':bool(null_byte_identity) and all(null_byte_identity),
      'force_effect_median_scalar':med([r['scalar_rel_max'] for r in force]),
      'force_effect_median_shape':med([r['shape_distance'] for r in force]),
      'numeric_effect_median_scalar':med([r['scalar_rel_max'] for r in numeric]),
      'numeric_effect_median_shape':med([r['shape_distance'] for r in numeric]),
      'resolution_effect_median_scalar':med([r['scalar_rel_max'] for r in resolution]),
      'resolution_effect_median_shape':med([r['shape_distance'] for r in resolution]),
      'plateau_pass_fraction':sum(plateau_bools)/len(plateau_bools) if plateau_bools else math.nan,
      'plateaus':plateaus,'generator_pair':gp,'trajectories':trajectories
    }
