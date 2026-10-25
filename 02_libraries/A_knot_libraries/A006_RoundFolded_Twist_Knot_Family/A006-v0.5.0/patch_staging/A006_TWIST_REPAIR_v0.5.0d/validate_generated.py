from pathlib import Path
import json,sys,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'validation_lib'))
from build_ladder import check_actual
from clearance import global_min_nonlocal
from knotplot_io import encode,decode
m=json.loads((ROOT/'MANIFEST.json').read_text())
for i,c in enumerate(m['cases']):
    q=np.loadtxt(ROOT/'REPLACEMENTS'/c['file']);name=c['name'];n=c['count'];branch=c['branch']
    # Only a projected Alexander check. No independent topological label attestation.
    try:
        test=check_actual(q,c['m']-2)
        c['topology_projected_gate']='PASS';c['topology_projected']=test
    except Exception as exc:
        c['topology_projected_gate']='FAIL';c['topology_error']=str(exc)
    try:
        if branch=='ORIG':
            gap=global_min_nonlocal(q)
            c['segment_clearance_coordinate_units']=gap['distance']
            c['segment_clearance_screen']='PASS' if gap['distance']>.05 else 'FAIL'
        else:
            match=next(t for t in m['cases'] if t['name']==name and t['count']==n and t['branch']=='ORIG')
            c['segment_clearance_coordinate_units']=match['segment_clearance_coordinate_units']
            c['segment_clearance_screen']=match['segment_clearance_screen']
    except Exception as exc:
        c['segment_clearance_screen']='ERROR';c['clearance_error']=str(exc)
    blob=encode([q]);rec=decode(blob)
    assert len(rec)==1 and np.array_equal(rec[0],q)
    kpt=(ROOT/'REPLACEMENTS'/Path(c['file']).with_suffix('.kpt'))
    kpt.write_bytes(blob);c['kpt_filename']=kpt.name;c['kpt_sha256']=hashlib.sha256(blob).hexdigest();c['kpt_roundtrip']='PASS'
    required=['edge_cv_gate_0p05','morphology_gap_gate_5deg','periodic_closure_gate_0p1','topology_projected_gate','segment_clearance_screen','kpt_roundtrip']
    c['release_status']='STATIC_GEOMETRY_CANDIDATE_NOT_EULER_CERTIFIED' if all(c.get(k)=='PASS' for k in required) else 'QUARANTINE_PREVIEW_ONLY'
    print(f"{i+1}/48 {name:<7} {n:<4} {branch:<6} {c['release_status']} d={c.get('segment_clearance_coordinate_units',-1):.4f}",flush=True)
(ROOT/'MANIFEST.json').write_text(json.dumps(m,indent=2)+'\n')
