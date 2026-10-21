#!/usr/bin/env python3
"""Evidence-only KnotPlot length/curvature/TANF/resolution matrix & plots."""
from pathlib import Path
import sys,json,csv,math
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from run_campaign import MODE_KNOTS,HORIZON,RES,ticks,run_dir,completed,validate_snapshot,digest

def metrics(x):
    v=np.roll(x,-1,axis=0)-x;d=np.linalg.norm(v,axis=1)
    a=x-np.roll(x,1,axis=0);b=v;z=np.roll(x,-1,axis=0)-np.roll(x,1,axis=0)
    denom=np.linalg.norm(a,axis=1)*np.linalg.norm(b,axis=1)*np.linalg.norm(z,axis=1)
    k=np.divide(2*np.linalg.norm(np.cross(a,b),axis=1),denom,out=np.full(len(x),np.inf),where=denom>1e-15)
    centroid=np.mean(x,axis=0)
    return dict(length=float(d.sum()),edge_cv=float(d.std()/d.mean()),kappa_max=float(k.max()),kappa_p99=float(np.percentile(k,99)),
                radius_gyration=float(np.sqrt(np.mean(np.sum((x-centroid)**2,axis=1)))),
                area_x=float(np.sum(np.cross(x,np.roll(x,-1,axis=0)),axis=0)[0]/2),
                area_y=float(np.sum(np.cross(x,np.roll(x,-1,axis=0)),axis=0)[1]/2),
                area_z=float(np.sum(np.cross(x,np.roll(x,-1,axis=0)),axis=0)[2]/2))

def kabsch(a,b):
    a=a-a.mean(axis=0);b=b-b.mean(axis=0)
    u,_,v=np.linalg.svd(a.T@b);d=np.eye(3);d[-1,-1]=np.linalg.det(u@v)
    x=a@u@d@v-b
    return float(np.sqrt(np.mean(np.sum(x*x,axis=1))))
def csv_out(path,rows,keys):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)

def run_data():
    records=[];issues=[];samples={}
    for tier in ['BASIC','SMALL','MEDIUM','FULL']:
      for knot in MODE_KNOTS[tier]:
       for n in RES:
        for arm in ['ON','OFF']:
         d=run_dir(knot,n,tier,arm)
         done=d/'DONE.json'
         if not done.exists():continue
         try:
          meta=json.loads(done.read_text())
          if meta.get('protocol_sha256')!=digest(knot,n,arm) or meta.get('max_iteration')!=HORIZON[tier] or meta.get('status')!='RUNTIME_CHECKPOINTS_COMPLETE':
           issues.append(f'unverifiable: {d}');continue
         except Exception:
          issues.append(f'invalid DONE manifest: {d}');continue
         base=validate_snapshot(d/'i00000.xyz',n)
         if base is None:issues.append('missing baseline '+str(d));continue
         bm=metrics(base)
         for t in ticks(HORIZON[tier]):
          p=validate_snapshot(d/f'i{t:05d}.xyz',n)
          if p is None:continue
          m=metrics(p)
          row=dict(tier=tier,knot=knot,n=n,tanf=arm,iteration=t,**m,
            length_delta_pct=100*(m['length']/bm['length']-1),kappa_max_ratio=m['kappa_max']/bm['kappa_max'],
            indexed_rms=float(np.linalg.norm(p-base,axis=1).mean()),kabsch_rms=kabsch(base,p))
          records.append(row);samples[knot,n,arm,tier,t]=p
    return records,samples,issues

def main():
    out=ROOT/'analysis';out.mkdir(exist_ok=True)
    rows,dat,issues=run_data()
    keys=['tier','knot','n','tanf','iteration','length','edge_cv','kappa_max','kappa_p99','radius_gyration','area_x','area_y','area_z','length_delta_pct','kappa_max_ratio','indexed_rms','kabsch_rms']
    csv_out(out/'matrix_long.csv',rows,keys)
    key_to_metric={(r['knot'],r['n'],r['tanf'],r['tier'],r['iteration']):r for r in rows}
    pair=[];rescmp=[]
    for tier in ['BASIC','SMALL','MEDIUM','FULL']:
      for knot in MODE_KNOTS[tier]:
       for t in ticks(HORIZON[tier]):
        for n in RES:
         a=dat.get((knot,n,'ON',tier,t));b=dat.get((knot,n,'OFF',tier,t))
         if a is not None and b is not None:
          pair.append({'tier':tier,'knot':knot,'n':n,'iteration':t,'tanf_on_off_rms_after_rigid_alignment':kabsch(a,b),
                       'tanf_on_off_length_difference':metrics(a)['length']-metrics(b)['length']})
        for arm in ['ON','OFF']:
         r1=key_to_metric.get((knot,1024,arm,tier,t));r2=key_to_metric.get((knot,2048,arm,tier,t))
         if r1 and r2:
          rescmp.append({'tier':tier,'knot':knot,'iteration':t,'tanf':arm,
            'relative_length_diff_pct':100*(r2['length']/r1['length']-1),
            'relative_kappa_max_diff_pct':100*(r2['kappa_max']/r1['kappa_max']-1),
            'warning':'equal iteration count is not equal physical time'})
    csv_out(out/'tanf_ab.csv',pair,['tier','knot','n','iteration','tanf_on_off_rms_after_rigid_alignment','tanf_on_off_length_difference'])
    csv_out(out/'resolution.csv',rescmp,['tier','knot','iteration','tanf','relative_length_diff_pct','relative_kappa_max_diff_pct','warning'])
    matrix=[]
    for tier in MODE_KNOTS:
     for knot in MODE_KNOTS[tier]:
      for n in RES:
       for arm in ['ON','OFF']:
        observed={r['iteration'] for r in rows if r['tier']==tier and r['knot']==knot and r['n']==n and r['tanf']==arm}
        for t in ticks(HORIZON[tier]):
         matrix.append(dict(tier=tier,knot=knot,n=n,tanf=arm,iteration=t,has_verified_snapshot=int(t in observed)))
    csv_out(out/'coverage.csv',matrix,['tier','knot','n','tanf','iteration','has_verified_snapshot'])
    try:
     import matplotlib
     matplotlib.use('Agg')
     import matplotlib.pyplot as plt
     # One chart per plot, no subplots
     for tier in ['BASIC','SMALL','MEDIUM','FULL']:
      vals=[r for r in rows if r['tier']==tier]
      if not vals:continue
      for metric in ['length_delta_pct','kappa_max_ratio']:
       fig,ax=plt.subplots(figsize=(11,6))
       for (knot,n,arm) in sorted({(r['knot'],r['n'],r['tanf']) for r in vals}):
        vr=sorted([r for r in vals if (r['knot'],r['n'],r['tanf'])==(knot,n,arm)],key=lambda r:r['iteration'])
        ax.plot([r['iteration'] for r in vr],[r[metric] for r in vr],label=f'{knot} N{n} {arm}',alpha=.65)
       ax.set_xlabel('KnotPlot ago iterations (not physical time)');ax.set_ylabel(metric);ax.set_title(f'{tier} numerical relaxation: {metric}')
       if tier in ['BASIC','SMALL']:ax.legend(fontsize='x-small',ncol=2)
       ax.grid(alpha=.25);fig.tight_layout();fig.savefig(out/f'{tier}_{metric}.png',dpi=130);plt.close(fig)
    except ImportError:issues.append('matplotlib missing: no plots generated')
    report={'version':'0.4.0','real_observations':len(rows),'expected_coverage':len(matrix),
            'full_mode_expected_snapshots':len(MODE_KNOTS['FULL'])*len(RES)*2*len(ticks(32000)),
            'issues':issues,'no_data_fabricated':True,
            'scope':'KnotPlot relaxation only; NOT finite-core Euler or Swirl Clock',
            'topology_certification':'UNRESOLVED'}
    (out/'AUDIT.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return 0 if not issues else 2
if __name__=='__main__':raise SystemExit(main())
