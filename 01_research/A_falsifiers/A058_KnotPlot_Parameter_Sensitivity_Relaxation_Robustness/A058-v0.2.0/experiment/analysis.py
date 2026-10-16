\
from __future__ import annotations
from pathlib import Path
import json,math
import numpy as np
from .metrics import read_xyz,curve_metrics,shape_distance

def _rel(a,b):
    vals={}
    for k in ('L_over_Rg','edge_cv'):
        aa=float(a[k]);bb=float(b[k]);vals[k]=abs(bb-aa)/max(abs(aa),abs(bb),1e-12)
    return max(vals.values()),vals

def analyze(root:Path):
    cfg=json.loads((root/'configs/default.json').read_text(encoding='utf-8')); mp=root/'campaign/manifest_pilot.json'; rp=root/'campaign/runlog_pilot.json'; rt=root/'campaign/runtime_pilot.json'
    if not mp.exists(): return {'available':False,'reason':'manifest_pilot.json missing'}
    man=json.loads(mp.read_text(encoding='utf-8')); conds=man['conditions']; cps=[int(x) for x in cfg['topology']['checkpoints']]; final=cps[-1]
    runlog=json.loads(rp.read_text(encoding='utf-8')) if rp.exists() else []; runtime=json.loads(rt.read_text(encoding='utf-8')) if rt.exists() else {}
    parsed={}; errors=[]
    for c in conds:
        cid=c['condition_id']; parsed[cid]={}
        for cp in cps:
            p=root/'campaign/results'/cid/f'i{cp:06d}.txt'
            try:
                x=read_xyz(p); parsed[cid][cp]={'metrics':curve_metrics(x),'path':str(p)}
            except Exception as e: errors.append({'condition_id':cid,'checkpoint':cp,'error':str(e)})
    expected=len(conds)*len(cps); complete=(expected-len(errors))/expected if expected else 0.0
    base=next(c for c in conds if c['axis_id']=='BASE'); base_id=base['condition_id']
    byaxis={a:[] for a in cfg['axes']}
    for c in conds:
        if c['axis_id'] in byaxis: byaxis[c['axis_id']].append(c)
    # axis references: active-default axes use BASE; conditional axis uses its own m=1 condition.
    refs={}
    for axis,cs in byaxis.items():
        own=next((c for c in cs if c['level_kind']=='log' and c['k']==0),None)
        refs[axis]=own or base
    def scal(cid):
        m=parsed[cid][final]['metrics']; rg=float(m['rg']); return {'L_over_Rg':float(m['length'])/rg,'edge_cv':float(m['edge_cv'])}
    responses=[]
    for axis,cs in byaxis.items():
        rid=refs[axis]['condition_id']; rx=read_xyz(root/'campaign/results'/rid/f'i{final:06d}.txt'); rs=scal(rid)
        for c in sorted(cs,key=lambda z:(z['multiplier'])):
            cid=c['condition_id']; x=read_xyz(root/'campaign/results'/cid/f'i{final:06d}.txt'); sd=shape_distance(rx,x,m=128); sr,parts=_rel(rs,scal(cid))
            responses.append({'axis_id':axis,'condition_id':cid,'reference_condition_id':rid,'multiplier':c['multiplier'],'x_log2':c['x_log2'],'k':c['k'],'level_kind':c['level_kind'],'shape_distance':sd,'scalar_rel_max':sr,'scalar_components':parts})
    # ladder integrity
    ladder_ok=True; ladder_detail=[]
    for axis,cs in byaxis.items():
        logs=sorted([c for c in cs if c['level_kind']=='log'],key=lambda c:c['k'])
        # active axes omit k=0; conditional includes it. Check every present point against exact formula and reciprocal values when both present.
        for c in logs:
            exp=2.0**(float(c['k'])/4.0); err=abs(float(c['multiplier'])-exp); ladder_detail.append({'axis_id':axis,'k':c['k'],'error':err}); ladder_ok &= err<=1e-14
    # local robustness for active-default axes only S0/S1; conditional S2 compared to its own m=1 reference reported separately.
    local={}; fits={}; liveness={}
    for axis in cfg['axes']:
        rr=[r for r in responses if r['axis_id']==axis]; local_pts=[r for r in rr if r['x_log2'] is not None and abs(float(r['x_log2']))==0.25]
        local[axis]={'max_shape':max([r['shape_distance'] for r in local_pts],default=math.nan),'points':local_pts}
        extremes=[r['shape_distance'] for r in rr if r['level_kind']=='log' and r['k'] in (-16,16)]
        liveness[axis]=max(extremes,default=math.nan)
        fitpts=[r for r in rr if r['x_log2'] is not None and abs(float(r['x_log2']))<=cfg['thresholds']['quadratic_local_abs_log2']]
        if len(fitpts)>=5:
            xx=np.array([r['x_log2'] for r in fitpts],float); yy=np.array([r['shape_distance'] for r in fitpts],float); co=np.polyfit(xx,yy,2); pred=np.polyval(co,xx); ssr=float(np.sum((yy-pred)**2)); sst=float(np.sum((yy-yy.mean())**2)); r2=1.0-ssr/sst if sst>0 else 1.0
            fits[axis]={'a':float(co[0]),'b':float(co[1]),'c':float(co[2]),'r2':r2,'n':len(fitpts)}
        else: fits[axis]={'r2':math.nan,'n':len(fitpts)}
    # reciprocal asymmetry diagnostic
    asym={}
    for axis in cfg['axes']:
        mpk={r['k']:r for r in responses if r['axis_id']==axis and r['k'] is not None}
        vals=[]
        for k in range(1,17):
            if k in mpk and -k in mpk: vals.append(abs(mpk[k]['shape_distance']-mpk[-k]['shape_distance']))
        asym[axis]={'median_abs':float(np.median(vals)) if vals else math.nan,'max_abs':max(vals) if vals else math.nan,'pairs':len(vals)}
    # conditional zero equivalence to master reset-all baseline
    s2zero=next(r for r in responses if r['axis_id']=='S2' and r['level_kind']=='zero'); zx=read_xyz(root/'campaign/results'/s2zero['condition_id']/f'i{final:06d}.txt'); bx=read_xyz(root/'campaign/results'/base_id/f'i{final:06d}.txt'); zshape=shape_distance(bx,zx,m=128); zscalar,zparts=_rel(scal(base_id),scal(s2zero['condition_id']))
    return {'schema':'A058-STRENGTH-ANALYSIS-2','available':True,'condition_count':len(conds),'expected_condition_count':101,'checkpoints_per_condition':len(cps),'expected_coordinate_files':expected,'parseable_coordinate_files':expected-len(errors),'coordinate_complete_fraction':complete,'parse_errors':errors,'runlog_entries':len(runlog),'runlog_nonzero_exits':sum(int(r.get('returncode',1))!=0 for r in runlog),'runtime':runtime,'ladder_ok':bool(ladder_ok),'ladder_detail':ladder_detail,'responses':responses,'axis_references':{a:refs[a]['condition_id'] for a in refs},'local':local,'liveness_extreme_shape':liveness,'quadratic_local_fits':fits,'reciprocal_asymmetry':asym,'conditional_zero_equivalence':{'shape_distance':zshape,'scalar_rel_max':zscalar,'scalar_components':zparts,'condition_id':s2zero['condition_id'],'baseline_condition_id':base_id}}
