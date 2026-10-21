#!/usr/bin/env python3
"""KnotPlot long-horizon TANF resolution matrix. Real checkpoints only; no synthetic results."""
from pathlib import Path
import argparse, csv, json, hashlib, math
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
TIMES=[0,1,8,32,128,512,2048,8192,32000]
KNOTS=['5_2','6_1']
RES=[1024,2048]
ARMS=['ON','OFF']

def load(path,n):
    rows=[]
    for l in path.read_text(encoding='utf-8-sig').splitlines():
        l=l.strip()
        if not l or l.lower().startswith('component'):continue
        c=l.split()
        if len(c)!=3:raise ValueError(f'{path}: unexpected record: {l[:100]}')
        rows.append([float(x) for x in c])
    p=np.asarray(rows,dtype=np.float64)
    if p.shape!=(n,3) or not np.isfinite(p).all(): raise ValueError(f'{path}: wrong shape {p.shape}')
    return p

def curvature(p):
    before=p-np.roll(p,1,axis=0)
    after=np.roll(p,-1,axis=0)-p
    chord=np.roll(p,-1,axis=0)-np.roll(p,1,axis=0)
    den=np.linalg.norm(before,axis=1)*np.linalg.norm(after,axis=1)*np.linalg.norm(chord,axis=1)
    num=2*np.linalg.norm(np.cross(before,after),axis=1)
    return np.divide(num,den,out=np.full(len(p),np.inf),where=den>1e-14)

def measures(p):
    v=np.roll(p,-1,axis=0)-p;edge=np.linalg.norm(v,axis=1)
    k=curvature(p); center=p.mean(axis=0)
    b=p-center
    cov=(b.T@b)/len(p)
    ew=np.maximum(0,np.linalg.eigvalsh(cov))
    return {'length':float(edge.sum()),'edge_mean':float(edge.mean()),'edge_cv':float(edge.std()/edge.mean()),
        'kappa_max':float(k.max()),'kappa_p99':float(np.percentile(k,99)),
        'kappa_radius_min':float(1/k.max()), 'cov_eig_min':float(ew[0]),
        'cov_eig_mid':float(ew[1]),'cov_eig_max':float(ew[2]),
        'radius_gyration':float(np.sqrt((b*b).sum(axis=1).mean())),
        'centroid_x':float(center[0]),'centroid_y':float(center[1]),'centroid_z':float(center[2])}

def kabsch_rms(a,b):
    a=a-a.mean(axis=0);b=b-b.mean(axis=0)
    u,s,vt=np.linalg.svd(a.T@b);d=np.eye(3);d[2,2]=np.linalg.det(u@vt)
    delta=a@u@d@vt-b
    return float(np.sqrt((delta*delta).sum(axis=1).mean()))

def from_baseline(base, p):
    x=p-base
    return {'indexed_rms':float(np.sqrt(np.mean(np.sum(x*x,axis=1)))),
        'max_displacement':float(np.linalg.norm(x,axis=1).max()),
        'kabsch_rms':kabsch_rms(base,p)}

def sample_periodic(p,n=512):
    """Arc-length polygonal resampling for cross-resolution *shape* comparison only."""
    d=np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1);s=np.r_[0,np.cumsum(d)]
    xi=np.arange(n)*s[-1]/n
    return np.column_stack([np.interp(xi,s,np.r_[p[:,j],p[0,j]]) for j in range(3)])

def cyclic_kabsch(a,b,coarse=16):
    """Optimize cyclic bead shift to avoid interpreting label slip as gross distortion."""
    # For n=512: 32 candidates plus local refinements; fast enough for ordinary runs.
    n=len(a)
    best=(math.inf,0)
    for shift in range(0,n,coarse):
        v=kabsch_rms(a,np.roll(b,shift,axis=0))
        if v<best[0]:best=(v,shift)
    anchor=best[1]
    for offs in range(-coarse+1,coarse):
        shift=(anchor+offs)%n
        v=kabsch_rms(a,np.roll(b,shift,axis=0))
        if v<best[0]: best=(v,shift)
    return best

def collate(tier):
    rows=[];datasets={};issues=[]
    for knot in KNOTS:
      for N in RES:
       for arm in ARMS:
        d=root_for(tier,knot,N,arm)
        existing={}
        for it in TIMES:
          f=d/f'i{it:05d}.xyz'
          if f.is_file():
            try: existing[it]=load(f,N)
            except Exception as e:issues.append(str(e))
        if 0 not in existing:
          issues.append(f'{tier}/{knot}/N{N:04d}/TANF_{arm}: missing i00000 baseline')
        for t in TIMES:
          if t not in existing:continue
          p=existing[t];m=measures(p)
          start=existing.get(0)
          ds=from_baseline(start,p) if start is not None else {'indexed_rms':math.nan,'max_displacement':math.nan,'kabsch_rms':math.nan}
          row={'tier':tier,'knot':knot,'N':N,'tanforce':arm,'iteration':t,'has_snapshot':1,**m,**ds,
                'baseline_equals_current':int(start is not None and np.array_equal(start,p))}
          rows.append(row)
          datasets[(knot,N,arm,t)]=p
        for aa,bb in zip(TIMES[:-1],TIMES[1:]):
          if aa in existing and bb in existing and np.array_equal(existing[aa],existing[bb]):
            issues.append(f'{tier}/{knot}/N{N}/{arm}: identical consecutive snapshots {aa}→{bb}')
    return rows,datasets,issues

def root_for(tier,knot,N,arm):return ROOT/'checkpoints'/tier/knot/f'N{N:04d}'/f'TANF_{arm}'

def save_csv(path,rows):
    if not rows:return
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--tier',choices=['PILOT','FULL'],default='PILOT');opt=ap.parse_args()
    rows,dat,issues=collate(opt.tier)
    out=ROOT/'analysis'/opt.tier;out.mkdir(parents=True,exist_ok=True)
    save_csv(out/'matrix_long.csv',rows)
    pairrows=[];scale_rows=[]
    for knot in KNOTS:
      for N in RES:
       for t in TIMES:
        a=dat.get((knot,N,'ON',t));b=dat.get((knot,N,'OFF',t))
        if a is not None and b is not None:
          y=from_baseline(a,b)
          pairrows.append({'knot':knot,'N':N,'iteration':t,'on_off_rms':y['indexed_rms'], 'on_off_kabsch':y['kabsch_rms']})
      for arm in ARMS:
       for t in TIMES:
        a=dat.get((knot,1024,arm,t));b=dat.get((knot,2048,arm,t))
        if a is not None and b is not None:
          aa=sample_periodic(a);bb=sample_periodic(b)
          f,shift=cyclic_kabsch(aa,bb)
          scale_rows.append({'knot':knot,'tanforce':arm,'iteration':t,'RMS_1024_2048_shape':f,'cyclic_shift_512':shift})
    save_csv(out/'tanf_on_off.csv',pairrows)
    save_csv(out/'resolution_1024_2048.csv',scale_rows)
    for knot in KNOTS:
      for N in RES:
        x=dat.get((knot,N,'ON',0));y=dat.get((knot,N,'OFF',0))
        if x is not None and y is not None and not np.array_equal(x,y):
          issues.append(f'{opt.tier}/{knot}/N{N}: unequal A/B baseline (FAIL)')
    gate={'version':'v0.2.0','tier':opt.tier,'total_measured_snapshots':len(dat),
          'expected_snapshots':2*2*2*(6 if opt.tier=='PILOT' else 9),
          'complete':len(dat)==2*2*2*(6 if opt.tier=='PILOT' else 9),
          'issues':issues,'science_scope':'Numerical KnotPlot relaxation only; topology/Euler UNRESOLVED',
          'long_run_promotion':'MANUAL_REVIEW_REQUIRED' if opt.tier=='PILOT' else 'NOT_APPLICABLE',
          'resolution_test_note':'Same iteration number is NOT a continuum-converged physical time; N changes solver discretization.'}
    (out/'audit.json').write_text(json.dumps(gate,indent=2)+'\n')
    try:
      import matplotlib
      matplotlib.use('Agg')
      import matplotlib.pyplot as plt
      if rows:
       for metric, fname in [('length','length_vs_iteration.png'),('kappa_max','max_curvature_vs_iteration.png'),('kabsch_rms','shape_change_vs_iteration.png')]:
        fig,ax=plt.subplots(figsize=(9,5))
        for knot in KNOTS:
         for N in RES:
          for arm in ARMS:
           r=sorted((r for r in rows if r['knot']==knot and r['N']==N and r['tanforce']==arm),key=lambda x:x['iteration'])
           if r:ax.plot([x['iteration'] for x in r],[x[metric] for x in r],marker='o',label=f'{knot} N{N} TANF {arm}')
        ax.set_xscale('symlog',linthresh=1)
        ax.set_xlabel('Atomic KnotPlot iterations (0,1,8,...)')
        ax.set_ylabel(metric+' [KnotPlot geometry units]')
        ax.legend(fontsize='small',ncol=2)
        ax.grid(alpha=.2);fig.tight_layout();fig.savefig(out/fname,dpi=150);plt.close(fig)
      if pairrows:
       fig,ax=plt.subplots(figsize=(9,5))
       for knot in KNOTS:
        for N in RES:
         r=sorted((r for r in pairrows if r['knot']==knot and r['N']==N),key=lambda x:x['iteration'])
         if r:ax.plot([x['iteration'] for x in r],[x['on_off_kabsch'] for x in r],marker='o',label=f'{knot} N{N}')
       ax.set_xscale('symlog',linthresh=1);ax.set_xlabel('Atomic KnotPlot iterations');ax.set_ylabel('A/B Kabsch RMS')
       ax.legend();ax.grid(alpha=.2);fig.tight_layout();fig.savefig(out/'tanf_effect_vs_iteration.png',dpi=150);plt.close(fig)
    except ImportError:issues.append('matplotlib unavailable: CSV and JSON still written')
    print(json.dumps({'tier':opt.tier,'collected':len(dat),'expected':gate['expected_snapshots'],'issues':issues[:15], 'output':str(out)},indent=2))
    return 0 if len(dat)==gate['expected_snapshots'] and not issues else 2
if __name__=='__main__':raise SystemExit(main())
