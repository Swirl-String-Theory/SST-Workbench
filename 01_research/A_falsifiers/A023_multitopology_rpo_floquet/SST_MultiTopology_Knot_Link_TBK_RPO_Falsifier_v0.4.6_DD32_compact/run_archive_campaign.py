from __future__ import annotations
import argparse, csv, hashlib, json, math, zipfile
from collections import Counter, defaultdict
from pathlib import Path
from sst_blind.multitopology import run_panel
from sst_blind.io import load_fseries, load_xyz_text, sha256_file

ROOT=Path(__file__).resolve().parent
ARC=ROOT/'repro_inputs'/'source_archives'
CACHE=ROOT/'_archive_cache'

def prepare():
    CACHE.mkdir(exist_ok=True)
    kroot=CACHE/'knotplot'; froot=CACHE/'fremlin'
    if not kroot.exists():
        kroot.mkdir(); zipfile.ZipFile(ARC/'KnotPlot_RidgeRunner_Knots_Links.zip').extractall(kroot)
    if not froot.exists():
        froot.mkdir(); zipfile.ZipFile(ARC/'Fremlin_Knots_FourierSeries.zip').extractall(froot)
    return kroot,froot

def topology_class(stem):
    if stem.startswith('link_0.'): return 'unlink'
    if stem.startswith('link_'): return 'link'
    if stem.startswith('torus_'):
        try:
            p,q=map(int,stem.split('_',1)[1].split('.'))
            return 'torus_link' if math.gcd(p,q)>1 else 'torus_knot'
        except Exception: return 'torus'
    if stem.startswith('knot_0.'): return 'unknot'
    return 'knot'

def all_entries():
    kroot,froot=prepare(); out=[]
    for p in sorted(kroot.glob('*_final.txt')):
        stem=p.name[:-10]; mp=kroot/(stem+'_final.metrics.json')
        canonical=stem.replace('knot_','').replace('link_','').replace('torus_','').replace('.', '_')
        out.append(dict(source=f'knotplot:{stem}',source_family='knotplot',canonical_id=canonical,variant=p.stem,
                        kind='knotplot',topology_class=topology_class(stem),path=str(p),metrics_path=str(mp)))
    for p in sorted(froot.rglob('*.fseries')):
        parent=p.parent.name; stem=p.stem
        cls='unknot' if parent in ('1_1','0_1') else 'knot'
        out.append(dict(source=f'fremlin:{parent}:{stem}',source_family='fremlin',canonical_id=parent,variant=stem,
                        kind='fseries',topology_class=cls,path=str(p)))
    out.sort(key=lambda x:(x['source_family'],x['canonical_id'],x['variant']))
    return out

def inventory(entries,out_path):
    rows=[]
    for e in entries:
        rows.append({k:e.get(k,'') for k in ('source','source_family','canonical_id','variant','kind','topology_class')} | {'sha256':sha256_file(e['path'])})
    out_path=Path(out_path); out_path.parent.mkdir(parents=True,exist_ok=True)
    with out_path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    return rows

def validate(entries,n_raw=1024):
    ok=[]; bad=[]
    for e in entries:
        try:
            x=load_fseries(e['path'],n_raw) if e['kind']=='fseries' else load_xyz_text(e['path'])
            ok.append({'source':e['source'],'points':len(x),'sha256':sha256_file(e['path'])})
        except Exception as ex: bad.append({'source':e['source'],'error':repr(ex)})
    return ok,bad

def archive_conclusions(out,results,mapping,total_inventory_count):
    out=Path(out); lines=['# Full Archive Conclusions','',f'Analyzed datasets in this campaign: **{len(results)}** of inventory **{total_inventory_count}**.','']
    byclass=defaultdict(list); bycanon=defaultdict(list); fails=Counter()
    for bid,r in results.items():
        m=mapping[bid]; byclass[m['topology_class']].append(r); bycanon[m.get('canonical_id','?')].append((m,r))
        for g,v in r['gates'].items():
            if v is False: fails[g]+=1
    lines += ['## Classification by topology class','', '| class | N | PASS | FAIL | median growth |', '|---|---:|---:|---:|---:|']
    import numpy as np
    for cls,rr in sorted(byclass.items()):
        gs=[x['metrics']['normalized_growth'] for x in rr]
        lines.append(f"| {cls} | {len(rr)} | {sum(x['status']=='PASS' for x in rr)} | {sum(x['status']=='FAIL' for x in rr)} | {np.median(gs):.6g} |")
    lines += ['', '## Gate failure counts','', '| gate | FAIL count |', '|---|---:|']
    for g,n in fails.most_common(): lines.append(f'| {g} | {n} |')
    ranked=sorted([(r['metrics']['normalized_growth'],mapping[b]['source'],r['status']) for b,r in results.items()])
    lines += ['', '## Lowest normalized-growth candidates','', '| source | growth | status |','|---|---:|---|']
    for g,s,st in ranked[:20]: lines.append(f'| {s} | {g:.7g} | {st} |')
    lines += ['', '## Highest normalized-growth candidates','', '| source | growth | status |','|---|---:|---|']
    for g,s,st in ranked[-20:][::-1]: lines.append(f'| {s} | {g:.7g} | {st} |')
    lines += ['', '## Representation sensitivity','', 'Canonical topology groups with more than one Fremlin/KnotPlot representation are shown; spread is descriptive and does not change gates.','', '| canonical | N | min growth | max growth | spread |', '|---|---:|---:|---:|---:|']
    for cid,grp in sorted(bycanon.items()):
        if len(grp)<2: continue
        gs=[r['metrics']['normalized_growth'] for _,r in grp]
        lines.append(f'| {cid} | {len(grp)} | {min(gs):.6g} | {max(gs):.6g} | {(max(gs)-min(gs)):.6g} |')
    rpos=[mapping[b]['source'] for b,r in results.items() if r['metrics'].get('rpo_found')]
    lines += ['', '## RPO candidates','', (', '.join(rpos) if rpos else 'No valid excursion-and-return RPO candidate in this campaign.'), '',
              '## Guardrails','', '- PASS/FAIL remains per-dataset and basis-dependent.', '- RPO/Floquet is evaluated only for datasets passing the preregistered linear-growth precondition in EXTRA_EXTENDED/FULL.', '- All Fremlin variants are separate inputs; no suffix variant is silently discarded.', '- Link pairwise Gauss-linking conservation is monitored without an imposed reconnection operator.']
    (out/'ARCHIVE_CONCLUSIONS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

def main():
    ap=argparse.ArgumentParser(description='SST v0.4.6.1 full archive campaign: every Fremlin .fseries and every KnotPlot/RidgeRunner *_final.txt')
    ap.add_argument('--config',default='configs/archive_extra_extended.json')
    ap.add_argument('--out-dir',default='outputs_archive_extra_extended')
    ap.add_argument('--backend',default='auto',choices=['auto','openmp','cpu','sycl','sycl-fp32','sycl-dd32','sycl-fp64','python'])
    ap.add_argument('--allow-sycl-cpu',action='store_true'); ap.add_argument('--force-build',action='store_true'); ap.add_argument('--build-verbose',action='store_true')
    ap.add_argument('--shard-count',type=int,default=1); ap.add_argument('--shard-index',type=int,default=0)
    ap.add_argument('--validate-only',action='store_true'); ap.add_argument('--inventory-only',action='store_true')
    a=ap.parse_args(); all_e=all_entries(); out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    inventory(all_e,out/'ARCHIVE_INVENTORY.csv')
    counts=Counter(e['source_family'] for e in all_e)
    (out/'ARCHIVE_INVENTORY.json').write_text(json.dumps({'total':len(all_e),'counts':counts,'entries':[{k:v for k,v in e.items() if k not in ('path','metrics_path')} for e in all_e]},indent=2,default=dict),encoding='utf-8')
    if a.inventory_only:
        print(json.dumps({'total':len(all_e),'fremlin':counts['fremlin'],'knotplot':counts['knotplot'],'out_dir':str(out)},indent=2)); return 0
    if a.validate_only:
        ok,bad=validate(all_e); (out/'VALIDATION.json').write_text(json.dumps({'ok':ok,'bad':bad},indent=2),encoding='utf-8')
        print(json.dumps({'total':len(all_e),'ok':len(ok),'bad':len(bad),'out_dir':str(out)},indent=2)); return 0 if not bad else 2
    if a.shard_count<1 or not 0<=a.shard_index<a.shard_count: raise SystemExit('invalid shard parameters')
    selected=[e for i,e in enumerate(all_e) if i%a.shard_count==a.shard_index]
    (out/'SHARD_INFO.json').write_text(json.dumps({'shard_index':a.shard_index,'shard_count':a.shard_count,'selected':len(selected),'inventory_total':len(all_e)},indent=2),encoding='utf-8')
    final,results,mapping=run_panel(selected,a.config,out,backend=a.backend,allow_sycl_cpu=a.allow_sycl_cpu,force_build=a.force_build,build_verbose=a.build_verbose)
    archive_conclusions(out,results,mapping,len(all_e))
    print(json.dumps({'inventory_total':len(all_e),'selected':len(selected),'overall':final['overall'],'out_dir':str(out)},indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
