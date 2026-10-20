#!/usr/bin/env python3
"""F005 v0.4.2 — exhaustive generated-candidate family screening and conditional path forecasts.

DEVELOPMENT ONLY. TEST/OOD experimental elevations are NEVER read; acceleration inputs
may be read for input-only source/family checks. No Euler or PKLSA claim.
Requires existing data/f005_free_run_family_v0.4.1.py (unmodified). See docs/SCIENCE_CONTRACT_v0.4.2.md.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import time

import numpy as np

VERSION = '0.4.2'
ANCHORS_S = (0.004, 1.5, 2.8)
HORIZONS_S = (0.1, 0.5, 1.0, 2.0, 3.0)
PAIR_SCREEN_SPEC = ((64, 0.05), (32, 0.1), (16, 0.20))
SHIFT_SAMPLES = (-4, -2, 0, 2, 4)
CORRELATION_MIN = 0.995
NORMALIZED_RMSE_MAX = 0.075
BOOTSTRAP_N = 400
BOOTSTRAP_SEED = 20261020
# v0.4.1 release's number of proposed pairs for the currently registered input set.
# Only lock against a matching v0.4.1 report, do NOT claim all-pairs exhaustiveness.


def load_prior_module(root: Path):
    fp = root/'data'/'f005_free_run_family_v0.4.1.py'
    if not fp.is_file():
        raise FileNotFoundError(f'Install v0.4.1 source first (missing {fp})')
    spec=importlib.util.spec_from_file_location('f005_locked_v041',fp)
    mod=importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    if mod.VERSION != '0.4.1':
        raise RuntimeError('Expected exactly v0.4.1 dependency')
    return mod


def verify_previous(root:Path,prior:dict,cfg:dict,engine):
    old=root/'outputs'/'f005_free_run_family_v0.4.1'/'v041_report.json'
    if not old.is_file():
        raise FileNotFoundError('Missing source v041_report.json: '+str(old))
    if prior.get('tool') != 'F005_FreeRun_Family_v0.4.1':
        raise ValueError('Wrong v0.4.1 report')
    if prior['P5b']['morphology_audit']['status']!='REVIEW_BOUNDED_SCREEN_NOT_FAMILY_CERTIFIED':
        raise ValueError('Unexpected P5b prior status')
    if prior['P6a']['status']!='DEVELOPMENT_CONDITIONAL_FREE_RUN_FAMILY_REVIEW_OPEN':
        raise ValueError('Unexpected P6a prior status')
    if prior['P6a']['no_test_ood_response_access'] is not True:
        raise ValueError('Previous stage accessed sealed output')
    if prior['source_provenance']['input_npy_sha256']!=engine.hash_file(cfg['input_path']):
        raise ValueError('Input NPY content changed since v0.4.1')
    validation=sorted(i for i,k in cfg['labels'].items() if k=='STANDARD_VALIDATION')
    validation_sha=hashlib.sha256(np.asarray(cfg['y'][validation],dtype=np.float64).tobytes()).hexdigest()
    if prior['source_provenance']['validation_output_subset_sha256']!=validation_sha:
        raise ValueError('Validation outputs changed since v0.4.1')
    if prior['source_provenance']['v0.3_audit_sha256']!=engine.hash_file(cfg['old_path']):
        raise ValueError('Previous v0.3 audit lock mismatch')
    if prior['source_provenance']['pilot_split_metadata_sha256']!=cfg['source_hashes']:
        raise ValueError('Previous pilot/split/metadata lock mismatch')
    fixed=[prior['P6a']['frozen_arx'][k] for k in ('A','B','C')]
    if not np.array_equal(np.asarray(fixed,np.float64),np.asarray(cfg['beta'],np.float64)):
        raise ValueError('Frozen v0.3 model has changed')
    if not math.isclose(prior['time_step_s'],cfg['dt'],rel_tol=1e-11):
        raise ValueError('Timebase changed')
    if prior['candidate_partition_counts']!=cfg['counts']:
        raise ValueError('Split changed since v0.4.1')
    return old


def generate_candidates(acceleration,labels):
    """Reconstruct the WHOLE v0.4.1 proposed set, without its scoring cap.

    Uses exactly the published 3 input-only fingerprints + deterministic neighbours.
    This is an exhaustive examination *of this generator's candidate set*, not all
    possible 9,822 choose 2 waveform pairs and not source-provenance family IDs.
    """
    from bisect import bisect_left
    buckets=[defaultdict(list) for _ in PAIR_SCREEN_SPEC]
    exact=defaultdict(lambda:defaultdict(list))
    invalid=[]; zeros=[]
    for i in sorted(labels):
        x=np.asarray(acceleration[i],dtype=np.float64)
        if not np.isfinite(x).all():
            invalid.append(i)
            continue
        if float(np.max(abs(x)))<1e-12:zeros.append(i)
        exact[hashlib.sha256(x.tobytes()).hexdigest()][labels[i]].append(i)
        for bucket,(bins,step) in zip(buckets,PAIR_SCREEN_SPEC):
            # The fingerprint is intentionally the SAME as v0.4.1.
            v=np.asarray([p.mean() for p in np.array_split(x/max(1e-12,float(np.max(abs(x)))),bins)])
            sig=hashlib.sha256(np.rint(v/step).astype(np.int16).tobytes()).hexdigest()
            bucket[sig].append(i)
    if invalid:raise ValueError('Nonfinite input rows: '+repr(invalid[:15]))
    exact_count=0
    for grouped in exact.values():
        ps=list(sorted(grouped.items()))
        for i in range(len(ps)):
            for j in range(i+1,len(ps)):
                exact_count+=len(ps[i][1])*len(ps[j][1])
    # v0.4.1 candidate population, with no 15,000 cap.
    proposed=set(); dense=0; largest=0
    for bucket in buckets:
        for _,entries in sorted(bucket.items()):
            seq=sorted(set(entries))
            if len(seq)<=1:continue
            largest=max(largest,len(seq))
            if len(seq)>140:dense+=1
            by_part={q:sorted(i for i in seq if labels[i]==q) for q in ('STANDARD_TRAIN','STANDARD_VALIDATION','STANDARD_TEST','OPTIMIZED_OOD')}
            for i in seq:
                partition=labels[i]
                same=by_part[partition]; idx=bisect_left(same,i)
                for j in same[idx-1:idx]+same[idx+1:idx+2]:
                    if j!=i:proposed.add((min(i,j),max(i,j)))
                for q,other in by_part.items():
                    if q==partition or not other:continue
                    idx=bisect_left(other,i)
                    others={other[0],other[-1],other[min(idx,len(other)-1)],other[(i*2654435761)%len(other)]}
                    for j in others:
                        if j!=i:proposed.add((min(i,j),max(i,j)))
    candidates=sorted(proposed)
    sha=hashlib.sha256()
    for i,j in candidates:
        sha.update(i.to_bytes(4,'little'));sha.update(j.to_bytes(4,'little'))
    return candidates,dict(rows_checked=len(labels),nonfinite_input_count=0,all_zero_input_count=len(zeros),
           exact_duplicate_cross_partition_pairs=exact_count,candidate_pairs_generated=len(candidates),
           largest_bucket_size=largest,large_buckets_over_140=dense,candidate_pair_sha256=sha.hexdigest(),
           fingerprint_spec=[f'{a} bins / {b}' for a,b in PAIR_SCREEN_SPEC])


def scored_shapes(x,y,shifts=SHIFT_SAMPLES):
    """Precisely v0.4.1 normalized shift-aware correlation/RMSE acceptance."""
    x=np.asarray(x,np.float64);y=np.asarray(y,np.float64)
    scale_x=float(np.max(abs(x)));scale_y=float(np.max(abs(y)))
    if scale_x<1e-12 or scale_y<1e-12:
        both=scale_x<1e-12 and scale_y<1e-12
        return (1. if both else 0.,0. if both else 2.,0)
    x=x/scale_x;y=y/scale_y
    best=(-2.,float('inf'),0)
    for s in shifts:
        xx=x[max(0,s):len(x)+min(0,s)]
        yy=y[max(0,-s):len(y)+min(0,-s)]
        if len(xx)<8:continue
        xc=xx-xx.mean();yc=yy-yy.mean()
        denom=float(np.linalg.norm(xc)*np.linalg.norm(yc))
        corr=float(xc.dot(yc)/denom) if denom>1e-12 else (1. if np.allclose(xx,yy) else 0.)
        rmse=float(np.sqrt(np.mean((xx-yy)**2)))
        if corr>best[0] or (abs(corr-best[0])<1e-12 and rmse<best[1]):best=(corr,rmse,int(s))
    return best


def score_candidate_set(a, labels, candidates,prior_module,verbose=False):
    """All generated candidate pairs are scored, no caps; writes one row per near-match."""
    dsu=prior_module.DSU(len(labels))
    near_total=near_cross=0
    edges=[]
    t0=time.monotonic()
    for n,(i,j) in enumerate(candidates,1):
        corr,rmse,shift=scored_shapes(a[i],a[j])
        if corr>=CORRELATION_MIN and rmse<=NORMALIZED_RMSE_MAX:
            dsu.union(i,j);near_total+=1
            if labels[i]!=labels[j]:near_cross+=1
            edges.append(dict(row_a=i,partition_a=labels[i],row_b=j,partition_b=labels[j],
                        correlation=round(corr,8),norm_rmse=round(rmse,8),shift=shift,
                        cross_partition=int(labels[i]!=labels[j])))
        if verbose and n%10000==0:
            print(f'[P5c] scored {n}/{len(candidates)} candidate pairs in {time.monotonic()-t0:.1f}s',flush=True)
    comp=defaultdict(list)
    for i in sorted(labels):comp[dsu.find(i)].append(i)
    overlaps=[v for v in comp.values() if len({labels[z] for z in v})>1]
    bysize=sorted(overlaps,key=lambda x:(-len(x),x[0]))
    input_components=[]
    train_overlapping_validation=[]
    for v in comp.values():
        parts={labels[z] for z in v}
        r=min(v)
        for i in v:
            input_components.append({'row_id_zero_based':i,'partition':labels[i],
                'shape_component_min_row_id':r,'shape_component_size':len(v),
                'component_cross_partition':int(len(parts)>1),
                'has_train_match_path':int('STANDARD_TRAIN' in parts and labels[i]!='STANDARD_TRAIN')})
            if labels[i]=='STANDARD_VALIDATION' and 'STANDARD_TRAIN' in parts:
                train_overlapping_validation.append(i)
    stats=dict(status='REVIEW_GENERATED_CANDIDATES_ALL_SCORED_NOT_PROVENANCE_CERTIFIED',
       pairs_scored=len(candidates),candidate_pairs_unscored=0,near_shape_total_pairs=near_total,
       near_shape_cross_partition_pairs=near_cross,approximate_components_cross_partition=len(overlaps),
       largest_component_size=max((len(v) for v in comp.values()),default=1),
       validation_rows_with_candidate_train_match=len(train_overlapping_validation),
       component_examples=[{'size':len(v),'partition_counts':dict(Counter(labels[z] for z in v)),
                            'example_row_ids':v[:12]} for v in bysize[:25]],
       threshold={'correlation_min':CORRELATION_MIN,'normalized_rmse_max':NORMALIZED_RMSE_MAX,
                  'shifts_samples':list(SHIFT_SAMPLES)},
       interpretation='All generated candidate pairs scored; candidate generator itself is not all-pairs and source family IDs are absent.')
    return stats,edges,sorted(input_components,key=lambda x:x['row_id_zero_based']),sorted(train_overlapping_validation)


def oscillator_unforced(y0,ym1,dt,steps,gamma,fd):
    """Homogeneous damped oscillator, params derived from v0.3 TRAIN-only ARX poles.

    Independent *forcing assumption*, NOT independently fitted oscillator parameters.
    This is a transparent unforced control and not an Euler solution.
    """
    v0=(y0-ym1)/dt
    w=2*np.pi*fd
    t=steps*dt
    return np.exp(-gamma*t)*(y0*np.cos(w*t)+(v0+gamma*y0)*np.sin(w*t)/w)


def oscillator_parameters(beta,dt):
    roots=np.roots([1.,-beta[0],-beta[1]])
    if not np.iscomplex(roots[0]) and abs(roots[0].imag)<1e-12:
        raise ValueError('Oscillator requires oscillatory stable poles')
    root=roots[np.argmax(roots.imag)]
    gamma=-math.log(abs(root))/dt
    fd=abs(np.angle(root))/(2*np.pi*dt)
    if gamma<=0 or fd<=0:raise ValueError('Unstable/invalid poles')
    return gamma,fd


def segment_metrics(reference,prediction,dt,frequency_hz):
    """Narrow-band phase/amplitude diagnostics across ROWS, not a mode fit."""
    n,s=reference.shape
    if s*dt<max(0.5,1/frequency_hz):return {'status':'INSUFFICIENT_WINDOW'}
    t=np.arange(s)*dt
    wave=np.exp(-2j*np.pi*frequency_hz*t)
    # Subtract row means. Avoid ill-defined phase on near-zero measured amplitude.
    ref=np.asarray(reference)-np.asarray(reference).mean(axis=1,keepdims=True)
    pr=np.asarray(prediction)-np.asarray(prediction).mean(axis=1,keepdims=True)
    rr=(ref@wave)*2/s;pp=(pr@wave)*2/s
    good=np.abs(rr)>=0.00025  # 0.25 mm measured amplitude threshold, predeclared
    count=int(good.sum())
    if not count:return {'status':'LOW_SIGNAL','qualifying_trajectories':0}
    phase=np.angle(pp[good]*np.conjugate(rr[good]))
    ratio=np.abs(pp[good])/np.abs(rr[good])
    return {'status':'DIAGNOSTIC_ONLY','qualifying_trajectories':count,
            'qualifying_fraction':count/n,'median_abs_phase_error_rad':float(np.median(abs(phase))),
            'median_amplitude_ratio':float(np.median(ratio)),'reference_frequency_hz':frequency_hz,
            'method':'fixed-frequency complex projection after mean removal; 0.25-mm threshold'}


def bootstrap_delta(err_sq_a,err_sq_b,nrep=BOOTSTRAP_N,seed=BOOTSTRAP_SEED):
    """Bootstrap across trajectories (not family-independent). CI on RMSE difference."""
    rng=np.random.default_rng(seed)
    n=len(err_sq_a)
    draws=rng.integers(0,n,size=(nrep,n),endpoint=False)
    deltas=np.sqrt(err_sq_b[draws].mean(axis=1))-np.sqrt(err_sq_a[draws].mean(axis=1))
    return [float(x) for x in np.quantile(deltas,[0.025,0.975])]


def qualified_rollouts(a, output, ids, dt, beta, anchors_s=ANCHORS_S,horizons_s=HORIZONS_S):
    """Input at ids and output at ids ONLY. Measured response used at anchors and scoring;
    forbidden within forward recursion. Score endpoint AND full path, including zero and
    unforced damped-oscillator controls. No TEST/OOD output indexing.
    """
    if not ids:raise ValueError('No validation trajectories')
    x=np.asarray(a[ids],np.float64)
    y=np.asarray(output[ids],np.float64)*.001  # source OUTPUT_TRAIN is mm
    if x.shape!=y.shape or not(np.isfinite(x).all() and np.isfinite(y).all()):
        raise ValueError('Invalid validation values')
    N,T=y.shape
    gamma,fd=oscillator_parameters(beta,dt)
    results=[];diagnostics=[];trace=[]
    for anchor in anchors_s:
        n0=max(1,int(round(anchor/dt)))
        hsteps=[int(round(h/dt)) for h in horizons_s]
        if n0+max(hsteps)>=T:raise ValueError('Invalid horizon/anchor')
        maxsteps=max(hsteps)
        prev=y[:,n0-1].copy();cur=y[:,n0].copy()
        init=cur.copy();vel=(cur-prev).copy()
        # All predictions generated ONCE to maximum horizon using own prior heights only.
        pred=np.empty((N,maxsteps),np.float64)
        for step in range(1,maxsteps+1):
            nxt=beta[0]*cur+beta[1]*prev+beta[2]*dt*dt*x[:,n0+step-1]
            pred[:,step-1]=nxt
            prev,cur=cur,nxt
        steps=np.arange(1,maxsteps+1,dtype=np.float64)
        actual=y[:,n0+1:n0+maxsteps+1]
        controls={
            'arx':pred,
            'persistence':np.broadcast_to(init[:,None],(N,maxsteps)),
            'linear_extrapolation':init[:,None]+steps[None,:]*vel[:,None],
            'zero_response':np.zeros((N,maxsteps),np.float64),
            'unforced_damped_oscillator':oscillator_unforced(init[:,None],(init-vel)[:,None],dt,steps[None,:],gamma,fd)
        }
        errs={k:(v-actual)**2 for k,v in controls.items()}
        for horizon,k in zip(horizons_s,hsteps):
            row={'anchor_time_s':round(n0*dt,6),'horizon_s':round(k*dt,6),
                 'trajectory_count':N,'time_points_in_path':k}
            per_traj={}
            for label,arr in errs.items():
                point=arr[:,k-1];path=arr[:,:k].mean(axis=1)
                row['endpoint_rmse_'+label+'_mm']=float(1000*np.sqrt(point.mean()))
                row['path_rmse_'+label+'_mm']=float(1000*np.sqrt(path.mean()))
                per_traj[label]=(point,path)
            other=['persistence','linear_extrapolation','zero_response','unforced_damped_oscillator']
            for score in ('endpoint','path'):
                best=min(other,key=lambda name:row[f'{score}_rmse_{name}_mm'])
                base=row[f'{score}_rmse_{best}_mm'];predrmse=row[f'{score}_rmse_arx_mm']
                row[f'{score}_best_baseline_name']=best
                row[f'{score}_best_baseline_rmse_mm']=base
                row[f'{score}_improvement_percent']=float(100*(1-predrmse/base)) if base else None
                # Sign is baseline minus ARX: + means ARX lower error. Descriptive non-grouped CI.
                ci=bootstrap_delta(per_traj['arx'][0 if score=='endpoint' else 1],
                                   per_traj['zero_response'][0 if score=='endpoint' else 1],
                                   seed=BOOTSTRAP_SEED+n0+k+(1 if score=='path' else 0))
                row[f'{score}_zero_minus_arx_ci95_low_mm']=1000*ci[0]
                row[f'{score}_zero_minus_arx_ci95_high_mm']=1000*ci[1]
            # diagnostic: only if enough cycles & measured amplitude is reliable.
            d=segment_metrics(actual[:,:k],pred[:,:k],dt,fd)
            diagnostics.append({'anchor_time_s':row['anchor_time_s'],
                               'horizon_s':row['horizon_s'],**d})
            results.append(row)
        # Preassigned first 3 validation rows, decimated for small CSV; does not affect forecasts.
        for j in range(min(3,N)):
            for step in range(0,maxsteps+1,20):
                if step==0:
                    trace.append(dict(anchor_s=round(n0*dt,6),row_id_zero_based=ids[j],time_s=round(n0*dt,6),
                        measured_mm=float(y[j,n0]*1000),arx_mm=float(init[j]*1000),
                        zero_mm=0.,oscillator_mm=float(init[j]*1000)))
                else:
                    ix=step-1
                    trace.append(dict(anchor_s=round(n0*dt,6),row_id_zero_based=ids[j],time_s=round((n0+step)*dt,6),
                        measured_mm=float(actual[j,ix]*1000),arx_mm=float(pred[j,ix]*1000),
                        zero_mm=0.,oscillator_mm=float(controls['unforced_damped_oscillator'][j,ix]*1000)))
    return results,diagnostics,trace,{'gamma_s_inv':gamma,'damped_frequency_hz':fd,
        'origin':'v0.3 ARX poles (TRAIN-only); NOT independent fitted oscillator'}


def write_csv(p,rows,columns=None):
    if columns is None:
        if not rows:raise ValueError('Missing CSV columns')
        columns=list(rows[0])
    with open(p,'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=columns,extrasaction='ignore');w.writeheader();w.writerows(rows)


def plot_pdf(dst,report,metrics,diag,traces):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    fam=report['P5c'];lock=report['P6d']
    with PdfPages(dst) as pdf:
        fig,ax=plt.subplots(figsize=(8.27,11.69));ax.axis('off')
        summary=(
            'F005 v0.4.2 | DEVELOPMENT QUALIFICATION\n'
            'NOT BLIND / NOT EULER / NOT PKLSA\n\n'
            'INPUT-ONLY FAMILY SCREEN\n'
            f"Generated pairs: {fam['candidate_pairs_generated']:,}\n"
            f"Scored pairs: {fam['pairs_scored']:,}\n"
            f"Cross-partition near-shape matches: {fam['near_shape_cross_partition_pairs']:,}\n"
            f"Components crossing partitions: {fam['approximate_components_cross_partition']:,}\n"
            'All GENERATED pairs scored; generator is not exhaustive.\n'
            'Publisher family identifiers unavailable => no blind certification.\n\n'
            'CONDITIONAL MULTISTEP FORECAST\n'
            f"Validation trajectories: {lock['validation_count']}\n"
            f"Sampling: {report['dt_s']:.6f} s\n"
            'Anchors: 0.004 / 1.5 / 2.8 s\n'
            'Horizon: 0.1 / 0.5 / 1 / 2 / 3 s\n'
            'Model: frozen TRAIN-only ARX(2), future forcing known.\n'
            'Baselines: persistence, linear, zero, unforced oscillator.\n'
            'Scores: endpoint + full path RMSE, mm.\n'
            'No measured elevation fed back after each origin.\n'
            'No TEST/OOD elevation read or scores disclosed.\n\n'
            'SCIENTIFIC GATE LIMITS\n'
            'P5c: REVIEW (no publisher family IDs)\n'
            'P6d: DEVELOPMENT VALIDATION ONLY\n'
            'P6e: baselines evaluated; no model refit\n'
            'P6f: narrowband phase diagnostic, no mode certification\n'
            'P6g: GROUP-SPLIT BLOCKED, holdouts remain sealed\n'
            'P7 PKLSA: NOT RUN; P8 PHYSICAL: UNRESOLVED.\n'
        )
        ax.text(.03,.97,summary,fontfamily='monospace',fontsize=10.1,va='top',linespacing=1.43,transform=ax.transAxes)
        fig.tight_layout();pdf.savefig(fig);plt.close(fig)
        for score in ('path','endpoint'):
            fig,ax=plt.subplots(figsize=(8.27,5.0))
            rows=sorted((r for r in metrics if abs(r['anchor_time_s']-1.5)<0.005),key=lambda r:r['horizon_s'])
            x=[r['horizon_s'] for r in rows]
            for label,name in [('arx','Frozen ARX(2)'),('zero_response','Zero equilibrium'),
                               ('persistence','Persistence'),('unforced_damped_oscillator','Unforced oscillator')]:
                ax.plot(x,[r[f'{score}_rmse_{label}_mm'] for r in rows],'-o',label=name)
            ax.set(xlabel='Horizon [s]',ylabel='RMSE [mm]',title=f'{score.title()} error, anchor 1.5 s, validation only')
            ax.grid(alpha=.2);ax.legend(loc='best',fontsize=8);fig.tight_layout()
            pdf.savefig(fig);plt.close(fig)
        fig,ax=plt.subplots(figsize=(8.27,5))
        one=sorted({t['row_id_zero_based'] for t in traces})[0]
        rows=[r for r in traces if r['row_id_zero_based']==one and abs(r['anchor_s']-1.5)<0.005]
        for key,name in [('measured_mm','Experimental elevation'),('arx_mm','Frozen ARX(2)'),
                         ('oscillator_mm','Unforced oscillator'),('zero_mm','Zero equilibrium')]:
            ax.plot([r['time_s'] for r in rows],[r[key] for r in rows],label=name)
        ax.set(xlabel='Time [s]',ylabel='Elevation [mm]',title=f'Fixed validation trajectory {one}, anchor 1.5 s')
        ax.grid(alpha=.2);ax.legend(fontsize=8);fig.tight_layout();pdf.savefig(fig);plt.close(fig)
        fig,ax=plt.subplots(figsize=(8.27,11.69));ax.axis('off')
        foot=(
            'LIMITATIONS / PROVENANCE\n\n'
            'A. Family candidates generated by 3 quantized input fingerprints.\n'
            '   Exhaustive scoring of candidates does not imply all-pairs search.\n'
            '   Near-shape != same publisher source-family.\n\n'
            'B. Sealed responses: STANDARD_TEST / OPTIMIZED_OOD never indexed.\n'
            '   Inputs for those partitions may be inspected for overlap only.\n'
            '   The existing candidate split has not been certified blind.\n\n'
            'C. Conditional rollout uses two elevations at each forecast origin,\n'
            '   then recursive predictions, plus future acceleration known.\n'
            '   This is NOT prediction of unknown future forcing.\n\n'
            'D. Unforced oscillator uses TRAIN-only ARX pole estimates.\n'
            '   It is NOT independent parameter identification / Euler dynamics.\n'
            '   Bootstrapped CIs treat trajectories as independent and hence\n'
            '   are descriptive until family independence is resolved.\n\n'
            'E. Phase/amplitude: demodulation at an ARX-selected frequency.\n'
            '   No vortex Kelvin mode or free-surface eigenmode certification.\n\n'
            'F. DATASET.zip (49.9 GB) never read. Sources left untouched.\n\n'
            'References:\n'
            ' Giulietti et al., Robot-executed sloshing dataset (2026),\n'
            ' https://doi.org/10.5281/zenodo.20039757\n'
            ' Ljung, System Identification: Theory for the User, 1999.\n'
        )
        ax.text(.03,.97,foot,fontfamily='monospace',fontsize=9.3,va='top',linespacing=1.45,transform=ax.transAxes)
        fig.tight_layout();pdf.savefig(fig);plt.close(fig)


def run(root:Path, *, verbose=False, require_previous=True):
    root=root.resolve()
    prior_mod=load_prior_module(root)
    cfg=prior_mod.source_lock(root)
    prev_path=root/'outputs'/'f005_free_run_family_v0.4.1'/'v041_report.json'
    if require_previous:
        prev=json.loads(prev_path.read_text(encoding='utf-8'))
        verify_previous(root,prev,cfg,prior_mod)
    else:prev=None
    labels=cfg['labels'];a=cfg['a'];y=cfg['y'];dt=cfg['dt'];beta=cfg['beta']
    out=root/'outputs'/'f005_qualification_v0.4.2'
    out.mkdir(parents=True,exist_ok=True)
    t0=time.monotonic()
    candidates,meta=generate_candidates(a,labels)
    if prev is not None and meta['candidate_pairs_generated']!=prev['P5b']['morphology_audit']['candidate_pairs_proposed']:
        raise ValueError('v041 fingerprint candidate generator disagrees with locked report')
    family,edges,components,overlap_val=score_candidate_set(a,labels,candidates,prior_mod,verbose)
    if len(candidates)!=family['pairs_scored']:
        raise RuntimeError('Missing scored family candidates')
    valid=sorted(i for i,p in labels.items() if p=='STANDARD_VALIDATION')
    metric,phase,trace,osc=qualified_rollouts(a,y,valid,dt,beta)
    screen_negative=sorted(set(valid)-set(overlap_val))
    sensitivity=[]
    if screen_negative:
        sensitivity,_,_,_=qualified_rollouts(a,y,screen_negative,dt,beta)
    scorecard={
        'endpoint_better_than_best_baseline':sum(r['endpoint_improvement_percent']>0 for r in metric),
        'path_better_than_best_baseline':sum(r['path_improvement_percent']>0 for r in metric),
        'path_better_than_zero_response':sum(r['path_rmse_arx_mm']<r['path_rmse_zero_response_mm'] for r in metric),
        'path_zero_minus_arx_ci_strictly_positive':sum(r['path_zero_minus_arx_ci95_low_mm']>0 for r in metric),
        'total_predeclared_anchor_horizon_conditions':len(metric),
        'qualification_label':'DEVELOPMENT_SCORECARD_NOT_PHYSICAL_CERTIFICATION',
    }
    report={
        'tool':'F005_Qualification_v0.4.2', 'created_utc':datetime.now(timezone.utc).isoformat(),
        'scientific_status':'DEVELOPMENT_ONLY_NOT_BLIND_NOT_EULER_NOT_PKLSA',
        'source_locks':{
            'v03_audit_sha256':prior_mod.hash_file(cfg['old_path']),
            'v041_report_sha256':prior_mod.hash_file(prev_path) if require_previous else 'SYNTHETIC_TEST_NO_PREV',
            'v041_source_sha256':prior_mod.hash_file(root/'data'/'f005_free_run_family_v0.4.1.py'),
            'pilot_split_metadata_sha256':cfg['source_hashes'],
            'input_npy_sha256':prior_mod.hash_file(cfg['input_path']),
            'sealed_output_full_sha256':'NOT_COMPUTED',
            'large_archive_read':False,
            'sources_modified':False,
        },
        'dt_s':dt,'candidate_partition_counts':cfg['counts'],
        'P5c':{**meta,**family,'publisher_defined_family_ids':'NOT_AVAILABLE',
                 'independence_certification':'BLOCKED_NO_SOURCE_FAMILY_IDENTIFIERS'},
        'P6d':{'status':'DEVELOPMENT_PATH_AND_ENDPOINT_MEASURED_NONBLIND',
               'validation_count':len(valid), 'seeds_per_anchor':2,
               'future_acceleration_known':True,'height_teacher_forcing_in_horizon':False,
               'test_ood_heights_accessed':False,'frozen_arx_A_B_C':list(beta),
               'anchors_s':list(ANCHORS_S),'horizons_s':list(HORIZONS_S),
               'rows':metric,'scorecard':scorecard,
               'bootstrap':{'method':'row bootstrap / not family independent',
               'iterations':BOOTSTRAP_N,'seed':BOOTSTRAP_SEED,'comparison':'zero response minus ARX'}},
        'P6e':{'status':'DEVELOPMENT_BASELINES_MEASURED',
               'models':['ARX(2)','persistence','linear extrapolation','zero equilibrium',
                         'unforced ARX-derived damped oscillator'],
               'oscillator_parameters':osc},
        'P6f':{'status':'EXPLORATORY_NARROWBAND_DIAGNOSTIC','rows':phase},
        'P6g':{'status':'BLOCKED_NO_PUBLISHER_GROUP_IDS_KEEP_SPLIT_UNCHANGED',
                'test_ood_response_sealed':True,
                'validation_input_screen_negative_count':len(screen_negative),
                'validation_input_candidate_connected_to_train_count':len(overlap_val),
                'input_screen_negative_sensitivity_metrics':sensitivity,
                'warning':'Screen-negative subgroup selected from INPUT ONLY; not a certified independent holdout.'},
        'P7':'NOT_RUN','P8':'UNRESOLVED',
        'runtime_wall_seconds':round(time.monotonic()-t0,3),
    }
    (out/'v042_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    write_csv(out/'family_candidate_matches_REVIEW.csv',edges,
              ['row_a','partition_a','row_b','partition_b','correlation','norm_rmse','shift','cross_partition'])
    write_csv(out/'validation_horizon_metrics.csv',metric)
    write_csv(out/'input_shape_components_REVIEW.csv',components)
    if sensitivity:
        write_csv(out/'input_screen_negative_validation_sensitivity.csv',sensitivity)
    else:
        write_csv(out/'input_screen_negative_validation_sensitivity.csv',[],columns=list(metric[0]))
    write_csv(out/'phase_amplitude_diagnostic.csv',phase)
    write_csv(out/'fixed_validation_trace_sample.csv',trace)
    summary=[
        '# F005 v0.4.2 - predictor and family qualification','',
        '**DEVELOPMENT / NON-BLIND / NOT EULER / NOT PKLSA**','',
        '## Family candidate audit',
        f"- Generator candidates: **{len(candidates):,}**; scored: **{family['pairs_scored']:,}**; unscored: **0**.",
        f"- Strong cross-partition input-shape pairs: **{family['near_shape_cross_partition_pairs']:,}**.",
        f"- Approximate cross-partition graph components: **{family['approximate_components_cross_partition']:,}**.",
        f"- VALIDATION with input candidate-linked path to TRAIN: **{len(overlap_val)} / {len(valid)}**.",
        f"- Screen-negative VALIDATION: **{len(screen_negative)} / {len(valid)}** (NOT independent-certified).",
        '- All generated candidates scored does NOT imply exhaustive all-pairs search.',
        '- Source-defined family identifiers absent; split NOT independent-certified.','',
        '## Conditional path predictions',
        '- Future forcing known. Two measured initial heights at each origin; NO further height feedback.',
        '- TEST/OOD elevations never read. v0.3 frozen ARX coefficients unchanged.',
        '- RMSE is in mm. Both endpoint and whole-path RMSE are reported.','',
        '| Anchor s | Horizon s | ARX path RMSE mm | Zero path RMSE mm | Best baseline | ARX change % |',
        '|---:|---:|---:|---:|---|---:|',
    ]
    for r in metric:
        summary.append(f"| {r['anchor_time_s']:.3f} | {r['horizon_s']:.3f} | {r['path_rmse_arx_mm']:.5f} | {r['path_rmse_zero_response_mm']:.5f} | {r['path_best_baseline_name']} | {r['path_improvement_percent']:.2f} |")
    summary+=['','## Input-screen-negative validation sensitivity',
              '- Screen-negative means no path from VALIDATION to TRAIN in the **generated candidate** graph.',
              '- Selection uses inputs only; the resulting subgroup is NOT source-family certified.',
              f'- Eligible trajectories: {len(screen_negative)}.',
              '- See input_screen_negative_validation_sensitivity.csv for path/endpoint errors.','',
              '## Qualification status','- P5c: REVIEW (input morphology only).',
              '- P6d/e: DEVELOPMENT RESULTS, no blind certification.',
              '- P6f: narrowband exploratory phase/amplitude only.',
              '- P6g: BLOCKED (publisher family provenance).','- P7 PKLSA NOT RUN; P8 PHYSICAL UNRESOLVED.',
              '- Zero/oscillator baselines added; oscillator parameters are ARX-derived.',
        f"- Path wins vs best baseline: {scorecard['path_better_than_best_baseline']}/{scorecard['total_predeclared_anchor_horizon_conditions']}.",
        f"- Endpoint wins vs best baseline: {scorecard['endpoint_better_than_best_baseline']}/{scorecard['total_predeclared_anchor_horizon_conditions']}.",
              '- Large 50GB DATASET.zip was not touched.']
    (out/'V042_SUMMARY.md').write_text('\n'.join(summary)+'\n',encoding='utf-8')
    plot_pdf(out/'F005_v0.4.2_QUALIFICATION_DEVELOPMENT.pdf',report,metric,phase,trace)
    return report,out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path.cwd())
    p.add_argument('--verbose',action='store_true')
    args=p.parse_args()
    try:r,o=run(args.root,verbose=args.verbose)
    except Exception as e:
        print('F005 v0.4.2 BLOCKED:',type(e).__name__,e,file=sys.stderr)
        return 2
    print(json.dumps({'P5c':r['P5c']['status'],'candidate_pairs_scored':r['P5c']['pairs_scored'],
      'P6d':r['P6d']['status'],'P6g':r['P6g']['status'],
      'output':str(o)},indent=2))
    return 0

if __name__=='__main__':sys.exit(main())
