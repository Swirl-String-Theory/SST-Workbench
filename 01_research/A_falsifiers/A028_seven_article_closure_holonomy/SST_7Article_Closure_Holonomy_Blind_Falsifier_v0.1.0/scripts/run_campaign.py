from pathlib import Path
import argparse,json,sys,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sst7.gates import run_case,summarize_case

a=argparse.ArgumentParser(); a.add_argument('--run-dir',required=True); a.add_argument('--config',default='config/basic.json'); a.add_argument('--mode',choices=['basic','extended'],default='basic'); ns=a.parse_args()
root=Path(__file__).resolve().parents[1]; cfg=json.loads((root/ns.config).read_text()); run=Path(ns.run_dir)
pub=json.loads((run/'blind/public_manifest.json').read_text()); cdir=run/'blind/cases'
res={'version':'0.1.0','mode':ns.mode,'cases':[]}
for c in pub['cases']:
    gs=run_case(cdir,c['case_id'],cfg,ns.mode); res['cases'].append({'case_id':c['case_id'],'split':c['split'],'overall':summarize_case(gs),'gates':gs})
txt=json.dumps(res,indent=2,sort_keys=True); (run/'opaque_results.json').write_text(txt,encoding='utf-8'); (run/'freeze.sha256').write_text(hashlib.sha256(txt.encode()).hexdigest()+'  opaque_results.json\n')
counts={}
for c in res['cases']: counts[c['overall']]=counts.get(c['overall'],0)+1
lines=['# Blind summary','',f"Mode: **{ns.mode}**",'',f"Cases: **{len(res['cases'])}**",'', '## Overall opaque statuses','']+[f"- {k}: {v}" for k,v in sorted(counts.items())]
lines+=['','A static-centerline-only `INDETERMINATE` is expected: absent phase/volume/probe data are never manufactured from geometry.','',f"Freeze SHA-256: `{hashlib.sha256(txt.encode()).hexdigest()}`"]
(run/'summary_blind.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('[SST7] blind scoring frozen:',run/'freeze.sha256')
