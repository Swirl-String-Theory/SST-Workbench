#!/usr/bin/env python3
"""F005 v0.4.3 proxy-family-disjoint DEVELOPMENT validation.

Uses v0.4.2 accepted input-only candidate edges; TRAIN+VALIDATION become a
previously exposed DEVELOPMENT pool. Never indexes TEST/OOD measured outputs.
Does NOT claim independent publisher family identification or blind validation.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, time
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter, defaultdict
import numpy as np

VERSION='0.4.3'
SEED=20261020
ANCHORS=(.004,1.5,2.8)
HORIZONS=(.1,.5,1.,2.,3.)
N_BOOT=250
EXPECTED_P5D_SPLIT_SHA256='d60bfe0daa8195290958ca0b8f6268e01bf93811267e6c80b02cfadaa84d37a2'
NEAR_CORR=.995
NEAR_NRMSE=.075


def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()


def load_dep(root):
    import importlib.util
    path=root/'data'/'f005_free_run_family_v0.4.1.py'
    if not path.is_file():raise FileNotFoundError(f'Prior v0.4.1 required: {path}')
    spec=importlib.util.spec_from_file_location('f005_v041_locked',path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    if mod.VERSION!='0.4.1':raise ValueError('Locked v0.4.1 required')
    return mod

class Union:
    def __init__(self,n):self.p=list(range(n));self.sz=[1]*n
    def find(self,x):
        while self.p[x]!=x:self.p[x]=self.p[self.p[x]];x=self.p[x]
        return x
    def join(self,a,b):
        a=self.find(a);b=self.find(b)
        if a!=b:
            if self.sz[a]<self.sz[b]:a,b=b,a
            self.p[b]=a;self.sz[a]+=self.sz[b]


def graph_from_v042(root, labels, a, *, input_path=None):
    """Load the complete accepted edge list, and form a graph on DEVELOPMENT only.

    Paths through TEST/OOD inputs are deliberately NOT used to group development;
    this is an independently-defined split for the available development population.
    """
    parent=root/'outputs'/'f005_qualification_v0.4.2'
    path=parent/'family_candidate_matches_REVIEW.csv'
    rp=parent/'v042_report.json'
    if not path.is_file() or not rp.is_file():
        raise FileNotFoundError('First install and run v0.4.2; missing v042 JSON or match CSV')
    prior=json.loads(rp.read_text(encoding='utf-8'))
    summary=prior.get('P5c',{})
    if prior.get('tool')!='F005_Qualification_v0.4.2' or summary.get('candidate_pairs_unscored')!=0:
        raise ValueError('v0.4.2 input candidate audit not complete')
    if summary.get('independence_certification')!='BLOCKED_NO_SOURCE_FAMILY_IDENTIFIERS':
        raise ValueError('Unexpected v042 provenance gate')
    if prior.get('P6g',{}).get('test_ood_response_sealed') is not True:
        raise ValueError('v042 source response seal not preserved')
    # Independently verify the exact source INPUT array has not changed since v042.
    input_sha=prior.get('source_locks',{}).get('input_npy_sha256')
    if input_path is None or not input_sha or input_sha != sha(Path(input_path)):
        raise ValueError('Source INPUT NPY differs from the v042 locked SHA256')
    dev={i for i,p in labels.items() if p in ('STANDARD_TRAIN','STANDARD_VALIDATION')}
    n=len(labels);uf=Union(n)
    matched=0;dev_edges=0; cross_source=0;verified=0
    seen=set()
    with path.open(encoding='utf-8-sig',newline='') as f:
        for row in csv.DictReader(f):
            i,j=int(row['row_a']),int(row['row_b'])
            if i==j or i<0 or j>=n or i>=n or j<0 or i>=j:
                raise ValueError('Invalid edge in v0.4.2 matches file')
            if (i,j) in seen:raise ValueError('Duplicate input edge record')
            seen.add((i,j));matched+=1
            if labels[i]!=row['partition_a'] or labels[j]!=row['partition_b']:
                raise ValueError('Input edge label mismatch')
            corr=float(row['correlation']);dist=float(row['norm_rmse'])
            if corr<NEAR_CORR-1e-7 or dist>NEAR_NRMSE+1e-7:
                raise ValueError('Edge violates v042 proximity contract')
            # Independently recompute first 32 + hash-selected 32 input matches.
            if verified<32 or int(hashlib.sha256(f'{i}/{j}'.encode()).hexdigest()[:4],16)%1000<1:
                x=np.asarray(a[i],float);y=np.asarray(a[j],float)
                sx=max(float(np.max(abs(x))),1e-12);sy=max(float(np.max(abs(y))),1e-12)
                if sx<=1e-12 or sy<=1e-12: pass
                else:
                    if not (np.isfinite(x).all() and np.isfinite(y).all()):raise ValueError('Nonfinite edge input')
                    # Same ±4/±2/0 scoring rule as prior stage.
                    best=(-2.,float('inf'))
                    for s in (-4,-2,0,2,4):
                        xx=x[max(0,s):len(x)+min(s,0)]/sx
                        yy=y[max(0,-s):len(y)+min(-s,0)]/sy
                        if len(xx)<8:continue
                        xxm=xx-xx.mean();yym=yy-yy.mean()
                        denom=np.linalg.norm(xxm)*np.linalg.norm(yym)
                        rc=float(np.dot(xxm,yym)/denom) if denom>1e-12 else 0.
                        dr=float(np.sqrt(np.mean((xx-yy)**2)))
                        if rc>best[0] or (abs(rc-best[0])<1e-12 and dr<best[1]):best=(rc,dr)
                    if abs(best[0]-corr)>2e-5 or abs(best[1]-dist)>2e-5:
                        raise ValueError('Previously reported input edge does not reproduce')
                verified+=1
            if i in dev and j in dev:
                dev_edges+=1
                uf.join(i,j)
            if labels[i]!=labels[j]:cross_source+=1
    if matched!=summary.get('near_shape_total_pairs'):
        raise ValueError('v042 matched-edge file count does not match locked report')
    groups=defaultdict(list)
    for i in sorted(dev):groups[uf.find(i)].append(i)
    groups=[sorted(v) for v in groups.values()]
    groups.sort(key=lambda v:(-len(v),v[0]))
    return groups,dict(matched_edges=matched,development_edges=dev_edges,
        matched_cross_original_partitions=cross_source,edge_rechecks=verified,
        v042_report_sha256=sha(rp),v042_matches_sha256=sha(path),
        components=len(groups),largest_component=len(groups[0]) if groups else 0,
        group_definition='connected components of v042 input-only candidate edges restricted to prior TRAIN+VALIDATION',
        source_family_identity='UNKNOWN_NOT_PUBLISHER_CERTIFIED')


def split_proxy_groups(groups,*,seed=SEED,validation_fraction=.20):
    """Stable grouping on inputs only; row outcome values are never used here."""
    if not groups:raise ValueError('No development groups')
    n=sum(map(len,groups));target=int(round(validation_fraction*n))
    rng=np.random.default_rng(seed)
    perm=rng.permutation(len(groups))
    val_groups=[];train_groups=[];num_val=0
    # greedy stable randomized knapsack; preserve graph-components as indivisible units
    for ix in perm:
        v=groups[int(ix)]
        if num_val<target and num_val+len(v)<=int(n*.35):
            val_groups.append(v);num_val+=len(v)
        else:train_groups.append(v)
    train=sorted(i for g in train_groups for i in g)
    valid=sorted(i for g in val_groups for i in g)
    if set(train)&set(valid) or len(train)+len(valid)!=n or len(valid)<max(1,int(.10*n)):
        raise RuntimeError('Failed proxy-disjoint split')
    group_rows=[]
    for kind,bundles in [('DEV_TRAIN',train_groups),('DEV_VALIDATION',val_groups)]:
        for g in bundles:
            gid=hashlib.sha256(np.asarray(g,dtype='<i4').tobytes()).hexdigest()[:20]
            for i in g:group_rows.append(dict(row_id_zero_based=i,proxy_component_id=gid,
                                               proxy_component_size=len(g),partition=kind))
    group_rows.sort(key=lambda z:z['row_id_zero_based'])
    return train,valid,group_rows


def fit_arx_train(a,y_mm,ids,dt,*,batch=64):
    """New ARX(2) fit with only new DEVELOPMENT-TRAIN rows; stable norm scaling.

    Second-difference features: eta, (eta-eta_previous), a*dt². Target d² eta.
    No use of prior ARX parameters to fit this model.
    """
    xx=np.zeros((3,3));xy=np.zeros(3);sumx=np.zeros(3);nt=0
    # fixed preconditioning units, physical quantity metres
    scales=np.array([.003,.00015,.00002],dtype=float)
    for b in range(0,len(ids),batch):
        ix=ids[b:b+batch]; yy=np.asarray(y_mm[ix],float)*.001
        aa=np.asarray(a[ix],float)
        if not(np.isfinite(yy).all() and np.isfinite(aa).all()):raise ValueError('Nonfinite training rows')
        yc=yy[:,1:-1];yp=yy[:,:-2];yn=yy[:,2:]
        Z=np.stack([yc,yc-yp,aa[:,1:-1]*dt*dt],axis=-1).reshape(-1,3)/scales
        t=(yn-2*yc+yp).ravel()
        xx+=Z.T@Z;xy+=Z.T@t;sumx+=Z.sum(axis=0);nt+=len(t)
    ridge=1e-7*np.trace(xx)/3
    theta=np.linalg.solve(xx+ridge*np.eye(3),xy)/scales
    A=2+theta[0]+theta[1]; B=-1-theta[1];C=theta[2]
    roots=np.roots([1.,-A,-B]); stable=bool(np.all(np.abs(roots)<1))
    return (float(A),float(B),float(C)),dict(samples=nt,fit='train-only second-difference least squares ridge',
        ridge_preconditioned=ridge,roots=[dict(real=float(t.real),imag=float(t.imag),abs=float(abs(t))) for t in roots],
        stable=stable)


def fit_oscillator_train(a,y_mm,ids,dt,*,batch=64):
    """Separate physical-coordinate ringdown fit on train-only low-forcing samples.

    Calibrate omega0 and gamma from unforced portions; calibrate drive K separately.
    This is a separately identified *reduced-order* oscillator, NOT Euler PDE closure.
    """
    sxx=np.zeros((2,2));sxy=np.zeros(2);num=0
    for b in range(0,len(ids),batch):
        ix=ids[b:b+batch];yy=np.asarray(y_mm[ix],float)*.001
        aa=np.asarray(a[ix],float)
        yc=yy[:,1:-1]; yp=yy[:,:-2];yn=yy[:,2:]
        vel=(yn-yp)/(2*dt);accel=(yn-2*yc+yp)/(dt*dt)
        amax=np.max(np.abs(aa),axis=1)
        # Quiet interval based only on the applied acceleration profile
        quiet=(np.abs(aa[:,:-2])<.015*amax[:,None]) & (np.abs(aa[:,1:-1])<.015*amax[:,None]) & (np.abs(aa[:,2:])<.015*amax[:,None])
        quiet &= (np.abs(yc)>.00015) & (np.abs(aa[:,1:-1])<.025)
        Z=np.stack([vel,yc],axis=-1)[quiet];t=accel[quiet]
        if len(t):sxx+=Z.T@Z;sxy+=Z.T@t;num+=len(t)
    if num<1500:return None,dict(status='BLOCKED_INSUFFICIENT_FREE_RINGDOWN',free_samples=num)
    # Scale features, solve for -2 gamma (s^-1) and -omega0^2 (s^-2).
    reg=1e-11*np.trace(sxx)/2
    co=np.linalg.solve(sxx+reg*np.eye(2),sxy)
    gamma=float(-co[0]/2);w02=float(-co[1])
    if not(np.isfinite(gamma) and np.isfinite(w02) and gamma>0 and w02>gamma*gamma):
        return None,dict(status='BLOCKED_NONPHYSICAL_RINGDOWN_FIT',free_samples=num,gamma_candidate=gamma,w02_candidate=w02)
    # Independently fit dimensionless drive coefficient using all TRAIN data.
    nume=0.;den=0.;nt=0
    for b in range(0,len(ids),batch):
        ix=ids[b:b+batch];yy=np.asarray(y_mm[ix],float)*.001;aa=np.asarray(a[ix],float)
        yc=yy[:,1:-1];yp=yy[:,:-2];yn=yy[:,2:]
        vel=(yn-yp)/(2*dt);accel=(yn-2*yc+yp)/(dt*dt)
        rest=accel+2*gamma*vel+w02*yc
        f=aa[:,1:-1]
        nume+=float((rest*f).sum());den+=float((f*f).sum());nt+=f.size
    if den<1e-9:return None,dict(status='BLOCKED_NO_EXCITATION',free_samples=num)
    K=float(nume/den)
    w0=math.sqrt(w02);wd=math.sqrt(w02-gamma*gamma)
    return (gamma,w0,K),dict(status='FITTED_TRAIN_ONLY_REDUCED_ORDER',ringdown_samples=num,
        drive_fit_samples=nt,gamma_s_inv=gamma,natural_frequency_hz=w0/(2*math.pi),
        damped_frequency_hz=wd/(2*math.pi),K_dimensionless=K,
        fit='ringdown d2eta/dt2 vs velocity and eta on quiet TRAIN spans; K from TRAIN forcing residual',
        not_euler=True,not_pklsa=True)


def oscillator_recurrence(params,dt):
    gamma,w0,K=params
    denom=1+gamma*dt
    A=(2-w0*w0*dt*dt)/denom
    B=-(1-gamma*dt)/denom
    C=K/denom
    poles=np.roots([1.,-A,-B])
    if np.max(abs(poles))>=1:raise ValueError('Independently fitted oscillator unstable in discretization')
    return A,B,C


def recursive_predictions(a,y_mm,ids,dt,coeff,anchors=ANCHORS,max_h=3.):
    x=np.asarray(a[ids],float); y=np.asarray(y_mm[ids],float)*.001
    if x.shape!=y.shape or not np.isfinite(x).all() or not np.isfinite(y).all():raise ValueError('Invalid DEV_VALIDATION samples')
    results={}
    horizon=int(round(max_h/dt))
    for anchor in anchors:
        n0=max(1,int(round(anchor/dt)))
        if n0+horizon>=x.shape[1]:raise ValueError('Forecast exceeds source time window')
        prev=y[:,n0-1].copy();cur=y[:,n0].copy();pred=np.empty((len(ids),horizon))
        for step in range(horizon):
            nxt=coeff[0]*cur+coeff[1]*prev+coeff[2]*dt*dt*x[:,n0+step]
            pred[:,step]=nxt
            prev,cur=cur,nxt
        actual=y[:,n0+1:n0+horizon+1]
        results[n0]=(pred,actual,y[:,n0],y[:,n0]-y[:,n0-1])
    return results


def group_bootstrap_difference(errorA,errorB,group_ids,seed=SEED,nboot=N_BOOT):
    """Positive delta means model A better than B. Resample whole detected groups."""
    group_ids=np.asarray(group_ids)
    g=np.unique(group_ids)
    sq_a=np.asarray(errorA)**2; sq_b=np.asarray(errorB)**2
    sum_a=np.array([sq_a[group_ids==u].sum() for u in g]);sum_b=np.array([sq_b[group_ids==u].sum() for u in g]);counts=np.array([np.sum(group_ids==u) for u in g])
    rng=np.random.default_rng(seed)
    vals=[]
    for _ in range(nboot):
        ix=rng.integers(0,len(g),size=len(g));cnt=counts[ix].sum()
        vals.append(1000*(np.sqrt(sum_b[ix].sum()/cnt)-np.sqrt(sum_a[ix].sum()/cnt)))
    return [float(z) for z in np.quantile(vals,[.025,.975])]


def evaluate(a,y,ids,groups_meta,dt,arx,osc=None,*,nboot=N_BOOT):
    """Only selected proxy validation y is accessed; all models are truly recursive."""
    byid={r['row_id_zero_based']:r['proxy_component_id'] for r in groups_meta}
    group_ids=np.array([byid[i] for i in ids])
    ar=recursive_predictions(a,y,ids,dt,arx)
    os=recursive_predictions(a,y,ids,dt,osc) if osc else None
    rows=[]; trace=[]
    for anchor_n,(pred,actual,init,velocity_increment) in ar.items():
        length=pred.shape[1];kstep=np.arange(1,length+1)
        base={
            'ARX_RETRAINED':pred,
            'PERSISTENCE':np.broadcast_to(init[:,None],pred.shape),
            'LINEAR_EXTRAPOLATION':init[:,None]+kstep[None,:]*velocity_increment[:,None],
            'ZERO_RESPONSE':np.zeros_like(pred)
        }
        if os is not None:base['OSCILLATOR_INDEPENDENT_TRAIN_FIT']=os[anchor_n][0]
        for H in HORIZONS:
            k=int(round(H/dt));score=dict(anchor_s=anchor_n*dt,horizon_s=k*dt,
                rows=len(ids),proxy_components=len(np.unique(group_ids)),steps=k)
            err={m:np.square(arr[:,:k]-actual[:,:k]) for m,arr in base.items()}
            for name,e in err.items():
                score[f'{name}_PATH_RMSE_MM']=float(1000*np.sqrt(e.mean()))
                score[f'{name}_ENDPOINT_RMSE_MM']=float(1000*np.sqrt(e[:,-1].mean()))
            control=[x for x in base if x!='ARX_RETRAINED']
            for kind in ('PATH','ENDPOINT'):
                best=min(control,key=lambda c:score[f'{c}_{kind}_RMSE_MM'])
                score[f'{kind}_BEST_BASELINE']=best
                score[f'{kind}_BEST_BASELINE_MM']=score[f'{best}_{kind}_RMSE_MM']
                score[f'{kind}_ARX_ADVANTAGE_PERCENT']=100*(1-score[f'ARX_RETRAINED_{kind}_RMSE_MM']/max(1e-12,score[f'{kind}_BEST_BASELINE_MM']))
                arxerr=err['ARX_RETRAINED'].mean(axis=1) if kind=='PATH' else err['ARX_RETRAINED'][:,-1]
                for c in control:
                    berr=err[c].mean(axis=1) if kind=='PATH' else err[c][:,-1]
                    score[f'{kind}_{c}_MINUS_ARX_CI95_MM']=group_bootstrap_difference(arxerr**.5,berr**.5,group_ids,seed=SEED+anchor_n+k+len(c),nboot=nboot)
            rows.append(score)
        # fixed-input evidence sample without cherry-picked path
        for ix in range(min(len(ids),2)):
            for k in range(0,length+1,25):
                rec=dict(row_id=ids[ix],anchor_s=anchor_n*dt,time_s=(anchor_n+k)*dt,
                         measured_mm=1000*(init[ix] if k==0 else actual[ix,k-1]),
                         arx_mm=1000*(init[ix] if k==0 else pred[ix,k-1]))
                if os:rec['independent_oscillator_mm']=1000*(init[ix] if k==0 else os[anchor_n][0][ix,k-1])
                trace.append(rec)
    return rows,trace


def write_csv(p,rows,columns=None):
    if not rows and not columns:raise ValueError('Missing columns')
    cols=columns if columns else list(rows[0]);
    with p.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
        for r in rows:
            w.writerow({k:json.dumps(v) if isinstance(v,(list,dict)) else v for k,v in r.items()})


def make_pdf(path,report,rows,trace):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    with PdfPages(path) as pdf:
        f,ax=plt.subplots(figsize=(8.27,11.69));ax.axis('off')
        t=report['P5d'];q=report['P6h'];o=report['P6i']
        s=(f"F005 v0.4.3 | FAMILY-DISJOINT DEVELOPMENT\n"
           f"NOT BLIND | NOT EULER | NOT PKLSA\n\n"
           f"DATA / PROVENANCE\nDevelopment rows: {t['development_rows']}\n"
           f"Proxy components: {t['proxy_components']}\n"
           f"New TRAIN rows: {t['train_count']}\n"
           f"New VALIDATION rows: {t['validation_count']}\n"
           f"Cross-group candidate edges: {t['cross_split_near_edges']}\n"
           f"Publisher-defined true family IDs: UNAVAILABLE\n"
           f"Original TEST/OOD responses: SEALED\n\n"
           f"NEW TRAIN-ONLY FITS\n"
           f"ARX: {q['arx_fit']['status']}\n"
           f"Ringdown oscillator: {o['fit']['status']}\n"
           f"Oscillator is independently trained, not Euler closure.\n\n"
           f"METRIC DESIGN\n15 fixed anchor/horizon conditions\n"
           f"Path RMSE and endpoint RMSE; units: mm\n"
           f"Group bootstrap resamples proxy components\n"
           f"Future acceleration known in both driven models\n"
           f"No observed heights within forecast horizon\n\n"
           f"GATE STATES\nP5d proxy-disjoint: {t['status']}\n"
           f"P6h refit+forecasts: {q['status']}\n"
           f"P6i independent oscillator: {o['status']}\n"
           f"P7 Euler/PKLSA: NOT RUN\nP8 physical SST: UNRESOLVED\n")
        ax.text(.035,.97,s,fontfamily='monospace',fontsize=10,va='top',transform=ax.transAxes,linespacing=1.5)
        pdf.savefig(f);plt.close(f)
        if rows:
            anchor=1.5; sub=sorted((r for r in rows if abs(r['anchor_s']-anchor)<.001),key=lambda z:z['horizon_s'])
            for kind in ['PATH','ENDPOINT']:
                f,ax=plt.subplots(figsize=(8.27,5.8))
                for name in ['ARX_RETRAINED','OSCILLATOR_INDEPENDENT_TRAIN_FIT','PERSISTENCE','ZERO_RESPONSE']:
                    key=f'{name}_{kind}_RMSE_MM'
                    if key in sub[0]:ax.plot([r['horizon_s'] for r in sub],[r[key] for r in sub],'-o',label=name.replace('_',' ').title())
                ax.set(title=f'{kind} RMSE - anchor=1.5 s (proxy group development)',xlabel='Horizon [s]',ylabel='RMSE [mm]')
                ax.grid(alpha=.25);ax.legend(fontsize=8);f.tight_layout();pdf.savefig(f);plt.close(f)
        f,ax=plt.subplots(figsize=(8.27,11.69));ax.axis('off')
        txt=("BOUNDARIES AND FAILURE CRITERIA\n\n"
             "1. Input components come from v0.4.2 accepted-candidate graph.\n"
             "   Candidate generator is not exhaustive; unknown source families.\n"
             "   Zero graph leakage is NOT real-family independence.\n\n"
             "2. TRAIN and VALIDATION are rebuilt from the formerly observed\n"
             "   development pool. No new untouched holdout is created.\n"
             "   Previously seen validation data => no blind certification.\n\n"
             "3. ARX re-fit uses only new TRAIN measured heights.\n"
             "   Oscillator ringdown fit is separate; inferred from TRAIN.\n"
             "   Neither implements incompressible Euler fluid dynamics.\n\n"
             "4. Both driven models receive known future acceleration.\n"
             "   Initial two measured elevations define the origin.\n"
             "   Recursion receives no measured future heights.\n\n"
             "5. Cluster bootstrap uses detected PROXY input groups, not\n"
             "   certified publisher family IDs. Confidence is provisional.\n\n"
             "6. TEST/OOD response access is forbidden and regression-tested.\n"
             "   No 49.9 GB ZIP processing. v0.4.2 outputs preserved.\n\n"
             "References:\nGiulietti et al., robot sloshing Zenodo (2026),\n"
             "doi:10.5281/zenodo.20039757\n"
             "Ljung, System Identification, 2nd ed. (1999).\n")
        ax.text(.03,.97,txt,fontfamily='monospace',fontsize=9.3,va='top',linespacing=1.52,transform=ax.transAxes)
        pdf.savefig(f);plt.close(f)


def run(root,*,cfg_override=None,graph_override=None,nboot=N_BOOT):
    root=Path(root).resolve();start=time.monotonic()
    if cfg_override is None:
        prior=load_dep(root);cfg=prior.source_lock(root)
    else:cfg=cfg_override
    labels=cfg['labels'];a=cfg['a'];y=cfg['y'];dt=cfg['dt']
    # Use prior candidate graph, locked SHA, and never read prior TEST/OOD responses
    if graph_override is None:groups,graph_info=graph_from_v042(root,labels,a,input_path=cfg['input_path'])
    else:groups,graph_info=graph_override
    dev={i for i,p in labels.items() if p in ('STANDARD_TRAIN','STANDARD_VALIDATION')}
    if set(i for g in groups for i in g)!=dev:raise ValueError('Proxy groups do not cover development exactly')
    train,val,group_rows=split_proxy_groups(groups)
    gids={r['row_id_zero_based']:r['proxy_component_id'] for r in group_rows}
    overlap=len({gids[i] for i in train}&{gids[i] for i in val})
    if overlap:raise ValueError('Proxy groups leaked across split')
    # The exact INPUT-only preview is preregistered from the uploaded v0.4.2 outputs.
    # Reject a surprising remapping before any DEVELOPMENT-response model refit.
    if len(dev)==4250 and graph_info.get('matched_edges')==36081:
        import io
        stream=io.StringIO(newline='')
        w=csv.DictWriter(stream,fieldnames=list(group_rows[0]));w.writeheader();w.writerows(group_rows)
        observed=hashlib.sha256(stream.getvalue().encode('utf-8')).hexdigest()
        if observed!=EXPECTED_P5D_SPLIT_SHA256:
            raise ValueError('Prerecorded v0.4.3 input-only DEVELOPMENT split changed: '+observed)
    # Preserve input-only graph status as review; no source family certification.
    arx,fit=fit_arx_train(a,y,train,dt)
    oscillator,oscinfo=fit_oscillator_train(a,y,train,dt)
    osc_coef=None
    if fit['stable'] is False:
        rows=[];traces=[];status='BLOCKED_REFIT_UNSTABLE'
    else:
        if oscillator is not None:
            try:osc_coef=oscillator_recurrence(oscillator,dt)
            except ValueError:
                oscinfo['status']='BLOCKED_OSCILLATOR_DISCRETIZATION_UNSTABLE'
        rows,traces=evaluate(a,y,val,group_rows,dt,arx,osc_coef,nboot=nboot)
        status='DEVELOPMENT_EVALUATED_PROXY_DISJOINT'
    out=root/'outputs'/'f005_family_disjoint_v0.4.3'
    out.mkdir(parents=True,exist_ok=True)
    report=dict(tool='F005_Family_Disjoint_v0.4.3',utc=datetime.now(timezone.utc).isoformat(),
        scientific_status='DEVELOPMENT_REUSED_POOL_NOT_BLIND_NOT_EULER_NOT_PKLSA',
        provenance=dict(v03_model_unchanged=True,v042_outputs_unchanged=True,source_zip_50gb_read=False,
          test_ood_response_access=False,source_hashes=cfg.get('source_hashes'),
          input_npy_sha256=sha(cfg['input_path']) if cfg_override is None else 'SYNTHETIC_TEST',
          v042_graph=graph_info),
        P5d=dict(status='DEVELOPMENT_PROXY_GRAPH_DISJOINT_NOT_TRUE_FAMILY_CERTIFIED',
           development_rows=len(dev),proxy_components=len(groups),train_count=len(train),validation_count=len(val),
           target_validation_fraction=.20,cross_split_near_edges=overlap,
           original_test_ood_membership_unchanged=True,publisher_family_ids='ABSENT',
           partition_semantics='old TRAIN+VALIDATION both reused for DEVELOPMENT; original TEST/OOD response sealed'),
        P6h=dict(status=status,arx_fit=dict(status='FITTED_TRAIN_ONLY' if fit['stable'] else 'BLOCKED',coefficients=arx,**fit),
           known_future_acceleration=True,response_teacher_forcing_in_horizon=False,
           anchors_s=ANCHORS,horizons_s=HORIZONS,
           metrics=rows,qualifying_path_conditions=sum(r.get('PATH_ARX_ADVANTAGE_PERCENT',-math.inf)>0 for r in rows),
           qualifying_endpoint_conditions=sum(r.get('ENDPOINT_ARX_ADVANTAGE_PERCENT',-math.inf)>0 for r in rows)),
        P6i=dict(status='REDUCED_ORDER_OSCILLATOR_TRAIN_ONLY' if osc_coef is not None else 'OSCILLATOR_NOT_QUALIFIED',
           fit=oscinfo,parameters=list(oscillator) if oscillator is not None else None),
        P7='NOT_RUN',P8='UNRESOLVED',seconds=round(time.monotonic()-start,2))
    (out/'v043_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    write_csv(out/'proxy_family_development_split.csv',group_rows)
    write_csv(out/'validation_full_path_metrics.csv',rows,columns=['anchor_s','horizon_s','rows','proxy_components','steps'] if not rows else None)
    write_csv(out/'fixed_development_trace_sample.csv',traces,columns=['row_id','anchor_s','time_s','measured_mm','arx_mm'] if not traces else None)
    lines=["# F005 v0.4.3 - Family-disjoint DEVELOPMENT audit",'',
           '**NOT BLIND; NOT EULER; NOT PKLSA; physical status UNRESOLVED.**','',
           f"- Proxy input groups: {len(groups)}; development TRAIN: {len(train)}; development VALIDATION: {len(val)}.",
           f"- Detected proxy groups crossing new split: {overlap}.",
           '- Previous VALIDATION responses were already inspected; rebuilt group split is development-only.',
           '- TEST/OOD response arrays not indexed; original v0.4.2 results unchanged.',
           f"- New ARX fit: {fit['stable']} stable; independent oscillator: {oscinfo['status']}.",
           f"- ARX path improvement versus best tested baseline: {report['P6h']['qualifying_path_conditions']}/{len(rows)} conditions.",
           f"- ARX endpoint improvement versus best tested baseline: {report['P6h']['qualifying_endpoint_conditions']}/{len(rows)} conditions.",
           '- Cluster bootstrap resamples candidate graph components, not verified publisher-defined families.',
           '- Euler and source-native PKLSA have not been tested.','']
    (out/'V043_SUMMARY.md').write_text('\n'.join(lines),encoding='utf-8')
    make_pdf(out/'F005_v0.4.3_DEVELOPMENT_REPORT.pdf',report,rows,traces)
    return report,out


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=Path('.'))
    a=parser.parse_args()
    r,out=run(a.root)
    print(json.dumps(dict(status=r['scientific_status'],P5d=r['P5d']['status'],P6h=r['P6h']['status'],
        P6i=r['P6i']['status'],out=str(out)),indent=2))

if __name__=='__main__':main()
