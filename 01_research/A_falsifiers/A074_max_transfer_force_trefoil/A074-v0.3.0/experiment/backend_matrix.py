"""v1.1.0 backend adapter. Count ONLY real executed numerical science.
A compiled native template Biot-Savart kernel is NOT independent Euler validation.
"""
from pathlib import Path
import hashlib,json
from experiment.qualification import prepared_state,one_level
from experiment.euler3d import Euler3D

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def run_backend_matrix(*,root,cfg,mode,output_dir,devices):
    root=Path(root);out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    science_cfg,curve,identity=prepared_state()
    entry=one_level(32,science_cfg,curve,identity,steps=False)
    obs=[float(entry['initial_marker_fit']['normal_residual']),float(entry['full_field_fit']['relative_euler_field_residual']),float(entry['euler_initial_diagnostics']['energy_J'])]
    payload={'executed':True,'actual_backend':'python','input_sha256':identity['candidate_full_input_sha256'],
             'observable':obs,'precision':'float64','physical_final_time':None,'science':'Euler finite-core vorticity field residual, n32; diagnostic only'}
    path=out/'py.json';path.write_text(json.dumps(payload,sort_keys=True,indent=2)+'\n')
    src=root/'experiment/qualification.py'
    return {'py':{'executed':True,'actual_backend':'python','source_path':str(src.relative_to(root)),
                  'source_sha256':sha(src),'evidence_path':str(path.relative_to(output_dir.parent)),
                  'evidence_sha256':sha(path),'input_sha256':identity['candidate_full_input_sha256'],'observable':obs},
            'cpp':{'executed':False,'reason':'No independently implemented C++ finite-core Euler full-field solver; cannot count unrelated default native example'},
            'gpu':{'executed':False,'reason':'No independently implemented Intel Arc finite-core Euler full-field solver; CPU tensor or probe not counted'}}
