"""A054 target-free KnotPlot geometry/projection numerical screening.

This is a diagnostic sibling of A054 v0.5.1, NOT an admitted state selection.
Its reach estimator and projected objective reproduce the frozen v0.5.1
mathematical definitions, evaluated with vectorized NumPy rather than a
new physical energy law. Uses no topology-dependent numerical tuning.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, os, pathlib, sys, time
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT/'inputs'/'census'
DEFAULT_RESULTS = ROOT/'results'
EPS = .015
LIMIT_HESS = .25
STATIONARITY_LIMIT = .1
CORE = 1.0
REACH_TANGENT_TOL = .18


def sha256_bytes(b): return hashlib.sha256(b).hexdigest()

def parse_native(b):
    comps, cur = [], []
    for n,line in enumerate(b.decode('utf-8-sig').splitlines(), 1):
        raw=line.strip()
        if not raw:
            if cur: comps.append(np.asarray(cur,dtype=np.float64));cur=[]
            continue
        vals=raw.split()
        if len(vals)!=3: raise ValueError(f'line {n}: expected 3 coordinates')
        row=[float(x) for x in vals]
        if not all(math.isfinite(x) for x in row): raise ValueError(f'line {n}: nonfinite coordinate')
        cur.append(row)
    if cur: comps.append(np.asarray(cur,dtype=np.float64))
    if not comps or any(len(c)<4 for c in comps): raise ValueError('component missing or fewer than four beads')
    return comps

def clean(c):
    c=np.asarray(c,dtype=np.float64)
    if len(c)>4 and np.linalg.norm(c[0]-c[-1]) < 1e-12*max(1.0,np.ptp(c,axis=0).max()):c=c[:-1]
    return c

def length(c):return float(np.linalg.norm(np.roll(c,-1,axis=0)-c,axis=1).sum())

def arc_resample(c,n):
    p=clean(c);q=np.vstack((p,p[0]));seg=np.linalg.norm(np.diff(q,axis=0),axis=1)
    s=np.r_[0.,np.cumsum(seg)]
    if s[-1] <= 0:raise ValueError('zero total length')
    t=np.linspace(0.,s[-1],int(n)+1)[:-1]
    return np.column_stack([np.interp(t,s,q[:,i]) for i in range(3)])

def allocate(cs,total,min_per=24):
    L=np.array([length(c) for c in cs]);n=[max(min_per,int(round(total*float(v)/float(L.sum())))) for v in L]
    return [arc_resample(c,ni) for c,ni in zip(cs,n)]

def edge_metrics(cs):
    delta=np.concatenate([np.linalg.norm(np.roll(c,-1,axis=0)-c,axis=1) for c in cs]);mu=float(delta.mean())
    return {'count':int(len(delta)), 'component_counts':[len(c) for c in cs],
        'edge_mean':mu,'edge_cv':float(delta.std()/max(mu,1e-30)),
        'edge_spread_relative':float((delta.max()-delta.min())/max(mu,1e-30)),
        'edge_min':float(delta.min()),'edge_max':float(delta.max())}

def approximate_reach(cs):
    # v0.5.1: curvature-limited reach OR a doubly-critical-chord proxy.
    local=np.inf;dcrit=np.inf
    tans=[]
    for c in cs:
        c=clean(c);N=len(c);seg=np.roll(c,-1,axis=0)-c;ds=float(np.linalg.norm(seg,axis=1).sum())/N
        d1=(np.roll(c,-1,axis=0)-np.roll(c,1,axis=0))/(2*ds)
        d2=(np.roll(c,-1,axis=0)-2*c+np.roll(c,1,axis=0))/(ds*ds)
        cross=np.cross(d1,d2)
        curvature=np.linalg.norm(cross,axis=1)/np.maximum(np.linalg.norm(d1,axis=1)**3,1e-15)
        km=float(curvature.max())
        if km>0:local=min(local,1/km)
        tan=d1/np.maximum(np.linalg.norm(d1,axis=1)[:,None],1e-15)
        tans.append(tan)
        # Upper triangle, remove arclength-close indices; only doubly-normal chords.
        I,J=np.triu_indices(N,k=1)
        sep=np.minimum(J-I,N-(J-I));keep=sep>max(3,N//20)
        I,J=I[keep],J[keep]
        if len(I):
            R=c[J]-c[I];distance=np.linalg.norm(R,axis=1)
            good=distance>1e-15
            U=R[good]/distance[good,None];I=I[good];J=J[good];distance=distance[good]
            normal=(np.abs(np.sum(U*tan[I],axis=1))<=REACH_TANGENT_TOL)&(np.abs(np.sum(U*tan[J],axis=1))<=REACH_TANGENT_TOL)
            if normal.any(): dcrit=min(dcrit,float(np.min(distance[normal])))
    for i,a in enumerate(cs):
        for b in cs[i+1:]:
            for st in range(0,len(a),128):
                diff=a[st:st+128,None,:]-b[None,:,:]
                dcrit=min(dcrit,float(np.linalg.norm(diff,axis=2).min()))
    nonlocalr=.5*dcrit if math.isfinite(dcrit) else np.inf
    r=min(local,nonlocalr)
    branch='curvature' if local<=nonlocalr else 'nonlocal'
    if not math.isfinite(r) or r<=1e-12:
        r=max(sum(length(c) for c in cs)/(2*np.pi*max(len(cs),1)),1e-6);branch='fallback'
    return float(r),{'branch':branch,'curvature_radius':float(local) if math.isfinite(local) else None,'half_critical_distance':float(nonlocalr) if math.isfinite(nonlocalr) else None}

def recondition(cs,counts):
    cs=[arc_resample(c,n) for c,n in zip(cs,counts)]
    center=np.concatenate(cs,axis=0).mean(axis=0)
    cs=[c-center for c in cs]
    reach,info=approximate_reach(cs)
    return [c/reach for c in cs],reach,info

def kernel(cs):
    # Numerically identical summation target to A054.energy_matrix(core=1), but vectorized.
    c=np.concatenate(cs,axis=0)
    d=np.concatenate([np.roll(x,-1,axis=0)-x for x in cs],axis=0)
    m=np.concatenate([.5*(x+np.roll(x,-1,axis=0)) for x in cs],axis=0)
    # block-oriented to avoid large temporary arrays (n<=600 in standard screen).
    result=0.0
    for i in range(0,len(m),96):
        ds=d[i:i+96]
        delta=m[i:i+96,None,:]-m[None,:,:]
        denom=np.sqrt(np.sum(delta*delta,axis=2)+CORE**2)
        result+=float(np.sum((ds @ d.T)/denom))
    return result

def components_rms(a,b):
    if len(a)!=len(b) or any(len(x)!=len(y) for x,y in zip(a,b)):return None
    x=np.concatenate(a);y=np.concatenate(b)
    return float(np.sqrt(np.mean(np.sum((x-y)**2,axis=1)))/max(np.sqrt(np.mean(np.sum(x*x,axis=1))),1e-30))

def bishop(c):
    t=np.roll(c,-1,axis=0)-np.roll(c,1,axis=0)
    t/=np.maximum(np.linalg.norm(t,axis=1)[:,None],1e-15)
    axes=np.eye(3);ax=axes[np.argmin(np.abs(axes@t[0]))]
    n0=ax-np.dot(ax,t[0])*t[0];n0/=np.linalg.norm(n0)
    n=np.zeros_like(c);n[0]=n0
    for i in range(len(c)-1):
        u=t[i];v=t[i+1];axis=np.cross(u,v);s=np.linalg.norm(axis);d=np.clip(np.dot(u,v),-1,1)
        if s<1e-14: nn=n[i].copy()
        else:
            k=axis/s;ang=np.arctan2(s,d)
            nn=n[i]*np.cos(ang)+np.cross(k,n[i])*np.sin(ang)+k*np.dot(k,n[i])*(1-np.cos(ang))
        nn-=np.dot(nn,v)*v;nn/=max(np.linalg.norm(nn),1e-15);n[i+1]=nn
    b=np.cross(t,n);b/=np.maximum(np.linalg.norm(b,axis=1)[:,None],1e-15)
    return n,b

def mode_basis(cs,modes=2):
    offsets=np.cumsum([0]+[len(c) for c in cs]);T=int(offsets[-1]);basis=[]
    for ci,c in enumerate(cs):
        n,b=bishop(c);theta=2*np.pi*np.arange(len(c))/len(c)
        for k in range(1,modes+1):
            for frame,phase in ((n,np.cos(k*theta)),(b,np.sin(k*theta))):
                arr=np.zeros((T,3),dtype=float)
                arr[offsets[ci]:offsets[ci+1]]=frame*phase[:,None]
                mag=np.sqrt(np.mean(np.sum(arr*arr,axis=1)))
                arr/=max(mag,1e-15);basis.append(arr)
    return np.asarray(basis),offsets

def objective_factory(start, modes=2):
    base,_,_=recondition(start,[len(c) for c in start])
    flat=np.concatenate(base);basis,offs=mode_basis(base,modes)
    counts=[len(c) for c in base];evaluations=[0]
    def project(q):
        x=flat+np.tensordot(np.asarray(q,dtype=float),basis,axes=(0,0))
        cs=[x[offs[i]:offs[i+1]] for i in range(len(counts))]
        return recondition(cs,counts)
    def energy(q):
        p,_,_=project(q)
        evaluations[0]+=1
        return kernel(p)
    return energy,len(basis),evaluations

def gradient_sweep(U,d,eps=EPS):
    z=np.zeros(d);u0=float(U(z));sc=[]
    for h in (eps,eps/2,eps/4):
        g=[]
        for i in range(d):
            e=np.zeros(d);e[i]=h
            g.append((U(e)-U(-e))/(2*h))
        g=np.asarray(g);sc.append(g)
    dif=float(np.linalg.norm(sc[-1]-sc[-2])/max(np.linalg.norm(sc[-1]),1e-30))
    direction=-sc[-1]/max(np.linalg.norm(sc[-1]),1e-30)
    directional=[]
    for h in (eps,eps/2,eps/4):
        fd=(U(h*direction)-U(-h*direction))/(2*h)
        forward=(U(h*direction)-u0)/h
        directional.append({'eps':h,'central_slope':float(fd),'forward_slope':float(forward)})
    return {'stationarity':float(np.linalg.norm(sc[-1])/max(abs(u0),1e-30)),
        'gradients':[g.tolist() for g in sc],
        'gradient_relative_last_pair':dif,
        'predicted_slope':float(np.dot(sc[-1],direction)),
        'directional':directional}

def hessian_sweep(U,d,eps=EPS):
    z=np.zeros(d);u0=U(z);scales=[];matrices=[]
    for h in (eps,eps/2,eps/4):
        K=np.zeros((d,d));vpos={};vneg={}
        for i in range(d):
            a=z.copy();a[i]=h;vpos[i]=U(a);a[i]=-h;vneg[i]=U(a)
            K[i,i]=(vpos[i]-2*u0+vneg[i])/h**2
        for i in range(d):
            for j in range(i+1,d):
                a=np.zeros(d);a[i]=h;a[j]=h;pp=U(a)
                a[j]=-h;pm=U(a)
                a[i]=-h;mm=U(a)
                a[j]=h;mp=U(a)
                K[i,j]=K[j,i]=(pp-pm+mm-mp)/(4*h*h)
        eig=np.linalg.eigvalsh(K);scale=max(float(np.abs(eig).max()),1e-30)
        sign='NONNEGATIVE' if float(eig[0]) >= -.001*scale else 'NEGATIVE'
        scales.append({'eps':h,'min_eigenvalue':float(eig[0]),'max_abs_eigenvalue':scale,'sign_class':sign});matrices.append(K)
    rel=float(np.linalg.norm(matrices[-1]-matrices[-2])/max(np.linalg.norm(matrices[-1]),1e-30))
    signstable=len({r['sign_class'] for r in scales})==1
    # This is NOT official stability; a projective problem may invalidate smoothness.
    return {'scales':scales,'last_pair_rel_l2':rel,'hessian_tolerance':LIMIT_HESS,
        'sign_consistent':signstable,'converged':bool(rel<=LIMIT_HESS and signstable)}

def link_vector(cs):
    ret=[]
    for i,a in enumerate(cs):
        da=np.roll(a,-1,axis=0)-a;ma=.5*(a+np.roll(a,-1,axis=0))
        for b in cs[i+1:]:
            db=np.roll(b,-1,axis=0)-b;mb=.5*(b+np.roll(b,-1,axis=0))
            r=ma[:,None,:]-mb[None,:,:];den=np.maximum(np.linalg.norm(r,axis=2)**3,1e-18)
            numer=np.sum(np.cross(da[:,None,:],db[None,:,:])*r,axis=2)
            ret.append(float(np.sum(numer/den)/(4*np.pi)))
    return ret

def run_case(rec,raw_data, do_hessian, modes=2):
    t0=time.monotonic();case_id=rec['source_case_id'];native=parse_native(raw_data)
    stat={'case':case_id,'source_kind':rec['source_kind'],'catalog_id':rec['knotplot_catalog_id'],
      'roles':rec['roles'],'source_sha256':sha256_bytes(raw_data),'components':len(native),'native_beads':sum(map(len,native)),
      'status':'DIAGNOSTIC_ONLY_NO_ADMISSION','source_independence':'ONE_KNOTPLOT_CENSUS_FAMILY'}
    if rec.get('torus'):
        stat['torus_expected_components']=rec['torus']['components']
        stat['torus_component_gate']='PASS' if len(native)==rec['torus']['components'] else 'FAIL'
    else:stat['torus_component_gate']='NOT_APPLICABLE'
    arms={'native':native,'uniform300_no_relax':allocate(native,300)}
    armrows={}
    for name,comps in arms.items():
        counts=[max(24,int(round(96*length(c)/sum(length(v) for v in comps)))) for c in comps]
        seq0=[arc_resample(c,n) for c,n in zip(comps,counts)]
        P1,reach1,info1=recondition(seq0,counts)
        P2,reach2,info2=recondition(P1,counts)
        P3,reach3,info3=recondition(P2,counts)
        e1,e2,e3=kernel(P1),kernel(P2),kernel(P3)
        lr1,lr2=link_vector(P1),link_vector(P2)
        projector_drift=components_rms(P1,P2)
        proj_hchange=abs(e2-e1)/max(abs(e1),1e-30)
        row={'edge':edge_metrics(comps),'analysis_counts':counts,'projector_rms_relative':projector_drift,
             'E_P1':e1,'E_P2':e2,'E_P3':e3,'rel_energy_drift_P1_P2':proj_hchange,
             'delta_E_P1_P2':e2-e1,'delta_E_P2_P3':e3-e2,'reach_after_projection':[reach1,reach2,reach3],
             'reach_branches':[info1['branch'],info2['branch'],info3['branch']],
             'linking_P1':lr1,'linking_P2':lr2,
             'linking_drift_max':max((abs(x-y) for x,y in zip(lr1,lr2)),default=0.),
             'projector_idempotence_status':'DIAGNOSTIC_NONZERO' if projector_drift>1e-10 else 'WITHIN_1E-10'}
        U,d,evals=objective_factory(seq0,modes=modes)
        row['gradient']=gradient_sweep(U,d)
        if do_hessian:
            row['hessian']=hessian_sweep(U,d)
        else:row['hessian']={'status':'NOT_EVALUATED_PROFILE_BUDGET'}
        row['objective_evaluations']=evals[0]
        armrows[name]=row
    stat['arms']=armrows
    stat['runtime_seconds']=time.monotonic()-t0
    return stat

def serialize(row):return json.dumps(row,sort_keys=True,allow_nan=False)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=pathlib.Path,default=DEFAULT_SOURCE)
    parser.add_argument('--output',type=pathlib.Path,default=DEFAULT_RESULTS)
    parser.add_argument('--profile',choices=('BASIC','FULL'),default='BASIC')
    parser.add_argument('--modes',type=int,default=2)
    parser.add_argument('--start-index',type=int,default=0)
    parser.add_argument('--stop-index',type=int,default=100000)
    parser.add_argument('--resume',action='store_true')
    args=parser.parse_args()
    if args.modes<1:raise SystemExit('modes must be >=1')
    args.output.mkdir(parents=True,exist_ok=True)
    cases=json.loads((ROOT/'preregistration.json').read_text())
    full_candidates=set(cases['hessian_pilot_case_ids'])
    data=[];errors=[];status_counts={}
    checkpoints=args.output/'CHECKPOINTS';checkpoints.mkdir(exist_ok=True)
    for idx,rec in enumerate(cases['source_cases']):
        if idx<args.start_index or idx>=args.stop_index: continue
        checkpoint=checkpoints/(rec['source_case_id']+'.json')
        if args.resume and checkpoint.exists():
            print('RESUME',rec['source_case_id'],flush=True);continue
        p=args.source/rec['native_txt'].split('/')[-1]
        if not p.is_file():
            errors.append({'case':rec['source_case_id'],'error':'SOURCE_MISSING','filename':p.name});continue
        try:
            # BASIC: fixed pilot; FULL: entire corpus, still diagnostic, not A054 admission.
            hess=args.profile=='FULL' or rec['source_case_id'] in full_candidates
            a=run_case(rec,p.read_bytes(),hess,args.modes);data.append(a)
            checkpoint.write_text(serialize(a)+'\n',encoding='utf8')
            print(f"{a['case']} {a['components']} comps; projdrift R={a['arms']['native']['rel_energy_drift_P1_P2']:.5g}; H={a['arms']['native']['hessian'].get('last_pair_rel_l2','SKIP')}",flush=True)
        except Exception as ex:
            errors.append({'case':rec['source_case_id'],'error':type(ex).__name__,'detail':str(ex)});
            print('ERROR',rec['source_case_id'],ex,flush=True)
    # Merge durable checkpoints in preregistered order, including prior bounded runs.
    data=[]
    for rec in cases['source_cases']:
        p=checkpoints/(rec['source_case_id']+'.json')
        if p.is_file(): data.append(json.loads(p.read_text()))
    (args.output/'ROWS.jsonl').write_text(''.join(serialize(a)+'\n' for a in data),encoding='utf8')
    fields=['case','source_kind','catalog_id','roles','arm','components','native_beads','analysis_beads','edge_cv','edge_spread','projector_rms_relative','delta_E_P1_P2','rel_energy_drift_P1_P2','gradient_rel_last_pair','stationarity','hessian_rel_last_pair','hessian_converged','hessian_sign_consistent','status']
    with (args.output/'SCREEN_RESULTS.csv').open('w',newline='',encoding='utf8') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for x in data:
            for arm,row in x['arms'].items():
                h=row['hessian'];writer.writerow({'case':x['case'],'source_kind':x['source_kind'],'catalog_id':x['catalog_id'],
                    'roles':';'.join(x['roles']),'arm':arm,'components':x['components'],'native_beads':x['native_beads'],
                    'analysis_beads':sum(row['analysis_counts']),'edge_cv':row['edge']['edge_cv'],'edge_spread':row['edge']['edge_spread_relative'],
                    'projector_rms_relative':row['projector_rms_relative'],'delta_E_P1_P2':row['delta_E_P1_P2'],
                    'rel_energy_drift_P1_P2':row['rel_energy_drift_P1_P2'],'gradient_rel_last_pair':row['gradient']['gradient_relative_last_pair'],
                    'stationarity':row['gradient']['stationarity'],'hessian_rel_last_pair':h.get('last_pair_rel_l2',''),
                    'hessian_converged':h.get('converged',''),'hessian_sign_consistent':h.get('sign_consistent',''),'status':'DIAGNOSTIC_ONLY'})
    cnt_h=sum('last_pair_rel_l2' in row['hessian'] for a in data for row in a['arms'].values())
    hs=[r['hessian'] for a in data for r in a['arms'].values() if 'last_pair_rel_l2' in r['hessian']]
    nonid=sum(r['projector_idempotence_status']=='DIAGNOSTIC_NONZERO' for a in data for r in a['arms'].values())
    summary={'schema':'A054-GEOMETRY-SCREEN-RUN-SUMMARY-1','profile':args.profile,'mode_count_per_component':args.modes,
        'census_source_count_expected':len(cases['source_cases']),'census_source_count_processed':len(data),
        'completeness':'FULL_CORPUS' if len(data)==len(cases['source_cases']) else 'PARTIAL_CHECKPOINTED',
        'arms_processed':sum(len(a['arms']) for a in data),'hessian_arms_processed':cnt_h,
        'hessian_converged_diagnostic_count':sum(x.get('converged',False) for x in hs),
        'hessian_failed_diagnostic_count':sum(not x.get('converged',False) for x in hs),
        'projector_nonidempotent_arms_threshold_1e-10':nonid,
        'errors':errors,'missing_registered_sources':cases['missing_targets'],
        'A054_v0_5_1_changed':False,'A057_handoffs':0,
        'admission':'NO_AUTHORIZED_A054_SELECTION_OR_A057_TRANSFER',
        'source_census_zip_sha256':sha256_bytes((ROOT/'inputs'/'falsifier_census_v0.1.0_output.zip').read_bytes()) if (ROOT/'inputs'/'falsifier_census_v0.1.0_output.zip').is_file() else None,
        'protocol_sha256':sha256_bytes((ROOT/'preregistration.json').read_bytes())}
    (args.output/'RUN_SUMMARY.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print('RUN_SUMMARY',json.dumps({k:v for k,v in summary.items() if k not in ('errors','missing_registered_sources')},ensure_ascii=False),flush=True)
    if errors:sys.exit(2)

if __name__=='__main__':main()
