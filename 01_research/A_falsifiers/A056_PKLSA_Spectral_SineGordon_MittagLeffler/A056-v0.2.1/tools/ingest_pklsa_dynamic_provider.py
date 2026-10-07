from pathlib import Path
import argparse,json,shutil,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from sst_falsifier_framework.sources import validate_dynamic_metadata
p=argparse.ArgumentParser(description='Validate/copy provider-native t,s,phi NPZ cases into an A056 blind input directory.')
p.add_argument('provider_dir'); p.add_argument('destination'); a=p.parse_args(); src=Path(a.provider_dir); dst=Path(a.destination); dst.mkdir(parents=True,exist_ok=True)
count=0
for npz in sorted(src.glob('*.npz')):
    meta=npz.with_suffix('.json')
    if not meta.exists(): raise SystemExit(f'missing metadata: {meta}')
    m=json.loads(meta.read_text(encoding='utf-8')); chk=validate_dynamic_metadata(m,synthetic=False)
    if not chk['pass']: raise SystemExit(f'{meta.name}: missing {chk["missing"]}')
    z=np.load(npz,allow_pickle=False)
    for key in ('t','s','phi'):
        if key not in z: raise SystemExit(f'{npz.name}: missing {key}')
    shutil.copy2(npz,dst/npz.name); shutil.copy2(meta,dst/meta.name); count+=1
print(json.dumps({'status':'PASS','copied_cases':count,'destination':str(dst)},indent=2))
