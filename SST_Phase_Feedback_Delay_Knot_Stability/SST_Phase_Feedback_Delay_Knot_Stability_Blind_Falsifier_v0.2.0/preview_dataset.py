from pathlib import Path
import argparse,json,hashlib,numpy as np
from sst_phase_delay_falsifier.geometry import read_xyz,resample_closed
p=argparse.ArgumentParser(); p.add_argument('input'); p.add_argument('--pattern',default='*_i10000.txt');p.add_argument('--registry',required=True);a=p.parse_args()
files=sorted(Path(a.input).rglob(a.pattern)); reg=set(json.loads(Path(a.registry).read_text())['canonical64_sha256']); groups={}
for f in files:
 raw=read_xyz(f)
 xi=resample_closed(raw,128); ident=hashlib.sha256(np.ascontiguousarray(xi,dtype='<f8').tobytes()).hexdigest()
 xn=resample_closed(raw,64); nov=hashlib.sha256(np.ascontiguousarray(xn,dtype='<f8').tobytes()).hexdigest()
 groups.setdefault(ident,{'nov':nov,'n':0}); groups[ident]['n']+=1
seen=sum(q['nov'] in reg for q in groups.values()); novel=len(groups)-seen
print(f'[PFD v0.2] source files       : {len(files)}')
print(f'[PFD v0.2] unique identity128 : {len(groups)}')
print(f'[PFD v0.2] duplicates removed : {len(files)-len(groups)}')
print(f'[PFD v0.2] seen in v0.1.7     : {seen}')
print(f'[PFD v0.2] novel unique       : {novel}')
print('[PFD v0.2] CONFIRMATORY INPUT PASS' if novel>=8 else '[PFD v0.2] CONFIRMATORY INPUT INSUFFICIENT: need >= 8 novel unique geometries')
raise SystemExit(0 if novel>=8 else 2)
