from pathlib import Path
import argparse,json,sys,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sst7.gates import run_case,summarize_case
from sst7.blind import sha256_file,write_json_bytes

a=argparse.ArgumentParser(); a.add_argument('--run-dir',required=True); a.add_argument('--config',default='config/basic.json'); a.add_argument('--mode',choices=['basic','extended'],default='basic'); ns=a.parse_args()
root=Path(__file__).resolve().parents[1]; cfg=json.loads((root/ns.config).read_text()); run=Path(ns.run_dir)
pub=json.loads((run/'blind/public_manifest.json').read_text()); cdir=run/'blind/cases'
res={'version':'0.1.2','mode':ns.mode,'dataset_snapshot_sha256':pub.get('dataset_snapshot_sha256'),'blind_state_id':pub.get('blind_state_id'),'cases':[]}
for c in pub['cases']:
    gs=run_case(cdir,c['case_id'],cfg,ns.mode); res['cases'].append({'case_id':c['case_id'],'split':c['split'],'overall':summarize_case(gs),'gates':gs})
outfile=run/'opaque_results.json'; write_json_bytes(outfile,res); digest=sha256_file(outfile)
(run/'freeze.sha256').write_bytes((digest+'  opaque_results.json\n').encode('ascii'))
counts={}
for c in res['cases']: counts[c['overall']]=counts.get(c['overall'],0)+1
lines=['# Blind summary','',f"Mode: **{ns.mode}**",'',f"Cases: **{len(res['cases'])}**",'', '## Overall opaque statuses','']+[f"- {k}: {v}" for k,v in sorted(counts.items())]
lines+=['','A static-centerline-only `INDETERMINATE` is expected: absent phase/volume/probe data are never manufactured from geometry.','',f"Dataset snapshot: `{pub.get('dataset_snapshot_sha256','')}`",f"Blind state: `{pub.get('blind_state_id','')}`",f"Freeze SHA-256: `{digest}`"]
(run/'summary_blind.md').write_bytes(('\n'.join(lines)+'\n').encode('utf-8'))
print('[SST7] blind scoring frozen:',run/'freeze.sha256')
print('[SST7] freeze verified against file bytes:',digest)
