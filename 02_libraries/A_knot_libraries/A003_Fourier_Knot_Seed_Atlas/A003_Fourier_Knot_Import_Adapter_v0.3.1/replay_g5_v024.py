"""Replay the uploaded v0.2.4 G5-F3 discrepancy without pyKnotid.

Emits diagnosis from a hashed historical report excerpt; never changes gate status.
"""
from __future__ import annotations
import json,hashlib,sys
from pathlib import Path
import numpy as np
import g5_extended as g
import fourier_atlas_adapter as a


def main():
    home=Path(__file__).resolve().parent
    gold=json.loads((home/'tests/fixtures/g5_v024_f3_f4_golden.json').read_text())
    cases=[]
    for case in gold['seed_results']:
        report=g.summarize_invariant_observations(
            case['observations'],case['expected_polynomial_coefficients'])
        cases.append({'id':case['id'],'v024_status':case['status'],
                      'v025_assessment':report})
    atlas=a.resolve_atlas_root(None)
    source=atlas/'manifest.json'
    manifest,_=a.load_manifest(atlas)
    picks=[]
    for n in (1200,2400):
        rec=next(x for x in manifest['records'] if x['id']=='fibonacci_torus_F3'
                 and x['sampling']=='uniform_t' and x['points']==n)
        xyz=(atlas/rec['file']).resolve()
        if hashlib.sha256(xyz.read_bytes()).hexdigest()!=rec['sha256']:
            raise RuntimeError('source hash changed: fail closed')
        pts=np.loadtxt(xyz)
        for index in range(4):
            q=pts@g.rotation_for_projection(index).T
            picks.append({'N':n,'projection':index,
                          'source_sha256':rec['sha256'],
                          'angles_rad':list(g.PROJECTION_ANGLES[index]),
                          'geometry':g.projected_crossing_diagnostics(q)})
    result={'schema':'sst.a003.g5.projection-replay/1',
            'adapter_version':'0.2.5','source_atlas_manifest_sha256':a.PINNED_ATLAS_MANIFEST_SHA256,
            'historical_report_sha256':gold['source_report_sha256'],
            'historical_v024_G5_status':gold['source_report_g5_status'],
            'cases':cases,'geometric_projection_diagnostics':picks,
            'historical_fail_reclassified_as_pass':False,
            'not_a_new_pyknotid_result':True,
            'G6_PKLSA_EULER':'NOT_RUN'}
    target=home/'outputs_g5_projection_replay'/'projection_replay.json'
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'historical_status':result['historical_v024_G5_status'],
                      'f3_v025_assessment':cases[0]['v025_assessment']['status'],
                      'geometric_projection_count':len(picks),'result':str(target)},indent=2))
    return 0 if cases[0]['v025_assessment']['status']=='INVARIANT_MISMATCH' else 2


if __name__=='__main__':sys.exit(main())
