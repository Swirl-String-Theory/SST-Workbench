from __future__ import annotations
from pathlib import Path
import argparse,json
from .core import scan_links,save_conditioned,relative_output_dir


def load_cfg(p): return json.loads(Path(p).read_text(encoding='utf-8'))

def main():
    ap=argparse.ArgumentParser(prog='sst-katlas-condition')
    sp=ap.add_subparsers(dest='cmd',required=True)
    a=sp.add_parser('scan'); a.add_argument('root'); a.add_argument('--out',default='outputs/SOURCE_SCAN.json')
    a=sp.add_parser('focus'); a.add_argument('record'); a.add_argument('outdir'); a.add_argument('--config',default='config/basic.json')
    a=sp.add_parser('all'); a.add_argument('root'); a.add_argument('outroot'); a.add_argument('--config',default='config/basic.json'); a.add_argument('--limit',type=int,default=None)
    ns=ap.parse_args()
    if ns.cmd=='scan':
        rows=scan_links(Path(ns.root)); s={'format':'SST-KATLAS-CONDITIONING-SCAN-2.0','n_links':len(rows),'n_pd_ok':sum(r.get('pd_ok',False) for r in rows),'rows':rows}; Path(ns.out).parent.mkdir(parents=True,exist_ok=True); Path(ns.out).write_text(json.dumps(s,indent=2,sort_keys=True)+'\n'); print(json.dumps({k:s[k] for k in ('format','n_links','n_pd_ok')},indent=2)); return
    cfg=load_cfg(ns.config)
    if ns.cmd=='focus': print(json.dumps(save_conditioned(Path(ns.record),Path(ns.outdir),cfg),indent=2,sort_keys=True)); return
    root=Path(ns.root); outroot=Path(ns.outroot); rows=scan_links(root); todo=[r for r in rows if r.get('pd_ok')][:ns.limit or None]; results=[]
    for i,r in enumerate(todo,1):
        p=Path(r['path']); od=relative_output_dir(root,p,outroot)
        try: rep=save_conditioned(p,od,cfg); results.append({'katlas_id':r['katlas_id'],'ok':True,'accepted':rep.get('accepted'),'harmonics':rep.get('selected_harmonics')})
        except Exception as e: results.append({'katlas_id':r['katlas_id'],'ok':False,'error':repr(e)})
        print(f'[{i}/{len(todo)}] {r["katlas_id"]} {results[-1]}',flush=True)
    summary={'format':'SST-KATLAS-CONDITIONING-RUN-2.0','n_requested':len(todo),'n_ok':sum(x['ok'] for x in results),'n_conditioned':sum(bool(x.get('accepted')) for x in results),'results':results}; outroot.mkdir(parents=True,exist_ok=True); (outroot/'CONDITIONING_SUMMARY.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n'); print(json.dumps({k:summary[k] for k in ('format','n_requested','n_ok','n_conditioned')},indent=2))

if __name__=='__main__': main()
