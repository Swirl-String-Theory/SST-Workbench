from __future__ import annotations
import argparse, json, time, zipfile
from pathlib import Path
from run_archive_campaign import all_entries, inventory
from sst_blind.io import sha256_file
from sst_blind.multitopology import run_panel
from sst_blind.spectral_extension import load_v047_k16_baseline, load_rung_by_source, evaluate_triplet, write_extension_outputs

ROOT=Path(__file__).resolve().parent

def _latest_baseline():
    cand=[]
    # Current project root plus sibling version directories under the same workbench.
    for p in ROOT.glob('outputs_hr_ladder_dd32_*'):
        if p.is_dir() or p.suffix.lower()=='.zip': cand.append(p)
    for p in ROOT.parent.glob('*/outputs_hr_ladder_dd32_*'):
        if p.is_dir() or p.suffix.lower()=='.zip': cand.append(p)
    for p in ROOT.parent.glob('outputs_hr_ladder_dd32_*.zip'):
        if p.is_file(): cand.append(p)
    return max(cand,key=lambda p:p.stat().st_mtime) if cand else None

def _verify_baseline(baseline_data, entries_by_source, sources):
    bad=[]
    for src in sorted(sources):
        if src not in baseline_data:
            bad.append((src,'missing')); continue
        meta=baseline_data[src]['meta']; r=baseline_data[src]['result']
        if meta.get('sha256') and sha256_file(entries_by_source[src]['path'])!=meta['sha256']:
            bad.append((src,'input_sha256_mismatch'))
        if int((r.get('dominant_mode_diagnostics',{}) or {}).get('requested_k_max',-1))!=16:
            bad.append((src,'baseline_not_k16'))
        if abs(float(r.get('metrics',{}).get('jacobian_reference_eps',-1))-0.004)>1e-15:
            bad.append((src,'baseline_reference_eps_not_0.004'))
        nc=(r.get('meta',{}) or {}).get('normalized_component_counts')
        if nc and sum(map(int,nc))!=720:
            bad.append((src,'baseline_not_N720'))
    if bad:
        raise RuntimeError('Incompatible v0.4.7 baseline: '+repr(bad[:12])+(' ...' if len(bad)>12 else ''))

def _load_plan(path): return json.loads(Path(path).read_text(encoding='utf-8'))

def _load_existing_rung(folder):
    p=Path(folder)
    if (p/'unblind_manifest.json').exists() and (p/'pre_unblind').exists(): return load_rung_by_source(p)
    return None

def _write_active(out, stage, sources):
    p=Path(out)/f'{stage}_ACTIVE_SOURCES.json'
    data=sorted(sources)
    if p.exists():
        old=json.loads(p.read_text(encoding='utf-8'))
        if old!=data: raise RuntimeError(f'Refusing resume: active source set changed for {stage}')
    else: p.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')

def _run_stage(entries_by_source, active, cfg, ro, backend, force_build=False, build_verbose=False):
    selected=[entries_by_source[s] for s in sorted(active)]
    final,_,_=run_panel(selected,cfg,ro,backend=backend,force_build=force_build,build_verbose=build_verbose)
    return load_rung_by_source(ro), final

def _decision_for_source(src, data_by_k, ktrip, policy):
    return evaluate_triplet(ktrip,[data_by_k[k][src]['result'] for k in ktrip],policy)

def main():
    ap=argparse.ArgumentParser(description='SST v0.4.8 adaptive k_max spectral extension: 16 -> 24 -> 32 -> 48 -> 64 at N=720')
    ap.add_argument('--plan',default='configs/spectral_extension/spectral_extension_plan.json')
    ap.add_argument('--baseline',default=None,help='v0.4.7 HR-ladder output directory or zip. If omitted, latest local output is used; if none exists, k16 is recomputed.')
    ap.add_argument('--out-dir',required=True)
    ap.add_argument('--backend',default='sycl-dd32',choices=['sycl-dd32','sycl-fp32','sycl-fp64','openmp','cpu','python'])
    ap.add_argument('--force-build',action='store_true'); ap.add_argument('--build-verbose',action='store_true')
    ap.add_argument('--baseline-check-only',action='store_true')
    ap.add_argument('--shard-count',type=int,default=1); ap.add_argument('--shard-index',type=int,default=0)
    a=ap.parse_args(); plan=_load_plan(a.plan); policy=plan['policy']; out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    (out/'SPECTRAL_EXTENSION_PLAN_PREREGISTERED.json').write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
    entries=all_entries(); inventory(entries,out/'ARCHIVE_INVENTORY.csv'); bysrc={e['source']:e for e in entries}
    if a.shard_count<1 or not 0<=a.shard_index<a.shard_count: raise SystemExit('invalid shard parameters')
    selected_entries=[e for i,e in enumerate(entries) if i%a.shard_count==a.shard_index]
    all_sources={e['source'] for e in selected_entries}
    (out/'SHARD_INFO.json').write_text(json.dumps({'shard_index':a.shard_index,'shard_count':a.shard_count,'selected':len(all_sources),'inventory_total':len(entries)},indent=2)+'\n',encoding='utf-8')
    baseline=Path(a.baseline) if a.baseline else _latest_baseline()
    data={}; t0=time.time()
    if baseline:
        print(f'[SST-SPECTRAL] importing k16 baseline from {baseline}',flush=True)
        data[16]=load_v047_k16_baseline(baseline)
        missing=all_sources-set(data[16])
        if missing: raise RuntimeError(f'baseline missing {len(missing)} selected archive sources')
        _verify_baseline(data[16],bysrc,all_sources)
        (out/'BASELINE_CHECK.json').write_text(json.dumps({'ok':True,'baseline':str(baseline.resolve()),'selected_sources':len(all_sources),'N':720,'k_max':16,'reference_eps':0.004},indent=2)+'\n',encoding='utf-8')
        bs=out/'BASELINE_SOURCE.txt'
        resolved=str(baseline.resolve())
        if bs.exists():
            old=bs.read_text(encoding='utf-8').strip()
            if old and old!=resolved:
                raise RuntimeError(f'Refusing resume: baseline changed from {old} to {resolved}')
        else:
            bs.write_text(resolved+'\n',encoding='utf-8')
    else:
        if a.baseline_check_only:
            raise SystemExit('No v0.4.7 baseline found to check. Supply --baseline <output_dir_or_zip>.')
        print('[SST-SPECTRAL] no v0.4.7 baseline found; recomputing N720/K16 S0.',flush=True)
        ro=out/'00_S0_N720_K16_BASELINE'; _write_active(out,'S0_K16',all_sources)
        existing=_load_existing_rung(ro)
        if existing is None: existing,_=_run_stage(bysrc,all_sources,ROOT/plan['baseline_config'],ro,a.backend,a.force_build,a.build_verbose)
        data[16]=existing
    if a.baseline_check_only:
        print(json.dumps({'baseline_ok':True,'selected_sources':len(all_sources),'baseline':str(baseline)},indent=2),flush=True)
        return 0
    active=set(all_sources)
    stage_specs=[(24,'01_S1_N720_K24','config'),(32,'02_S2_N720_K32','config'),(48,'03_S3_N720_K48','config'),(64,'04_S4_N720_K64','config')]
    decisions={}; stop_at={}; growth_by_source={s:{16:float(data[16][s]['result']['metrics']['normalized_growth'])} for s in all_sources}
    for k,dirname,_ in stage_specs:
        if not active: break
        spec=next(x for x in plan['rungs'] if int(x['k_max'])==k)
        ro=out/dirname; _write_active(out,f'K{k}',active)
        print('',flush=True); print('='*78,flush=True)
        print(f'[SST-SPECTRAL] k_max={k} active={len(active)}/{len(all_sources)} selected N=720 linear-only',flush=True)
        print('='*78,flush=True)
        existing=_load_existing_rung(ro)
        if existing is None:
            existing,final=_run_stage(bysrc,active,ROOT/spec['config'],ro,a.backend,a.force_build and k==24,a.build_verbose)
            print(f"[SST-SPECTRAL] k={k} stage DONE overall={final['overall']} runtime={final['runtime_s']:.1f}s",flush=True)
        data[k]=existing
        for s in active:
            growth_by_source[s][k]=float(data[k][s]['result']['metrics']['normalized_growth'])
        if k==24: continue
        prev_trip={32:[16,24,32],48:[24,32,48],64:[32,48,64]}[k]
        newly=[]
        for s in sorted(active):
            d=_decision_for_source(s,data,prev_trip,policy); decisions[s]=d
            if d['resolved']:
                stop_at[s]=k; newly.append(s)
        print(f'[SST-SPECTRAL] convergence at k={k}: newly resolved={len(newly)}, unresolved={len(active)-len(newly)}',flush=True)
        active-=set(newly)
    records=[]
    for s in sorted(all_sources):
        k=stop_at.get(s,64)
        d=decisions.get(s)
        if d is None:
            # This can only occur if a run was externally truncated before k32.
            cls='INCOMPLETE'; gv=None; fg=growth_by_source[s].get(max(growth_by_source[s]))
            reasons=['missing_required_spectral_rungs']
        elif s in stop_at:
            cls=f'SPECTRAL_CONVERGED_K{k}'; gv=d['growth_verdict']; fg=float(d['growth_values'][-1]); reasons=[]
        else:
            cls='SPECTRAL_UNRESOLVED_AT_K64'; gv=d['growth_verdict']; fg=float(d['growth_values'][-1]); reasons=d['reasons']
        meta=data[16][s]['meta']
        records.append({'source':s,'topology_class':meta.get('topology_class'),'canonical_id':meta.get('canonical_id'),'classification':cls,'growth_verdict':gv,'final_kmax':k,'final_growth':fg,'growth_by_k':{str(kk):vv for kk,vv in sorted(growth_by_source[s].items())},'decision':d,'reasons':reasons})
    write_extension_outputs(out,records,plan)
    (out/'SPECTRAL_EXTENSION_RUNTIME.json').write_text(json.dumps({'runtime_s':time.time()-t0,'backend':a.backend,'baseline':str(baseline) if baseline else 'recomputed','shard_index':a.shard_index,'shard_count':a.shard_count,'selected':len(all_sources),'remaining_unresolved_at_k64':sum(r['classification']=='SPECTRAL_UNRESOLVED_AT_K64' for r in records)},indent=2)+'\n',encoding='utf-8')
    print('[SST-SPECTRAL] synthesis complete:',flush=True)
    from collections import Counter
    print(json.dumps(dict(Counter(r['classification'] for r in records)),indent=2),flush=True)
    return 0

if __name__=='__main__': raise SystemExit(main())
