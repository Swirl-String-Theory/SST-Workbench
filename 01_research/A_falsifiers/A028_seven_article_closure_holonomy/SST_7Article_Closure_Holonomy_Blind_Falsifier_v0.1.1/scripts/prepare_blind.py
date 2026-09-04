from pathlib import Path
import argparse,json,hashlib,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sst7.blind import prepare

a=argparse.ArgumentParser(); a.add_argument('--dataset',required=True); a.add_argument('--run-dir',required=True); a.add_argument('--config',default='config/basic.json'); ns=a.parse_args()
root=Path(__file__).resolve().parents[1]; cfg=json.loads((root/ns.config).read_text()); run=Path(ns.run_dir); run.mkdir(parents=True,exist_ok=True)
pub=prepare(Path(ns.dataset),run,cfg.get('holdout_fraction',0.3))
config_text=json.dumps(cfg,sort_keys=True,separators=(',',':'))
pre={'package_version':'0.1.1','config':cfg,'config_sha256':hashlib.sha256(config_text.encode()).hexdigest(),'public_manifest_commitment':pub['private_commitment_sha256'],'rule':'thresholds frozen before scoring; source names hidden until reveal'}
(run/'preregistration.json').write_text(json.dumps(pre,indent=2,sort_keys=True),encoding='utf-8')
print(f"[SST7] prepared {pub['n_cases']} opaque cases in {run}")
