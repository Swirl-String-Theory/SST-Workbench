"""Target-free numerical benchmark for S37C remap-kernel closure.

This is a numerical-method diagnostic only.  It uses an analytic T(2,3) curve
without any SST constant target and compares the historical polygonal-linear
remapper with the v0.3.3 periodic-cubic remapper under identical RK4 plans.
"""
from __future__ import annotations
import argparse, json, time
from pathlib import Path
import numpy as np
from .operator_split_cert import run_resolution, classify_resolution_ladder


def analytic_trefoil(n=512, R=2.0, a=.6, b=.4):
    t=np.linspace(0.0,2*np.pi,int(n),endpoint=False)
    return np.c_[(R+a*np.cos(3*t))*np.cos(2*t),
                 (R+a*np.cos(3*t))*np.sin(2*t),
                 b*np.sin(3*t)]


def benchmark(smoke=False):
    cfg={
        'gamma':1.0,'core_fraction':.08,'require_native':False,
        'dt_factor':.025,'max_steps':250000,'store_samples':48,
        'contact_skip':3,'min_gap_over_ds':.85,'cyclic_stride':4,
        'high_k_cut_fraction':.33,'pod_modes':3,
        'score_shape_scale':.13,'score_highk_scale':.1,
        'score_weights':{'rolling':.4,'shape':.3,'highk':.15,'pod':0.0,'contact':.1,'mesh':.05},
        'operator_split_resolution_ladder':[32,40,48],
        'operator_split_t_final':.3,
        'operator_split_samples':48,
        'operator_split_hard_ds_cv':.60,
        'operator_split_remap_intervals':[.15,.075,.0375],
        'operator_split_max_final_shape_distance':.035,
        'operator_split_max_score_rel_span':.12,
        'operator_split_max_auc_rel_span':.20,
        'operator_split_min_convergence_order':.5,
        'operator_split_min_resolution_levels_for_support':3,
        'operator_split_error_floor':1e-8,
        'operator_split_remap_oversample_factor':16,
        'operator_split_remap_min_oversample':1024,
    }
    if smoke:
        # Fast reproducibility check only; deliberately not the preregistered S37C certification ladder.
        cfg['operator_split_resolution_ladder']=[32,40,48]
        cfg['operator_split_t_final']=.12
        cfg['operator_split_remap_intervals']=[.06,.03,.015]
        cfg['operator_split_samples']=24
        cfg['store_samples']=24
    base=analytic_trefoil()
    out={'format':'SST-S37C-REMAP-KERNEL-BENCHMARK-1.1','target_free':True,'physics_verdict':'UNTESTED','certification_status':'DIAGNOSTIC_SMOKE_ONLY' if smoke else 'NUMERICAL_METHOD_BENCHMARK_NOT_PHYSICS_CERTIFICATION','smoke':bool(smoke),'kernels':{}}
    for kernel in ('legacy_linear','periodic_cubic'):
        cc=dict(cfg); cc['operator_split_remap_kernel']=kernel
        rows=[]; t0=time.perf_counter()
        for n in cc['operator_split_resolution_ladder']:
            rows.append(run_resolution(base,cc,n,cc['operator_split_t_final']))
        out['kernels'][kernel]={
            'seconds':time.perf_counter()-t0,
            'rows':rows,
            'classification':classify_resolution_ladder(rows,cc),
        }
    return out


def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument('--out',default='remap_kernel_benchmark_v0.3.3.json')
    ap.add_argument('--smoke',action='store_true',help='fast non-certifying pure-Python reproducibility smoke')
    ns=ap.parse_args(argv)
    result=benchmark(smoke=ns.smoke); Path(ns.out).write_text(json.dumps(result,indent=2),encoding='utf-8')
    compact={k:{'classification':v['classification'],'seconds':v['seconds'],
                'errors':[r['max_pairwise_remap_shape_distance'] for r in v['rows']]}
             for k,v in result['kernels'].items()}
    print(json.dumps(compact,indent=2))
    return 0

if __name__=='__main__': raise SystemExit(main())
