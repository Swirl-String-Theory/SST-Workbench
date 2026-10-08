from pathlib import Path
import hashlib,sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from run_instance import ROOT,_load_framework
_load_framework()
from sst_falsifier.config import load_instance_config
from sst_falsifier.runner import instance_output_root
from sst_falsifier.outputs import deterministic_zip
cfg=load_instance_config(ROOT); out=instance_output_root(ROOT,cfg); prefix=f"{cfg['project']['name']}_{cfg['project']['version']}-outputs"
parent=ROOT.parent
combined=parent/f'{prefix}.zip'; deterministic_zip(out,combined,exclude_parts={'__pycache__','.pytest_cache','.venv','build'})
for p in (parent/f'{prefix}_BLIND.zip',parent/f'{prefix}_REVEALED.zip',combined):
 if p.exists():
  h=hashlib.sha256(p.read_bytes()).hexdigest(); Path(str(p)+'.sha256').write_text(f'{h}  {p.name}\n',encoding='ascii'); print(p.name,h)
