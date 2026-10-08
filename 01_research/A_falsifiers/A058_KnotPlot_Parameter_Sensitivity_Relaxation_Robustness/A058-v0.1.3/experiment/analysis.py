from __future__ import annotations
from pathlib import Path
import csv,json,math
import numpy as np
from .metrics import read_xyz,shape_distance


def _float(v):
    try: return float(str(v).strip())
    except Exception: return math.nan


def load_manifest(root:Path):
    active=root/'campaign'/'active_tier.json'
    if active.exists():
        try:
            tier=json.loads(active.read_text(encoding='utf-8'))['tier']
            p=root/'campaign'/f'manifest_{tier}.json'
            if p.exists(): return json.loads(p.read_text(encoding='utf-8')),p
        except Exception:
            pass
    for name in ('manifest_full.json','manifest_pilot.json','manifest_smoke.json'):
        p=root/'campaign'/name
        if p.exists(): return json.loads(p.read_text(encoding='utf-8')),p
    return None,None


def load_metric_csv(p:Path):
    if not p.exists(): return []
    with p.open(encoding='utf-8',errors='replace',newline='') as f:
        data=list(csv.reader(f))
    if len(data)<2: return []
    hdr=[h.strip().lower().replace(' ','_') for h in data[0]]
    rows=[]
    for vals in data[1:]:
        if not vals: continue
        rows.append({hdr[i] if i<len(hdr) else f'c{i}':_float(v) for i,v in enumerate(vals)})
    return rows


def final_scalar_vector(rows):
    if not rows: return {}
    r=rows[-1]
    out={}
    skip={'iteration','id','nbeads','n_beads'}
    for k,v in r.items():
        if k in skip or not math.isfinite(v): continue
        out[k]=v
    return out


def rel_effect(a,b):
    keys=set(a)&set(b); vals=[]
    for k in keys:
        scale=max(abs(a[k]),abs(b[k]),1e-12)
        vals.append(abs(b[k]-a[k])/scale)
    return max(vals) if vals else math.nan


def _shape(root:Path,cid_a:str,tag_a:str,cid_b:str,tag_b:str):
    try:
        a=read_xyz(root/'campaign'/'results'/cid_a/f'{tag_a}.txt')
        b=read_xyz(root/'campaign'/'results'/cid_b/f'{tag_b}.txt')
        return shape_distance(a,b,m=128)
    except Exception:
        return math.nan


def _finite(xs): return [float(x) for x in xs if math.isfinite(float(x))]

def _median(xs):
    q=_finite(xs); return float(np.median(q)) if q else math.nan

def _max(xs):
    q=_finite(xs); return max(q) if q else math.nan


def analyze(root:Path):
    man,mp=load_manifest(root)
    if not man: return {'available':False,'reason':'No campaign manifest found.'}
    cfg=json.loads((root/'configs/default.json').read_text(encoding='utf-8'))
    cps=[int(x) for x in cfg['checkpoints']]
    tags=[f'i{x:06d}' for x in cps]
    conds=man['conditions']; byid={c['condition_id']:c for c in conds}
    rows={cid:load_metric_csv(root/'campaign'/'results'/cid/'metrics.csv') for cid in byid}

    complete=[]
    completeness={}
    for cid in byid:
        csv_ok=len(rows[cid])>=len(cps)
        coords=[(root/'campaign'/'results'/cid/f'{tag}.txt').exists() for tag in tags]
        ok=csv_ok and all(coords)
        completeness[cid]={'csv_rows':len(rows[cid]),'coordinate_checkpoints':sum(coords),'expected_checkpoints':len(cps),'complete':ok}
        if ok: complete.append(cid)

    grouped={}
    for c in conds: grouped.setdefault(c['topology_id'],[]).append(c)
    effects=[]; neg=[]; force=[]; numeric=[]; resolution=[]; plateaus=[]
    baselines={}
    for tid,cs in grouped.items():
        base=next((c for c in cs if c['label']=='baseline'),None)
        if not base or not rows[base['condition_id']]: continue
        baselines[tid]=base
        bid=base['condition_id']; bv=final_scalar_vector(rows[bid]); components=int(base.get('components',1))
        for c in cs:
            cid=c['condition_id']
            if c is base or not rows[cid]: continue
            scalar=rel_effect(bv,final_scalar_vector(rows[cid]))
            shape=_shape(root,bid,'i015000',cid,'i015000') if components==1 else math.nan
            rec={'topology_id':tid,'condition_id':cid,'label':c['label'],'scalar_rel_max':scalar,'shape_distance':shape}
            effects.append(rec)
            if c['label'].startswith('dstep_'): neg.append(rec)
            elif c['label'].startswith('force_'): force.append(rec)
            elif c['label'].startswith('resolution_multiplier_'): resolution.append(rec)
            elif any(c['label'].startswith(x) for x in ['max_dr_','close_','bencon_','stusplit_']): numeric.append(rec)
        br=rows[bid]
        if len(br)>=2:
            # By construction the last two data records are 10k and 15k.
            v10=final_scalar_vector(br[-2:-1]); v15=final_scalar_vector(br[-1:])
            plateaus.append({
                'topology_id':tid,
                'scalar_rel_10k_15k':rel_effect(v10,v15),
                'shape_10k_15k':_shape(root,bid,'i010000',bid,'i015000') if components==1 else math.nan
            })

    # Registered anonymous dual-generator comparison T00/T01; semantics remain private until reveal.
    generator={'available':False,'scalar_rel':math.nan,'shape_distance':math.nan}
    if 'T00' in baselines and 'T01' in baselines:
        a=baselines['T00']['condition_id']; b=baselines['T01']['condition_id']
        if rows[a] and rows[b]:
            generator={'available':True,
                       'scalar_rel':rel_effect(final_scalar_vector(rows[a]),final_scalar_vector(rows[b])),
                       'shape_distance':_shape(root,a,'i015000',b,'i015000')}

    th=cfg['thresholds']
    plateau_pass=[]
    for r in plateaus:
        s=r['scalar_rel_10k_15k']; d=r['shape_10k_15k']
        if math.isfinite(s) and math.isfinite(d):
            plateau_pass.append(s<=th['plateau_scalar_rel'] and d<=th['plateau_shape'])

    return {
        'available':True,
        'manifest':str(mp.relative_to(root)),
        'expected_conditions':len(conds),
        'complete_conditions':len(complete),
        'complete_fraction':len(complete)/len(conds) if conds else 0.0,
        'completeness':completeness,
        'effects':effects,
        'negative_control_max_scalar':_max([r['scalar_rel_max'] for r in neg]),
        'negative_control_max_shape':_max([r['shape_distance'] for r in neg]),
        'force_effect_median_scalar':_median([r['scalar_rel_max'] for r in force]),
        'force_effect_median_shape':_median([r['shape_distance'] for r in force]),
        'numeric_effect_median_scalar':_median([r['scalar_rel_max'] for r in numeric]),
        'numeric_effect_median_shape':_median([r['shape_distance'] for r in numeric]),
        'resolution_effect_median_scalar':_median([r['scalar_rel_max'] for r in resolution]),
        'resolution_effect_median_shape':_median([r['shape_distance'] for r in resolution]),
        'plateau_pass_fraction':(sum(plateau_pass)/len(plateau_pass)) if plateau_pass else math.nan,
        'plateaus':plateaus,
        'generator_pair':generator,
    }
