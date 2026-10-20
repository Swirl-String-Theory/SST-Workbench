#!/usr/bin/env python3
"""F005 v0.3.0: source-preserving split/integrity audit + TRAIN/VAL ARX baseline.

Not a fluid Euler solver; not a PKLSA falsifier. Does not evaluate test or OOD
outputs, modify source files, nor touch large DATASET.zip. Requires numpy.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, sys
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timezone

VERSION = '0.3.0'
PARTITIONS = {'STANDARD_TRAIN', 'STANDARD_VALIDATION', 'STANDARD_TEST', 'OPTIMIZED_OOD'}
COUNTS = {'STANDARD_TRAIN': 3500, 'STANDARD_VALIDATION': 750, 'STANDARD_TEST': 750, 'OPTIMIZED_OOD': 4822}


def sha256_file(path: Path) -> str:
    d=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): d.update(block)
    return d.hexdigest()


def read_split(path: Path, n: int, expected: dict | None=COUNTS) -> dict:
    labels={}; duplicates=[]; errors=[]
    with path.open(newline='',encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            try: i=int(row['row_id_zero_based']);label=row['candidate_partition'].strip()
            except (KeyError,ValueError) as exc: errors.append(str(exc));continue
            if i in labels: duplicates.append(i)
            labels[i]=label
    counts=dict(Counter(labels.values()))
    missing=sorted(set(range(n))-set(labels));extra=sorted(set(labels)-set(range(n)))
    if missing or extra or duplicates or set(counts)-PARTITIONS:errors.append('ID/partition integrity failure')
    if expected is not None and counts!=expected:errors.append('Expected partition counts mismatch')
    errors=sorted(set(errors))
    return {'status':'PASS' if not errors else 'FAIL','count':len(labels),'counts':counts,'missing_count':len(missing),'extra_count':len(extra),'duplicate_ids':duplicates[:20],'issues':errors,'labels':labels}


def read_metadata(path:Path,n:int)->dict:
    with path.open(newline='',encoding='utf-8-sig') as f:
        rows=list(csv.DictReader(f))
    return {'rows':rows,'count':len(rows),'headings':list(rows[0]) if rows else [], 'count_matches':len(rows)==n}


def check_metadata_groups(meta:list[dict], labels:dict[int,str]) -> dict:
    groups={}; summaries={}
    for field in ('trajectory_id','trajectory_label','trajectory_subset'):
        table=defaultdict(set); nonempty=0
        for i,row in enumerate(meta):
            val=(row.get(field) or '').strip()
            if val and i in labels: table[val].add(labels[i]);nonempty+=1
        overlap=[{'value':v[:120],'partitions':sorted(vals)} for v,vals in table.items() if len(vals)>1]
        sizes=Counter((row.get(field) or '').strip() for row in meta if (row.get(field) or '').strip())
        summaries[field]={'nonempty':nonempty,'unique':len(table),'duplicated_labels':sum(1 for val in sizes if sizes[val]>1),'cross_partition_labels':len(overlap),'examples':overlap[:10]}
    # trajectory_subset is a publisher cohort, NOT a family key, and is never used as a blocker
    blockers=[]
    if summaries['trajectory_id']['cross_partition_labels']>0:blockers.append('trajectory_id across partitions')
    if summaries['trajectory_label']['cross_partition_labels']>0:blockers.append('trajectory_label across partitions: REVIEW semantic grouping')
    return {'fields':summaries,'blockers':blockers,'warning':'trajectory_subset is a COHORT label, not evidence of wave-form family leakage; duplicated trajectory_label may or may not denote one family'}


def normalized_input_fingerprint(x) -> str:
    """Heuristic-only fingerprint, cannot certify waveform-family independence."""
    import numpy as np
    x=np.asarray(x,dtype=np.float64)
    if not np.isfinite(x).all():return 'NONFINITE'
    maxabs=float(np.max(np.abs(x)))
    if maxabs<1e-12:return 'ALL_ZERO'
    y=x/maxabs
    # 64 bins mean, quantized to nearest 0.05. Flag possible near-duplicates only.
    groups=np.array_split(y,min(64,len(y)))
    q=np.rint(np.array([np.mean(v) for v in groups])*20).astype(np.int16)
    return hashlib.sha256(q.tobytes()).hexdigest()


def audit_input_content(a,labels:dict[int,str]) ->dict:
    import numpy as np
    exact=defaultdict(lambda: defaultdict(list)); approx=defaultdict(lambda:defaultdict(list))
    nonfinite=[]
    for i,label in sorted(labels.items()):
        row=np.asarray(a[i],dtype=np.float64)
        if not np.isfinite(row).all():nonfinite.append(i);continue
        digest=hashlib.sha256(row.tobytes()).hexdigest()
        exact[digest][label].append(i)
        approx[normalized_input_fingerprint(row)][label].append(i)
    def conflicts(dictionary):
        return [{'partitions':sorted(by.keys()),'row_examples':{s:ids[:3] for s,ids in by.items()},'total_rows':sum(map(len,by.values()))}
                for by in dictionary.values() if len(by)>1]
    xc=conflicts(exact);pc=conflicts(approx)
    return {'rows_checked':len(labels),'nonfinite_row_count':len(nonfinite),'nonfinite_examples':nonfinite[:10],
            'exact_duplicate_cross_partition_groups':len(xc),'exact_examples':xc[:15],
            'coarse_shape_cross_partition_groups':len(pc),'coarse_examples':pc[:15],
            'status':'FAIL' if nonfinite or xc else 'REVIEW',
            'warning':'Coarse normalized shape collisions are heuristics: both false positives and false negatives possible; absence is not proof of no leakage'}


def derive_oscillator_coefficients(beta,dt):
    import numpy as np
    A,B,C=map(float,beta)
    roots=np.roots([1.0,-A,-B]);moduli=np.abs(roots)
    stable=bool(np.all(moduli<1))
    oscillatory=bool(abs(np.imag(roots[0]))>1e-10)
    gamma=None;f=None;K=None
    if stable and oscillatory:
        radius=float(moduli[0]); gamma=float(-np.log(radius)/dt)
        f=float(abs(np.angle(roots[0]))/(2*np.pi*dt))
        if abs(1-B)>1e-10:
            gamma_cd=(1+B)/(1-B)/dt
            K=-C*(1+gamma_cd*dt)
    return {'discrete_A':A,'discrete_B':B,'acceleration_coefficient_C':C,
            'pole_real_imag':[[float(v.real),float(v.imag)] for v in roots],
            'poles_stable':stable,'complex_oscillatory_poles':oscillatory,
            'ringdown_gamma_per_s':gamma,'ringdown_frequency_hz':f,
            'central_difference_coupling_K_dimensionless':K}


def fit_arx_train(a,y,train_ids:list[int],dt:float):
    """Fit ARX(2)+forcing via a numerically better conditioned second difference.

    d2y[n] = D*y[n] + E*(y[n]-y[n-1]) + C*dt^2*acc[n];
    A=2+D+E, B=-1-E. y is meters, acceleration in m s^-2.
    Never fits on validation/test/OOD target arrays.
    """
    import numpy as np
    scaling=np.array([1e-4,1e-5,1e-5],dtype=np.float64)
    G=np.zeros((3,3));v=np.zeros(3);n=0
    for idx in train_ids:
        yy=np.asarray(y[idx],dtype=np.float64)*1e-3
        xx=np.asarray(a[idx],dtype=np.float64)
        if not (np.all(np.isfinite(yy)) and np.all(np.isfinite(xx))):continue
        X=np.column_stack((yy[1:-1], yy[1:-1]-yy[:-2], dt*dt*xx[1:-1])) / scaling
        target=yy[2:]-2*yy[1:-1]+yy[:-2]
        G+=X.T@X;v+=X.T@target;n+=len(target)
    if n==0:raise RuntimeError('No finite training observations')
    lam=1e-14*max(float(np.trace(G))/3,1)
    de_c=(np.linalg.solve(G+lam*np.eye(3),v)/scaling)
    D,E,C=map(float,de_c)
    beta=np.array([2+D+E,-1-E,C])
    return beta, {'num_rows':len(train_ids),'num_pairs':n,'regularization':lam,
                  'fit_parameterization':'second difference (numerical conditioning)',
                  'features':'elevation(t), elevation(t)-elevation(t-dt), acceleration(t)*dt^2',
                  'target':'elevation(t+dt)-2*elevation(t)+elevation(t-dt) [m]'}

def validate_one_step(a,y,ids:list[int],dt:float,beta):
    """Teacher-forced one-step diagnostics on VALIDATION only, not free rollout."""
    import numpy as np
    sse=sst=baseline=0.; n=0
    for idx in ids:
        yy=np.asarray(y[idx],dtype=np.float64)*1e-3
        aa=np.asarray(a[idx],dtype=np.float64)
        if not (np.isfinite(yy).all() and np.isfinite(aa).all()):continue
        pred=beta[0]*yy[1:-1]+beta[1]*yy[:-2]+beta[2]*dt*dt*aa[1:-1]
        tgt=yy[2:]
        sse+=float(np.sum((pred-tgt)**2));sst+=float(np.sum(tgt*tgt))
        baseline+=float(np.sum((yy[1:-1]-tgt)**2));n+=len(tgt)
    if not n:raise RuntimeError('No valid validation points')
    return {'validation_rows':len(ids),'samples':n,'one_step_rmse_m':float(math.sqrt(sse/n)),
            'persistence_rmse_m':float(math.sqrt(baseline/n)),
            'improvement_over_persistence_percent':float(100*(1-math.sqrt(sse/max(baseline,1e-99)))),
            'warning':'Teacher-forced one-step error; NOT a multi-second open-loop wave prediction'}


def read_time_seconds(p:Path,n:int)->float:
    import numpy as np
    with p.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
    if len(rows)!=n:raise ValueError(f'time series length {len(rows)} != {n}')
    if not rows or 'time_s' not in rows[0]:raise ValueError('Missing explicit time_s header')
    t=np.array([float(r['time_s']) for r in rows]); diff=np.diff(t)
    if len(diff)<2 or not np.all(np.isfinite(t)) or not np.all(diff>0):raise ValueError('Invalid time axis')
    dt=float(np.median(diff))
    if np.max(np.abs(diff-dt))>max(1e-7,dt*1e-3):raise ValueError('Time jitter >0.1%')
    return dt


def run(root:Path, do_fit:bool=True)->dict:
    import numpy as np
    root=root.resolve()
    out=root/'outputs'/'f005_integrity_baseline_v0.3.0';out.mkdir(parents=True,exist_ok=True)
    pilot_file=root/'outputs'/'f005_data_pilot_v0.2.0'/'pilot_report.json'
    split_path=root/'outputs'/'f005_data_pilot_v0.2.0'/'candidate_split_NOT_BLIND.csv'
    if not pilot_file.is_file() or not split_path.is_file():raise FileNotFoundError('Run v0.2.0 first: pilot_report.json and candidate_split_NOT_BLIND.csv are required')
    pilot=json.loads(pilot_file.read_text(encoding='utf-8'))
    data=Path(pilot.get('robot',{}).get('robot_directory',''))
    if not data.is_dir(): data=root/'outputs'/'data_preflight_v0.1.0'/'data'/'robot_sloshing'/'raw_extracted'
    a=np.load(data/'INPUT_TRAIN.npy',mmap_mode='r',allow_pickle=False)
    y=np.load(data/'OUTPUT_TRAIN.npy',mmap_mode='r',allow_pickle=False)
    if a.shape!=(9822,1500) or y.shape!=a.shape:raise ValueError(f'Unexpected data shape: {a.shape} and {y.shape}')
    split=read_split(split_path,a.shape[0]);labels=split.pop('labels')
    md=read_metadata(data/'trajectory_metadata.csv',a.shape[0])
    metadata=check_metadata_groups(md['rows'],labels) if md['count_matches'] else {'status':'FAIL','reason':'Metadata count mismatch'}
    inputs=audit_input_content(a,labels) if split['status']=='PASS' else {'status':'NOT_RUN'}
    dt=read_time_seconds(data/'time_vector.csv',a.shape[1])
    source_hashes={'pilot_report_sha256':sha256_file(pilot_file),'candidate_split_sha256':sha256_file(split_path),'metadata_sha256':sha256_file(data/'trajectory_metadata.csv')}
    data_status=('FAIL' if split['status']=='FAIL' or not md['count_matches'] or inputs['status']=='FAIL' or metadata.get('blockers') else 'REVIEW_NO_BLIND_CERTIFICATION')
    result={'tool':'F005_Integrity_Baseline_v0.3.0','timestamp_utc':datetime.now(timezone.utc).isoformat(),
        'scientific_status':'DEVELOPMENT_NOT_BLIND_NOT_PKLSA_NOT_EULER', 'source_hashes':source_hashes,
        'P5':{'status':data_status,'split_integrity':split,'metadata':{'count':md['count'],'headings':md['headings'],'groups':metadata},'input_leakage':inputs,'time_step_s':dt},
        'P6':{'status':'NOT_RUN'},'P7':'NOT_RUN','P8':'UNRESOLVED','data_directory':str(data)}
    if do_fit and data_status=='REVIEW_NO_BLIND_CERTIFICATION':
        tr=[i for i,lab in labels.items() if lab=='STANDARD_TRAIN']
        va=[i for i,lab in labels.items() if lab=='STANDARD_VALIDATION']
        beta,details=fit_arx_train(a,y,tr,dt)
        model=derive_oscillator_coefficients(beta,dt)
        val=validate_one_step(a,y,va,dt,beta)
        result['P6']={'status':'ARX_DEV_ONLY_NOT_EULER','training':details,'model':model,'validation':val,
            'no_test_peeking':True,'limitations':['one-step teacher-forced','candidate split is non-blind','not nonlinear Euler','not PKLSA','no field velocity measured']}
    elif do_fit:result['P6']={'status':'BLOCKED_SPLIT_LEAKAGE','reason':'Split or data content fails integrity gate; no training allowed'}
    (out/'audit_report.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    with (out/'AUDIT_SUMMARY.md').open('w',encoding='utf-8') as f:
        f.write('# F005 external data audit v0.3.0 — DEVELOPMENT\n\n')
        f.write('**P5: '+data_status+'**; **P6: '+result['P6']['status']+'**; P7 NOT RUN; P8 UNRESOLVED.\n\n')
        f.write('## Source integrity\n\n'); f.write('Split: '+str(split)+'\n\n')
        f.write('Metadata group collisions: '+str(metadata.get('blockers',[]))+'\n\n')
        f.write('Input exact-duplicate cross-partition groups: '+str(inputs.get('exact_duplicate_cross_partition_groups'))+'\n\n')
        f.write('Input approximate shape cross-partition groups (diagnostic only): '+str(inputs.get('coarse_shape_cross_partition_groups'))+'\n\n')
        f.write('## Model\n\n');f.write(json.dumps(result['P6'],indent=2,ensure_ascii=False)+'\n\n')
        f.write('**Do not claim physical SST/PKLSA validation, certified blind split, or Euler closure.**\n')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path.cwd())
    parser.add_argument('--audit-only',action='store_true')
    args=parser.parse_args()
    try:r=run(args.root,not args.audit_only)
    except Exception as exc:
        print(f'BLOCKED: {type(exc).__name__}: {exc}',file=sys.stderr);return 2
    print(json.dumps({'P5':r['P5']['status'],'P6':r['P6']['status'],'output':str(args.root/'outputs'/'f005_integrity_baseline_v0.3.0')},indent=2))
    return 0 if r['P5']['status']!='FAIL' else 2

if __name__=='__main__':sys.exit(main())
