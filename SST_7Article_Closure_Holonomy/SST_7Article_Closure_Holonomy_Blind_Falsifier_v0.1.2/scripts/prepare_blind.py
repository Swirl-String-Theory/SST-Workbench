from pathlib import Path
import argparse,json,hashlib,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sst7.blind import prepare,write_json_bytes

a=argparse.ArgumentParser()
a.add_argument('--dataset',required=True)
a.add_argument('--run-dir',required=True)
a.add_argument('--config',default='config/basic.json')
a.add_argument('--shared-state-dir',default='results/_blind_state',help='persistent private seed cache; same dataset snapshot => same opaque IDs/split')
a.add_argument('--seed-hex',default=None,help='optional explicit 256-bit seed for reproducible testing')
ns=a.parse_args()
root=Path(__file__).resolve().parents[1]; cfg=json.loads((root/ns.config).read_text()); run=Path(ns.run_dir); run.mkdir(parents=True,exist_ok=True)
state=Path(ns.shared_state_dir) if ns.shared_state_dir else None
pub=prepare(Path(ns.dataset),run,cfg.get('holdout_fraction',0.3),seed_hex=ns.seed_hex,state_dir=state)
config_text=json.dumps(cfg,sort_keys=True,separators=(',',':'))
pre={'package_version':'0.1.2','config':cfg,'config_sha256':hashlib.sha256(config_text.encode()).hexdigest(),
     'public_manifest_commitment':pub['private_commitment_sha256'],
     'dataset_snapshot_sha256':pub['dataset_snapshot_sha256'],'blind_state_id':pub['blind_state_id'],
     'rule':'thresholds frozen before scoring; source names hidden until reveal; same dataset snapshot reuses opaque IDs and train/holdout split'}
write_json_bytes(run/'preregistration.json',pre)
print(f"[SST7] prepared {pub['n_cases']} opaque cases in {run}")
print(f"[SST7] dataset snapshot: {pub['dataset_snapshot_sha256']}")
print(f"[SST7] shared blind state: {pub['blind_state_id']}")
