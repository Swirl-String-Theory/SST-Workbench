from pathlib import Path
import argparse,json,sys,hashlib

a=argparse.ArgumentParser(); a.add_argument('--run-dir',required=True); ns=a.parse_args(); run=Path(ns.run_dir)
opaque=json.loads((run/'opaque_results.json').read_text()); private=json.loads((run/'blind/private_mapping.json').read_text())
rev={'version':'0.1.0','freeze_sha256':hashlib.sha256((run/'opaque_results.json').read_bytes()).hexdigest(),'cases':[]}
for c in opaque['cases']:
    m=private['cases'][c['case_id']]
    rev['cases'].append({**c,'source':m['source'],'source_sha256':m['sha256'],'source_sidecars':m['sidecars']})
(run/'revealed_results.json').write_text(json.dumps(rev,indent=2,sort_keys=True),encoding='utf-8')
lines=['# Revealed summary','',f"Freeze SHA-256: `{rev['freeze_sha256']}`",'','| Case | Split | Overall | Source |','|---|---|---|---|']
for c in rev['cases']: lines.append(f"| {c['case_id']} | {c['split']} | {c['overall']} | `{c['source']}` |")
(run/'summary_revealed.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('[SST7] reveal complete')
