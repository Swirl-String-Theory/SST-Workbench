#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, os, subprocess, sys
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
STAGES=[(64,384),(96,512),(128,768)]
DEFAULT_IDS=['L4a1','L6a4','L6n1','L7n2']


def _flatten(values):
    if values is None: return list(DEFAULT_IDS)
    out=[]
    for v in values:
        out.extend(x.strip() for x in str(v).split(',') if x.strip())
    return out


def _read(path):
    with path.open(newline='',encoding='utf-8') as f: return list(csv.DictReader(f))


def _rel(a,b):
    a=float(a); b=float(b); return abs(a-b)/max(abs(a),abs(b),1e-12)


def main():
    ap=argparse.ArgumentParser(description='v0.3.5 matched full-Hessian Fourier-cutoff convergence ladder')
    ap.add_argument('--ids','-Ids',nargs='*',default=None)
    ap.add_argument('--native-threads','-NativeThreads',type=int,default=16)
    ap.add_argument('--output','-Output',default=None)
    ap.add_argument('--max-stage','-MaxStage',type=int,choices=[64,96,128],default=128)
    ap.add_argument('--re-threshold',type=float,default=0.05)
    ap.add_argument('--gradient-threshold',type=float,default=0.15)
    args=ap.parse_args()
    ids=_flatten(args.ids)
    stamp=datetime.now().strftime('%Y%m%d_%H%M%S')
    outroot=Path(args.output) if args.output else ROOT/f'outputs_qm_spectral_ladder_{stamp}'
    outroot.mkdir(parents=True,exist_ok=True)
    stage_rows={}
    for cutoff,n in STAGES:
        if cutoff>args.max_stage: break
        stage=outroot/f'm{cutoff}_N{n}'
        cfg=ROOT/'configs'/f'qm_full_filtered_m{cutoff}.json'
        command=[sys.executable,'-m','sst_link_suite.qm_cli',
                 '--input',str(ROOT/'data'/'idealLinks.txt'),'--output',str(stage),'--config',str(cfg),
                 '--ids',*ids,'--require-native','--skip-native-build','--native-threads',str(args.native_threads)]
        print(f'\\n[SST] cutoff m<={cutoff}, N={n}',flush=True)
        env=os.environ.copy()
        env['PYTHONPATH']=str(ROOT/'src') + os.pathsep + env.get('PYTHONPATH','')
        rc=subprocess.run(command,cwd=ROOT,env=env).returncode
        if rc: return rc
        stage_rows[cutoff]={(r['link_id'],r['signs']):r for r in _read(stage/'sector_readiness.csv')}

    comparisons=[]
    ordered=sorted(stage_rows)
    for lo,hi in zip(ordered,ordered[1:]):
        keys=sorted(set(stage_rows[lo])&set(stage_rows[hi]))
        for key in keys:
            a=stage_rows[lo][key]; b=stage_rows[hi][key]
            re_rel=_rel(a['relative_equilibrium_score'],b['relative_equilibrium_score'])
            grad_rel=_rel(a['primary_gradient_norm'],b['primary_gradient_norm'])
            neg_equal=int(a['hessian_negative_modes'])==int(b['hessian_negative_modes'])
            rank_equal=(int(a['symplectic_rank']),int(a['symplectic_dimension']))==(int(b['symplectic_rank']),int(b['symplectic_dimension']))
            unstable_equal=int(a['unstable_linear_modes'])==int(b['unstable_linear_modes'])
            step_ok=str(a['step_convergence_pass']).lower()=='true' and str(b['step_convergence_pass']).lower()=='true'
            passed=(re_rel<=args.re_threshold and grad_rel<=args.gradient_threshold and neg_equal and rank_equal and unstable_equal and step_ok)
            comparisons.append({
                'link_id':key[0],'signs':key[1],'cutoff_from':lo,'cutoff_to':hi,
                'relative_equilibrium_relative_difference':re_rel,
                'primary_gradient_relative_difference':grad_rel,
                'negative_mode_count_agreement':neg_equal,'symplectic_rank_agreement':rank_equal,
                'unstable_mode_count_agreement':unstable_equal,'both_step_converged':step_ok,
                'cutoff_stability_pass':passed,
            })
    if comparisons:
        path=outroot/'spectral_cutoff_comparison.csv'
        with path.open('w',newline='',encoding='utf-8') as f:
            wr=csv.DictWriter(f,fieldnames=list(comparisons[0])); wr.writeheader(); wr.writerows(comparisons)
    final=[]
    for link_id in ids:
        rows=[r for r in comparisons if r['link_id']==link_id]
        final.append({
            'link_id':link_id,
            'comparison_rows':len(rows),
            'all_sector_cutoff_stability_pass': bool(rows) and all(r['cutoff_stability_pass'] for r in rows),
            'failed_rows':sum(not r['cutoff_stability_pass'] for r in rows),
            'status':'[RESEARCH TRACK NUMERICAL REGULARIZATION] Cutoff convergence is not a physical SST cutoff derivation.',
        })
    (outroot/'spectral_cutoff_ladder_summary.json').write_text(json.dumps({'ids':ids,'stages':ordered,'summary':final},indent=2),encoding='utf-8')
    print('\\n[SST] final cutoff-stability summary')
    for row in final: print(f"{row['link_id']:6s} pass={row['all_sector_cutoff_stability_pass']} failed_rows={row['failed_rows']}")
    print(f'[SST] output: {outroot}')
    return 0

if __name__=='__main__': raise SystemExit(main())
