from pathlib import Path
import json, numpy as np
from sst_katlas_conditioning.core import parse_katlas_pd,pd_to_components,condition_components,linking_matrix,resample_closed


def test_hopf_pd_parse_and_condition():
    pd=parse_katlas_pd('X<sub>4132</sub> X<sub>2314</sub>')
    assert pd==[(4,1,3,2),(2,3,1,4)]
    raw=pd_to_components(pd)
    assert len(raw)==2
    cfg={'n_points_per_component':96,'max_harmonics':8,'circularize_first_harmonic':True,'homotopy_samples':9,'guard_points':96,'min_homotopy_clearance':0.015,'linking_number_tolerance':0.30,'max_curvature_rms_ratio':0.95}
    c,rep=condition_components(raw,cfg)
    assert rep['accepted']
    assert rep['selected_harmonics'] is not None
    assert len(c)==2
    assert abs(round(linking_matrix(c)[0,1]))==1
    assert rep['conditioned_metrics']['turn_angle_rms_rad'] < rep['raw_metrics']['turn_angle_rms_rad']
    assert rep['conditioned_metrics']['ds_cv'] < 0.02


def test_uniform_resampling():
    t=np.linspace(0,2*np.pi,37,endpoint=False); q=np.c_[2*np.cos(t),np.sin(t),0*t]; r=resample_closed(q,96); ds=np.linalg.norm(np.roll(r,-1,axis=0)-r,axis=1); assert ds.std()/ds.mean()<0.02


def test_pd_embedding_deterministic_across_hash_seeds(tmp_path):
    import os, subprocess, sys
    code = r'''
import hashlib, numpy as np
from sst_katlas_conditioning.core import parse_katlas_pd, pd_to_components
pd=parse_katlas_pd("X<sub>4132</sub> X<sub>2314</sub>")
arr=np.vstack(pd_to_components(pd))
print(hashlib.sha256(arr.tobytes()).hexdigest())
'''
    root = Path(__file__).resolve().parents[1]
    hashes=[]
    for seed in ('1','77','123456'):
        env=os.environ.copy(); env['PYTHONHASHSEED']=seed
        env['PYTHONPATH']=str(root/'src') + (os.pathsep + env['PYTHONPATH'] if env.get('PYTHONPATH') else '')
        out=subprocess.check_output([sys.executable,'-c',code],env=env,text=True).strip()
        hashes.append(out)
    assert len(set(hashes))==1
