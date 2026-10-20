#!/usr/bin/env python3
"""F005-v0.4.1: frozen-ARX conditional open-loop forecasts and INPUT-ONLY waveform-family audit.

DEVELOPMENT, NOT BLIND, NOT EULER, NOT PKLSA. Never evaluates TEST/OOD response arrays.
Needs numpy and matplotlib for PDF. Source ZIP archives are never opened.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys

VERSION = '0.4.1'
LABELS = ('STANDARD_TRAIN', 'STANDARD_VALIDATION', 'STANDARD_TEST', 'OPTIMIZED_OOD')
EXPECTED = {'STANDARD_TRAIN': 3500, 'STANDARD_VALIDATION': 750,
            'STANDARD_TEST': 750, 'OPTIMIZED_OOD': 4822}
HORIZONS_S = (0.1, 0.5, 1.0, 2.0, 3.0)
ANCHOR_S = (0.004, 1.5, 2.8)
# Parameters of detection algorithms are fixed in the distributed source before real data run.
FAMILY_MAX_BUCKET = 140
FAMILY_MAX_PAIRS = 15000
FAMILY_MAX_EXAMPLES = 250
SHAPE_CORRELATION = 0.995
SHAPE_RMSE_LIMIT = 0.075
SHIFT_SAMPLES = (-4, -2, 0, 2, 4)


def hash_file(p: Path) -> str:
    sha = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(2**20), b''):
            sha.update(b)
    return sha.hexdigest()


def read_split(p: Path, n: int, expected: dict | None=EXPECTED):
    ids = {}
    with p.open('r', newline='', encoding='utf-8-sig') as f:
        r = csv.DictReader(f)
        assert {'row_id_zero_based', 'candidate_partition'} <= set(r.fieldnames or []), 'Split headers missing'
        for row in r:
            idx = int(row['row_id_zero_based'])
            lab = row['candidate_partition'].strip()
            if idx in ids:
                raise ValueError('Duplicate candidate split index: '+str(idx))
            if idx < 0 or idx >= n or lab not in LABELS:
                raise ValueError('Invalid split label/index')
            ids[idx] = lab
    if len(ids) != n or len(set(ids)) != n:
        raise ValueError('Incomplete candidate split')
    counts = dict(Counter(ids.values()))
    if expected is not None and counts != expected:
        raise ValueError('Wrong candidate partition counts: '+repr(counts))
    return ids, counts


def load_time(p: Path, n: int):
    import numpy as np
    with p.open('r', newline='', encoding='utf-8-sig') as f:
        rr = list(csv.DictReader(f))
    if len(rr) != n or not rr or 'time_s' not in rr[0]:
        raise ValueError('Invalid time vector')
    t = np.array([float(v['time_s']) for v in rr], dtype='float64')
    steps = np.diff(t)
    if not np.all(np.isfinite(t)) or not np.all(steps > 0):
        raise ValueError('Non-finite/non-monotonic time')
    dt = float(np.median(steps))
    if float(np.max(abs(steps-dt))) > max(1e-7, dt*1e-3):
        raise ValueError('Time axis jitter too large')
    return dt


def read_metadata(p: Path, n: int):
    with p.open('r', newline='', encoding='utf-8-sig') as f:
        rr = list(csv.DictReader(f))
    if len(rr) != n:
        raise ValueError('Metadata rows mismatch')
    for key in ('trajectory_id', 'trajectory_label', 'trajectory_subset'):
        if key not in rr[0]:
            raise ValueError('Metadata field missing: '+key)
    return rr


def source_lock(root: Path):
    """Read only local v0.3 verified data; never read TEST/OOD outputs."""
    import numpy as np
    old = root / 'outputs' / 'f005_integrity_baseline_v0.3.0' / 'audit_report.json'
    pilot_path = root / 'outputs' / 'f005_data_pilot_v0.2.0' / 'pilot_report.json'
    split_path = root / 'outputs' / 'f005_data_pilot_v0.2.0' / 'candidate_split_NOT_BLIND.csv'
    for p in (old, pilot_path, split_path):
        if not p.is_file():
            raise FileNotFoundError('Required prior run file not found: '+str(p))
    audit = json.loads(old.read_text(encoding='utf-8'))
    pilot = json.loads(pilot_path.read_text(encoding='utf-8'))
    if audit['tool'] != 'F005_Integrity_Baseline_v0.3.0':
        raise ValueError('Unexpected model audit tool/version')
    if audit['P5']['split_integrity']['status'] != 'PASS':
        raise ValueError('v0.3 split integrity not PASS')
    if audit['P5']['status'] != 'REVIEW_NO_BLIND_CERTIFICATION':
        raise ValueError('v0.3 P5 blocked or changed')
    if audit['P6']['status'] != 'ARX_DEV_ONLY_NOT_EULER' or audit['P6'].get('no_test_peeking') is not True:
        raise ValueError('v0.3 model is not safe to lock')
    dd = Path(pilot['robot']['robot_directory'])
    if not dd.is_dir():
        dd = root/'outputs'/'data_preflight_v0.1.0'/'data'/'robot_sloshing'/'raw_extracted'
    files = {key: dd/key for key in ('INPUT_TRAIN.npy','OUTPUT_TRAIN.npy','time_vector.csv','trajectory_metadata.csv')}
    for p in files.values():
        if not p.is_file():
            raise FileNotFoundError('Missing robot data: '+str(p))
    expected_sha = audit['source_hashes']
    required = {'pilot_report_sha256': hash_file(pilot_path),
                'candidate_split_sha256': hash_file(split_path),
                'metadata_sha256': hash_file(files['trajectory_metadata.csv'])}
    if any(expected_sha.get(k) != v for k,v in required.items()):
        raise ValueError('Source lock mismatch: pilot / candidate split / metadata hashes')
    a = np.load(files['INPUT_TRAIN.npy'], mmap_mode='r', allow_pickle=False)
    y = np.load(files['OUTPUT_TRAIN.npy'], mmap_mode='r', allow_pickle=False)
    if a.shape != (9822,1500) or y.shape != a.shape or a.dtype != np.float64 or y.dtype != np.float64:
        raise ValueError('Unexpected array shape/dtype')
    dt = load_time(files['time_vector.csv'], a.shape[1])
    if not math.isclose(dt, audit['P5']['time_step_s'], rel_tol=1e-8):
        raise ValueError('Local time step differs from frozen audit')
    labels,counts = read_split(split_path, a.shape[0])
    meta = read_metadata(files['trajectory_metadata.csv'],a.shape[0])
    model = audit['P6']['model']
    beta = tuple(float(model[k]) for k in ('discrete_A','discrete_B','acceleration_coefficient_C'))
    roots = np.roots([1.0,-beta[0],-beta[1]])
    if not np.all(np.abs(roots) < 1) or model['poles_stable'] is not True:
        raise ValueError('v0.3 parameters not a stable frozen model')
    return dict(a=a,y=y,dt=dt,labels=labels,counts=counts,metadata=meta,
                beta=beta,audit=audit,old_path=old,split_path=split_path,
                input_path=files['INPUT_TRAIN.npy'],output_path=files['OUTPUT_TRAIN.npy'],
                source_hashes=required)


def aggregate_shape(row, bins=64):
    """Sign-preserving, amplitude-normalized input shape. Only external accelerations."""
    import numpy as np
    x = np.asarray(row, dtype=np.float64)
    if not np.isfinite(x).all():
        raise ValueError('Nonfinite acceleration input')
    maxabs = float(np.max(np.abs(x)))
    if maxabs < 1e-12:
        return np.zeros(bins, dtype='float64')
    vals = x/maxabs
    parts = np.array_split(vals, bins)
    return np.array([float(p.mean()) for p in parts])


def fingerprint(x, bins, step):
    import numpy as np
    v = aggregate_shape(x,bins)
    return hashlib.sha256(np.rint(v/step).astype(np.int16).tobytes()).hexdigest()


def compare_shapes(a,b,shifts=SHIFT_SAMPLES):
    """Return conservative similarity for timing shifts; all quantities input-derived."""
    import numpy as np
    aa=np.asarray(a,dtype=np.float64);bb=np.asarray(b,dtype=np.float64)
    if not (np.isfinite(aa).all() and np.isfinite(bb).all()):
        raise ValueError('Nonfinite vector')
    sa=float(np.max(np.abs(aa)));sb=float(np.max(np.abs(bb)))
    if sa<1e-12 or sb<1e-12:
        return {'correlation':1.0 if sa<1e-12 and sb<1e-12 else 0.,
                'norm_rmse':0. if sa<1e-12 and sb<1e-12 else 2.,'shift':0}
    aa=aa/sa;bb=bb/sb
    best={'correlation':-2.0,'norm_rmse':float('inf'),'shift':0}
    for lag in shifts:
        x=aa[max(0,lag):len(aa)+min(0,lag)]
        y=bb[max(0,-lag):len(bb)+min(0,-lag)]
        if len(x)<8:continue
        xd=x-float(np.mean(x));yd=y-float(np.mean(y))
        denom=math.sqrt(float(np.dot(xd,xd)*np.dot(yd,yd)))
        corr=float(np.dot(xd,yd)/denom) if denom>1e-12 else (1.0 if np.allclose(x,y) else 0.0)
        nrmse=float(np.sqrt(np.mean((x-y)**2)))
        if corr>best['correlation'] or (abs(corr-best['correlation'])<1e-12 and nrmse<best['norm_rmse']):
            best={'correlation':corr,'norm_rmse':nrmse,'shift':int(lag)}
    return best


class DSU:
    def __init__(self,n):
        self.par=list(range(n));self.size=[1]*n
    def find(self,a):
        while self.par[a]!=a:
            self.par[a]=self.par[self.par[a]];a=self.par[a]
        return a
    def union(self,a,b):
        a=self.find(a);b=self.find(b)
        if a!=b:
            if self.size[a]<self.size[b]:a,b=b,a
            self.par[b]=a;self.size[a]+=self.size[b]


def family_audit(input_arrays, labels, max_pairs=FAMILY_MAX_PAIRS, max_bucket=FAMILY_MAX_BUCKET):
    """Deterministic bounded INPUT-ONLY waveform screening, not exhaustive family certification.

    Complete exact-byte cross-partition SHA-256 check is performed independently.
    Approximate morphology screening uses bounded comparisons across fingerprint buckets,
    then a stable global cap. Dense buckets are sampled, not silently ignored.
    """
    import numpy as np
    from bisect import bisect_left
    n=len(labels)
    ids=sorted(labels)
    buckets=[defaultdict(list) for _ in range(3)]
    exact_hashes=defaultdict(lambda:defaultdict(list))
    zero=[]; nonfinite=[]
    for i in ids:
        v=np.asarray(input_arrays[i], dtype=np.float64)
        if not np.isfinite(v).all():
            nonfinite.append(i)
            continue
        if float(np.max(np.abs(v))) < 1e-12:
            zero.append(i)
        exact_hashes[hashlib.sha256(v.tobytes()).hexdigest()][labels[i]].append(i)
        for b,(count,quantum) in zip(buckets,((64,.05),(32,.1),(16,.20))):
            b[fingerprint(v,count,quantum)].append(i)
    if nonfinite:
        return dict(status='BLOCKED_NONFINITE_INPUT',rows_checked=n,
                    nonfinite_input_count=len(nonfinite),nonfinite_input_examples=nonfinite[:10],
                    candidate_pairs_scored=0,exact_duplicate_cross_partition_pairs=None), []
    exact_cross=sum(sum(len(x)*len(y) for j,(_,x) in enumerate(sorted(gr.items()))
                        for _,y in sorted(gr.items())[j+1:])
                    for gr in exact_hashes.values() if len(gr)>1)
    # Cross-partition representatives and local within-partition neighbours for each row.
    # Complexity in each bucket is O(4 * bucket size) rather than O(bucket size^2).
    proposed=set(); large_sampled=0; max_seen=0
    for dictionary in buckets:
        for signature, entries in sorted(dictionary.items()):
            bb=sorted(set(entries))
            if len(bb)<=1: continue
            max_seen=max(max_seen,len(bb))
            if len(bb)>max_bucket:
                large_sampled+=1
            by_label={q:sorted(i for i in bb if labels[i]==q) for q in LABELS}
            for i in bb:
                part=labels[i]
                same=by_label[part]
                ix=bisect_left(same,i)
                for j in (same[ix-1:ix]+same[ix+1:ix+2]):
                    if i!=j:proposed.add((min(i,j),max(i,j)))
                # Stratified opposite-partition candidates with deterministic fractional ranks.
                for q in LABELS:
                    other=by_label[q]
                    if q==part or not other:continue
                    rank=bisect_left(other,i)
                    js={other[0],other[-1],other[min(rank,len(other)-1)],
                        other[min((i*2654435761)%len(other),len(other)-1)]}
                    for j in js:
                        if i!=j:proposed.add((min(i,j),max(i,j)))
    pre_cap=len(proposed)
    if len(proposed)>max_pairs:
        # Stable hash ordering prevents scan-order bias when capping comparisons.
        proposed=set(sorted(proposed,key=lambda ij:(hashlib.blake2b(f'{ij[0]}:{ij[1]}'.encode(),
                          digest_size=8).digest(),ij))[:max_pairs])
    dsu=DSU(max(ids)+1 if ids else 0)
    near_cross=0;near_total=0;scored=0;examples=[]
    for i,j in sorted(proposed):
        obs=compare_shapes(input_arrays[i],input_arrays[j]);scored+=1
        matched=(obs['correlation']>=SHAPE_CORRELATION and obs['norm_rmse']<=SHAPE_RMSE_LIMIT)
        if matched:
            near_total+=1;dsu.union(i,j)
            if labels[i]!=labels[j]:
                near_cross+=1
                if len(examples)<FAMILY_MAX_EXAMPLES:
                    examples.append({'row_a':i,'partition_a':labels[i],
                        'row_b':j,'partition_b':labels[j],
                        **{k:round(v,7) if isinstance(v,float) else v for k,v in obs.items()}})
    comp=defaultdict(list)
    for i in ids:comp[dsu.find(i)].append(i)
    crosses=[v for v in comp.values() if len({labels[z] for z in v})>1]
    return dict(status='REVIEW_BOUNDED_SCREEN_NOT_FAMILY_CERTIFIED', rows_checked=n,
        nonfinite_input_count=0, all_zero_input_count=len(zero),
        fingerprint_methods=['64-bins/0.05','32-bins/0.1','16-bins/0.20'],
        candidate_pairs_proposed=pre_cap,candidate_pairs_scored=scored,
        candidate_pairs_not_scored_due_cap=max(0,pre_cap-scored),
        max_pair_budget=max_pairs,large_buckets_sampled=large_sampled,
        largest_bucket_size=max_seen,
        exact_duplicate_cross_partition_pairs=exact_cross,
        near_shape_cross_partition_pairs=near_cross,
        near_shape_total_pairs=near_total,
        family_components_cross_partition=len(crosses),
        cross_partition_component_examples=[{'size':len(c),'partitions':dict(Counter(labels[x] for x in c)),
             'row_examples':c[:8]} for c in crosses[:20]],
        thresholds={'correlation_min':SHAPE_CORRELATION,'normalized_rmse_max':SHAPE_RMSE_LIMIT,
                    'shift_samples':list(SHIFT_SAMPLES)},
        notes=['EXACT byte-duplicate scan is complete for finite inputs.',
               'Approximate morphology screening is bounded and NOT EXHAUSTIVE.',
               'Capped or unsampled candidate pairs may contain missed family matches.',
               'Near match flags REVIEW only, not publisher-defined family identity.',
               'P6a runs as conditional DEVELOPMENT regardless of incomplete P5b screen.',
               'No TEST/OOD response array accessed.']), examples


def rollouts(a,y,dt,beta,ids,anchors_s=ANCHOR_S,horizons_s=HORIZONS_S):
    """Independent measured seed at each PREDECLARED anchor, no output updates during any horizon.

    At t=n we have observed (y[n-1], y[n]) and KNOWN FUTURE forcing a(t).
    Prediction y[n+k] uses only predicted heights and a; no teacher-forcing.
    """
    import numpy as np
    if not ids:raise ValueError('No validation IDs')
    x=np.asarray(a[ids],dtype=np.float64)
    target=np.asarray(y[ids],dtype=np.float64)*1e-3
    if x.shape!=target.shape or not np.isfinite(x).all() or not np.isfinite(target).all():
        raise ValueError('Nonfinite/wrong validation arrays')
    N,T=target.shape
    results=[];trace=[]
    for ts in anchors_s:
        n0=max(1,int(round(ts/dt)))
        n_h=[int(round(h/dt)) for h in horizons_s]
        if n0+max(n_h)>=T:
            raise ValueError('Anchor plus largest horizon beyond duration')
        max_steps=max(n_h)
        prev=target[:,n0-1].copy();cur=target[:,n0].copy()
        initial_slope=cur-prev
        initial=cur.copy()
        errors={int(k):{} for k in n_h}
        chosen=sorted(set([0, 1, 2]))[:min(3,N)]
        traces={j:[(n0*dt,float(target[j,n0]),float(cur[j]),float(initial[j]),float(initial[j]))] for j in chosen}
        for step in range(1,max_steps+1):
            source=n0+step-1
            pred=beta[0]*cur+beta[1]*prev+beta[2]*dt*dt*x[:,source]
            prev,cur=cur,pred
            tt=target[:,n0+step]
            hold=initial
            linear=initial+step*initial_slope
            if step in errors:
                errors[step]={'arx':float(np.sqrt(np.mean((cur-tt)**2))),
                              'hold':float(np.sqrt(np.mean((hold-tt)**2))),
                              'linear':float(np.sqrt(np.mean((linear-tt)**2))),
                              'max_abs_prediction_m':float(np.max(abs(cur)))}
            if step==1 or step%20==0 or step==max_steps:
                for j in chosen:
                    traces[j].append(((n0+step)*dt,float(tt[j]),float(cur[j]),float(hold[j]),float(linear[j])))
        for h,k in zip(horizons_s,n_h):
            e=errors[k]; baseline=min(e['hold'],e['linear'])
            results.append({'anchor_time_s':round(n0*dt,7),'horizon_s':round(k*dt,7),
                'validation_trajectories':N,
                'rmse_arx_m':e['arx'],'rmse_persistence_m':e['hold'],
                'rmse_linear_extrap_m':e['linear'],
                'rmse_best_baseline_m':baseline,
                'arx_improvement_vs_best_baseline_percent':float(100*(1-e['arx']/baseline)) if baseline>0 else None,
                'max_abs_predicted_height_m':e['max_abs_prediction_m']})
        for j in chosen:
            for t_obs,meas,arp,hol,lin in traces[j]:
                trace.append({'anchor_s':round(n0*dt,6),'row_id_zero_based':ids[j],
                             'time_s':round(t_obs,6),'measured_m':meas,'arx_m':arp,
                             'persistence_m':hol,'linear_extrap_m':lin})
    return results,trace


def make_pdf(out:Path, report:dict, trace:list, summaryrows:list):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    with PdfPages(out) as pdf:
        fig=plt.figure(figsize=(8.27,11.69));ax=fig.add_axes([.08,.12,.86,.78]);ax.axis('off')
        f=report['P6a']['frozen_arx'];fa=report['P5b']['morphology_audit']
        status='F005 v0.4.1  |  DEVELOPMENT / NON-BLIND'
        ax.text(0,1,status,fontsize=16,weight='bold',va='top',transform=ax.transAxes)
        s=("Independent-input waveform morphology audit and conditional free-run forecast\n"
           "Source: local Zenodo robot sloshing array; no 49.9-GB archive accessed\n\n"
           "Locked ARX(2) parameters, from F005-v0.3.0 TRAIN ONLY:\n"
           f"A = {f['A']:.9f}, B = {f['B']:.9f}, C = {f['C']:.9f}\n"
           f"dt = {report['time_step_s']:.6f} s, validation N = {report['P6a']['validation_count']}\n\n"
           "P5b waveform audit:\n"
           f"  status = {fa['status']}\n"
           f"  candidate comparisons = {fa['candidate_pairs_scored']}\n"
           f"  near matching cross-partition pairs = {fa['near_shape_cross_partition_pairs']}\n"
           f"  large buckets sampled = {fa['large_buckets_sampled']}\n\n"
           "P6a conditional rollouts with 2 measured initial heights ONLY at start:\n"
           "  future acceleration is KNOWN, never forecast\n"
           "  future measured height NOT fed to the model\n"
           "  anchors fixed before evaluating the validation cohort\n"
           "  test/OOD response trajectories NOT accessed\n\n"
           "STATUS: no blind certification; no Euler/PIV/PKLSA/gravity closure.\n"
           "Optical or hydrodynamic wave-mode classification not inferred.\n")
        ax.text(0,.92,s,fontsize=10.2,fontfamily='monospace',va='top',transform=ax.transAxes,linespacing=1.55)
        pdf.savefig(fig);plt.close(fig)
        fig,ax=plt.subplots(figsize=(8.27,6.3))
        methods=[('rmse_arx_m','Frozen ARX(2)'),('rmse_persistence_m','Persistence'),('rmse_linear_extrap_m','Linear extrapolation')]
        for k,name in methods:
            lines=[r for r in summaryrows if abs(r['anchor_time_s']-1.5)<0.004]
            ax.plot([r['horizon_s'] for r in lines], [r[k]*1000 for r in lines], '-o',label=name)
        ax.set(xlabel='Forecast horizon [s]',ylabel='RMSE [mm]',title='Conditional free-run from fixed 1.5-s anchor')
        ax.legend();ax.grid(alpha=.25)
        fig.tight_layout();pdf.savefig(fig);plt.close(fig)
        firstval=next(iter(sorted({r['row_id_zero_based'] for r in trace})))
        data=[v for v in trace if v['row_id_zero_based']==firstval and abs(v['anchor_s']-1.5)<0.004]
        fig,ax=plt.subplots(figsize=(8.27,5))
        for k,name in [('measured_m','Experiment'),('arx_m','Frozen ARX(2)'),('persistence_m','Persistence')]:
            ax.plot([r['time_s'] for r in data],[r[k]*1000 for r in data],label=name)
        ax.set(xlabel='Time [s]',ylabel='Elevation [mm]',title=f'Predesignated validation trajectory {firstval}, anchor 1.5 s')
        ax.legend();ax.grid(alpha=.2)
        fig.tight_layout();pdf.savefig(fig);plt.close(fig)
        fig=plt.figure(figsize=(8.27,11.69));ax=fig.add_axes([.07,.07,.87,.85]);ax.axis('off')
        lines=['SCIENTIFIC GATES / LIMITS','',
               'P5b: morphology-based possible family overlap: REVIEW ONLY.',
               '      Publisher-defined family IDs absent; split remains NON-BLIND.',
               'P6a: development forecast, not a physically independent solver.',
               'P6b: persistence and linear extrapolation checked per anchor.',
               'P6c: per-trajectory eigenfrequency/damping not certified.',
               'P7: source-native PKLSA NOT RUN.',
               'P8: physical SST claims UNRESOLVED.','',
               'LOCKS:',
               ' - v0.3.0 source hashes of metadata, candidate split and pilot checked.',
               ' - ARX(2) coefficients loaded from prior TRAIN fit, not refitted.',
               ' - Two observed elevation samples define each forecast origin.',
               ' - After origin: previous model predictions ONLY.',
               ' - Acceleration is provided as known future EXOGENOUS input.',
               ' - Candidate split remains the unmodified v0.2.0 partition.',
               ' - TEST/OOD output signals are never used.',
               ' - DATASET.zip (49.9 GB) is never opened.','',
               'REQUIRED NEXT:',
               ' 1. Resolve waveform-family provenance, not just waveform similarity.',
               ' 2. Lock split/group ID without tuning on TEST/OOD outputs.',
               ' 3. Test free-run Euler/sloshing model with tank geometry.',
               ' 4. Independently generate PKLSA predictions before test reveal.','',
               'Sources:',
               ' Giulietti et al., robot-executed sloshing dataset,',
               ' Zenodo DOI: 10.5281/zenodo.20039757.',
               ' Ljung, System Identification: Theory for the User, 1999.']
        ax.text(0,1,'\n'.join(lines),va='top',fontsize=10.2,fontfamily='monospace',transform=ax.transAxes,linespacing=1.7)
        pdf.savefig(fig);plt.close(fig)


def write_csv(p:Path, rows:list,cols=None):
    if not rows and cols is None:return
    if cols is None:cols=list(rows[0])
    with p.open('w', newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore');w.writeheader();w.writerows(rows)


def run(root:Path, max_pairs=FAMILY_MAX_PAIRS, max_bucket=FAMILY_MAX_BUCKET):
    import numpy as np
    root=root.resolve()
    cfg=source_lock(root)
    labels=cfg['labels'];a=cfg['a'];y=cfg['y'];dt=cfg['dt'];beta=cfg['beta']
    # P5b: ONLY robot input acceleration (including holdout acceleration, never holdout elevations).
    family, examples=family_audit(a,labels,max_pairs,max_bucket)
    if family.get('nonfinite_input_count',0)>0:
        forecast={'status':'BLOCKED_NONFINITE_INPUT', 'no_test_peeking': True}
        summary=[];traces=[]
    else:
        valid=sorted(i for i,l in labels.items() if l=='STANDARD_VALIDATION')
        # Explicit exclusively validation output indexing. Never loops through test/OOD output.
        summary,traces=rollouts(a,y,dt,beta,valid)
        forecast={'status':'DEVELOPMENT_CONDITIONAL_FREE_RUN_FAMILY_REVIEW_OPEN',
                  'validation_count':len(valid),'seeds_per_anchor':2,
                  'known_future_input':'acceleration(t) provided; no forecasting of driving force',
                  'no_height_teacher_forcing_within_horizon':True,
                  'no_test_ood_response_access':True,
                  'frozen_arx':dict(zip(['A','B','C'],beta)),
                  'anchors_s':list(ANCHOR_S), 'horizons_s':list(HORIZONS_S),
                  'rows':summary,
                  'models_compared':['Frozen ARX(2)','persistence','linear extrapolation'],
                  'family_audit_dependency':'INDEPENDENT_DESCRIPTIVE_DEVELOPMENT_ONLY',
                  'interpretation':'Development prediction only; cannot claim Euler or independent PKLSA closure'}
    output=root/'outputs'/'f005_free_run_family_v0.4.1'
    output.mkdir(parents=True,exist_ok=True)
    report={'tool':'F005_FreeRun_Family_v0.4.1','created_utc':datetime.now(timezone.utc).isoformat(),
         'scientific_status':'DEVELOPMENT_NOT_BLIND_NOT_EULER_NOT_PKLSA',
         'source_provenance':{'v0.3_audit_sha256':hash_file(cfg['old_path']),
                              'pilot_split_metadata_sha256':cfg['source_hashes'],
                              'input_npy_sha256':hash_file(cfg['input_path']),
                              'output_npy_full_hash':'NOT_COMPUTED_SEALED_TEST_OOD_OUTPUT_BYTES',
                              'validation_output_subset_sha256':hashlib.sha256(np.asarray(y[sorted(i for i,l in labels.items() if l=='STANDARD_VALIDATION')],dtype=np.float64).tobytes()).hexdigest(),
                              'archive_files_modified':False,'large_archive_read':False},
         'time_step_s':dt,'candidate_partition_counts':cfg['counts'],
         'P5b':{'status':family['status'], 'morphology_audit':family,
                'independence_certification':'BLOCKED_NO_PUBLISHER_FAMILY_IDS_AND_NONEXHAUSTIVE_SCREEN'},
         'P6a':forecast,
         'P7':'NOT_RUN', 'P8':'UNRESOLVED'}
    (output/'v041_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    write_csv(output/'validation_free_run_metrics.csv',summary,
              ['anchor_time_s','horizon_s','validation_trajectories','rmse_arx_m','rmse_persistence_m','rmse_linear_extrap_m','rmse_best_baseline_m','arx_improvement_vs_best_baseline_percent','max_abs_predicted_height_m'])
    write_csv(output/'family_candidate_pairs_REVIEW.csv',examples,
              ['row_a','partition_a','row_b','partition_b','correlation','norm_rmse','shift'])
    write_csv(output/'fixed_validation_trace_sample.csv',traces,
              ['anchor_s','row_id_zero_based','time_s','measured_m','arx_m','persistence_m','linear_extrap_m'])
    note=['# F005 v0.4.1 - Free-run and independent waveform-family audit','',
          '**DEVELOPMENT / NON-BLIND. No physics/SST certification.**','',
          '## Gates',f"- P5b waveform-family audit: `{family['status']}`",
          f"- P6a conditional validation forecast: `{forecast['status']}`",
          '- TEST/OOD response time series **NOT ACCESSED**.','- P7 PKLSA NOT RUN; P8 physical UNRESOLVED.','',
          '## Important constraints',
          '- Frozen v0.3 ARX model, future forcing known, NO measured heights fed back within forecast horizon.',
          '- Anchors are predeclared at 0.004, 1.5, 2.8 seconds (quantized to dt).',
          '- Two measured values at the origin seed each conditional forecast.',
          '- Shape-matching is a candidate screening algorithm, NOT provenance-grounded family independence.',
          '- Family-screening remains non-exhaustive: development validation is allowed without claiming independence.',
          '- No sources modified, no 49.9GB archive accessed.','',
          '## Results', '',
          '| Anchor [s] | Horizon [s] | ARX RMSE [mm] | Persistence [mm] | Linear [mm] |',
          '|---:|---:|---:|---:|---:|']
    for r in summary:
        note.append(f"| {r['anchor_time_s']:.3f} | {r['horizon_s']:.3f} | {r['rmse_arx_m']*1e3:.5f} | {r['rmse_persistence_m']*1e3:.5f} | {r['rmse_linear_extrap_m']*1e3:.5f} |")
    note += ['','## Needed next','Source-defined family IDs and a group-disjoint split are prerequisites for a certified holdout.',
             'Do not promote this to a physical SST/PKLSA result.']
    (output/'V041_SUMMARY.md').write_text('\n'.join(note)+'\n',encoding='utf-8')
    if summary:
        try:make_pdf(output/'F005_FreeRun_Family_v0.4.1_DEVELOPMENT.pdf',report,traces,summary)
        except ImportError as exc:raise RuntimeError('PDF generation requires matplotlib: py -3 -m pip install matplotlib') from exc
    return report,output


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path.cwd())
    parser.add_argument('--max-family-pairs',type=int,default=FAMILY_MAX_PAIRS)
    parser.add_argument('--max-family-bucket',type=int,default=FAMILY_MAX_BUCKET)
    args=parser.parse_args()
    if args.max_family_pairs<1 or args.max_family_bucket<2:
        parser.error('Invalid limits')
    try:report,out=run(args.root,args.max_family_pairs,args.max_family_bucket)
    except Exception as exc:
        print('F005 v0.4.1 BLOCKED:',type(exc).__name__,str(exc),file=sys.stderr)
        return 2
    print(json.dumps({'P5b':report['P5b']['status'],'P6a':report['P6a']['status'],
        'no_test_ood_response_access':report['P6a'].get('no_test_ood_response_access',True),
        'results':str(out)},indent=2))
    return 0 if report['P6a']['status']=='DEVELOPMENT_CONDITIONAL_FREE_RUN_FAMILY_REVIEW_OPEN' else 3

if __name__=='__main__':sys.exit(main())
