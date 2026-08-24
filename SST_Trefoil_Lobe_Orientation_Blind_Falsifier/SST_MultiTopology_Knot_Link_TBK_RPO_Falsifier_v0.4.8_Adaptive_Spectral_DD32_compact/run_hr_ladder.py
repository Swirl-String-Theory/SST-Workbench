from __future__ import annotations
import argparse, json, time
from pathlib import Path
from run_archive_campaign import all_entries, inventory
from sst_blind.multitopology import run_panel
from sst_blind.ladder import analyze_ladder, write_ladder_outputs

ROOT=Path(__file__).resolve().parent


def load_plan(path):
    p=Path(path)
    return json.loads(p.read_text(encoding='utf-8'))


def main():
    ap=argparse.ArgumentParser(description='SST v0.4.7 high-resolution DD32 convergence ladder')
    ap.add_argument('--plan',default='configs/hr_ladder/ladder_plan.json')
    ap.add_argument('--out-dir',required=True)
    ap.add_argument('--backend',default='sycl-dd32',choices=['sycl-dd32','sycl-fp32','sycl-fp64','openmp','cpu','python'])
    ap.add_argument('--shard-count',type=int,default=1); ap.add_argument('--shard-index',type=int,default=0)
    ap.add_argument('--start-rung',type=int,default=0); ap.add_argument('--stop-rung',type=int,default=5)
    ap.add_argument('--force-build',action='store_true'); ap.add_argument('--build-verbose',action='store_true')
    a=ap.parse_args()
    plan=load_plan(a.plan); out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    if a.shard_count<1 or not 0<=a.shard_index<a.shard_count: raise SystemExit('invalid shard parameters')
    all_e=all_entries(); selected=[e for i,e in enumerate(all_e) if i%a.shard_count==a.shard_index]
    inventory(all_e,out/'ARCHIVE_INVENTORY.csv')
    (out/'LADDER_PLAN_PREREGISTERED.json').write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
    (out/'SHARD_INFO.json').write_text(json.dumps({'shard_index':a.shard_index,'shard_count':a.shard_count,'selected':len(selected),'inventory_total':len(all_e)},indent=2)+'\n',encoding='utf-8')
    print(f"[SST-LADDER] v0.4.7 backend={a.backend} selected={len(selected)}/{len(all_e)} shard={a.shard_index}/{a.shard_count}",flush=True)
    payload={}; t0=time.time()
    for rd in plan['rungs']:
        i=int(rd['index'])
        if i<a.start_rung or i>a.stop_rung: continue
        ro=out/f"{i:02d}_{rd['name']}"
        cfg=ROOT/rd['config']
        print('',flush=True); print('='*76,flush=True)
        print(f"[SST-LADDER] RUNG {i}/5 {rd['name']}  N={rd['N']}  k=2..{rd['k_max']}  dynamics={rd['dynamics']}",flush=True)
        print(f"[SST-LADDER] eps convergence={rd['eps_convergence']} robustness={rd['eps_robustness']} reference={rd['reference_eps']}",flush=True)
        print('='*76,flush=True)
        final,results,mapping=run_panel(selected,cfg,ro,backend=a.backend,force_build=(a.force_build and i==a.start_rung),build_verbose=a.build_verbose)
        payload[rd['name']]={'final':final,'results':results,'mapping':mapping}
        print(f"[SST-LADDER] RUNG {i} DONE overall={final['overall']} runtime={final['runtime_s']:.1f}s",flush=True)
        # Once all six required rungs are available in this invocation/output tree, analyze.
        if i==5:
            # Reload prior rungs from disk when this is a resumed start-rung > 0 launch.
            for prior in plan['rungs']:
                name=prior['name']
                if name in payload: continue
                pro=out/f"{prior['index']:02d}_{name}"
                vf=pro/'final_verdict.json'; mf=pro/'unblind_manifest.json'; pre=pro/'pre_unblind'
                if not (vf.exists() and mf.exists() and pre.exists()): continue
                mapping=json.loads(mf.read_text(encoding='utf-8')); results={}
                for af in sorted(pre.glob('B*_analysis.json')):
                    results[af.stem.replace('_analysis','')]=json.loads(af.read_text(encoding='utf-8'))
                payload[name]={'final':json.loads(vf.read_text(encoding='utf-8')),'results':results,'mapping':mapping}
            if all(rd2['name'] in payload for rd2 in plan['rungs']):
                records=analyze_ladder(payload,plan); write_ladder_outputs(out,records,plan)
                print(f"[SST-LADDER] convergence synthesis written to {out}",flush=True)
            else:
                print('[SST-LADDER] synthesis deferred: not all six rung outputs are present.',flush=True)
    (out/'LADDER_RUNTIME.json').write_text(json.dumps({'runtime_s':time.time()-t0,'backend':a.backend,'start_rung':a.start_rung,'stop_rung':a.stop_rung},indent=2)+'\n',encoding='utf-8')
    return 0

if __name__=='__main__': raise SystemExit(main())
