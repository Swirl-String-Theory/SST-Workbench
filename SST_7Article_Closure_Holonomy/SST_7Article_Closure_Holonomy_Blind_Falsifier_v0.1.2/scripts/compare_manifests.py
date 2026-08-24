from pathlib import Path
import argparse,json,sys

a=argparse.ArgumentParser(); a.add_argument('--a',required=True); a.add_argument('--b',required=True); ns=a.parse_args()
def load(p): return json.loads((Path(p)/'blind/public_manifest.json').read_text(encoding='utf-8'))
A=load(ns.a); B=load(ns.b)
ka=[(c['case_id'],c['split'],c.get('n_components')) for c in A['cases']]
kb=[(c['case_id'],c['split'],c.get('n_components')) for c in B['cases']]
if A.get('dataset_snapshot_sha256')!=B.get('dataset_snapshot_sha256') or ka!=kb:
    print('[SST7] MANIFEST MISMATCH',file=sys.stderr); sys.exit(2)
print('[SST7] manifests match:',len(ka),'cases; snapshot',A.get('dataset_snapshot_sha256'))
