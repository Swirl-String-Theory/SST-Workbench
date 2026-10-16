"""Generate three synthetic-control datasets, with a separate sealed labeling key.
Synthetic data are implementation/regression evidence only; never independent physics.
"""
from __future__ import annotations
import hashlib,json,math,secrets,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
INPUTS=ROOT/'inputs'; PRIVATE=ROOT/'private'
INPUTS.mkdir(exist_ok=True);PRIVATE.mkdir(exist_ok=True)
# The permutation is not chosen by the blind analyzer.
rng=secrets.SystemRandom()
labels=['fixed_amplitude','chirped_amplitude','alternating_amplitude']
rng.shuffle(labels)
meta={}; files=[]
for k,label in enumerate(labels,1):
    c_id=f'S{k:02d}'; n=6
    if label=='fixed_amplitude': amps=np.full(n,1.40897017e-15)
    elif label=='chirped_amplitude': amps=1.40897017e-15*np.sqrt(1+0.21*np.arange(n))
    else: amps=1.40897017e-15*np.sqrt(1+0.2*((np.arange(n)%2)*2-1))
    path=INPUTS/f'{c_id}.npz'
    np.savez_compressed(path,
         theta0=np.float64(6*math.pi),beta=np.float64(40.0),
         delay_s=np.float64(8.093299847e-21),
         inertia_kg_m2=np.float64(9.0e-56),mode_mass_kg=np.float64(5.0e-26),
         amplitudes_m=amps)
    sha=hashlib.sha256(path.read_bytes()).hexdigest()
    files.append({'file':path.name,'sha256':sha,'evidence_class':'synthetic_control','control_label':'SEALED'})
    meta[c_id]=label
(INPUTS/'SEALED_INPUT_MANIFEST.json').write_text(json.dumps({'version':'v0.1.0','source_independence':'NONE; SYNTHETIC CONTROLS ONLY','files':files},indent=2)+'\n')
key={'SEALED_LABELS':meta,'do_not_distribute_in_blind_package':True,
     'reason':'disclosure supports implementation audit only, never establishes physical truth'}
PRIVATE.joinpath('CONTROL_REVEAL_ONLY.json').write_text(json.dumps(key,indent=2)+'\n')
PRIVATE.joinpath('REVEAL_COMMITMENT.sha256').write_text(hashlib.sha256(json.dumps(key,sort_keys=True).encode()).hexdigest()+'\n')
print('Generated 3 separately SHA256-sealed synthetic control sources')
