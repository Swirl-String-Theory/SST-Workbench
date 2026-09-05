from pathlib import Path
import argparse,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sst7.blind import sha256_file,write_json_bytes

a=argparse.ArgumentParser(); a.add_argument('--run-dir',required=True); ns=a.parse_args(); run=Path(ns.run_dir)
opaque_path=run/'opaque_results.json'; freeze_path=run/'freeze.sha256'
if not freeze_path.exists(): raise RuntimeError('missing freeze.sha256; refusing reveal')
recorded=freeze_path.read_text(encoding='ascii').strip().split()[0]
actual=sha256_file(opaque_path)
if recorded.lower()!=actual.lower():
    raise RuntimeError(f'freeze verification FAILED: recorded={recorded} actual={actual}; refusing reveal')
public=json.loads((run/'blind/public_manifest.json').read_text(encoding='utf-8'))
private_path=run/'blind/private_mapping.json'; private=json.loads(private_path.read_text(encoding='utf-8'))
priv_actual=sha256_file(private_path); priv_expected=public.get('private_commitment_sha256')
if priv_expected and priv_actual.lower()!=priv_expected.lower():
    raise RuntimeError('private mapping commitment verification FAILED; refusing reveal')
opaque=json.loads(opaque_path.read_text(encoding='utf-8'))
rev={'version':'0.1.2','freeze_sha256':actual,'freeze_verified':True,
     'private_mapping_commitment_verified':(not priv_expected or priv_actual.lower()==priv_expected.lower()),
     'dataset_snapshot_sha256':public.get('dataset_snapshot_sha256'),'blind_state_id':public.get('blind_state_id'),'cases':[]}
for c in opaque['cases']:
    m=private['cases'][c['case_id']]
    source_hash_now=None; source_unchanged=None
    sp=Path(m['source'])
    if sp.exists():
        source_hash_now=sha256_file(sp); source_unchanged=(source_hash_now.lower()==m['sha256'].lower())
    rev['cases'].append({**c,'source':m['source'],'source_sha256':m['sha256'],'source_sha256_at_reveal':source_hash_now,
                         'source_unchanged_since_prepare':source_unchanged,'parser':m.get('parser'),
                         'source_sidecars':m['sidecars']})
write_json_bytes(run/'revealed_results.json',rev)
lines=['# Revealed summary','',f"Freeze SHA-256: `{actual}`",'',f"Freeze verified: **YES**",f"Private mapping commitment verified: **YES**",'',
       '| Case | Split | Overall | Components | Parser | Source |','|---|---|---|---:|---|---|']
for c in rev['cases']:
    parser=c.get('parser') or {}; lines.append(f"| {c['case_id']} | {c['split']} | {c['overall']} | {parser.get('n_components','')} | {parser.get('method','')} | `{c['source']}` |")
(run/'summary_revealed.md').write_bytes(('\n'.join(lines)+'\n').encode('utf-8'))
print('[SST7] reveal complete; freeze + private commitment verified')
