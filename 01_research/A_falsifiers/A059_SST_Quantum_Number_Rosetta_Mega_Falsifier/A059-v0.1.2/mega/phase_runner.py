from __future__ import annotations
from pathlib import Path
import json, shutil, sys, traceback
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from framework_bootstrap import load_framework
FRAMEWORK=load_framework()
from sst_falsifier.protocol import assert_frozen
from sst_falsifier.blind import assert_blind_tree
from .common import implementation_verify, phase_dir, write_json, make_local_manifest
from .phases import PHASES


def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0].upper() not in PHASES:
        print('Usage: run_python.cmd -m mega.phase_runner P00|P01|...|P08');return 2
    pid=argv[0].upper()
    assert_frozen(ROOT,ROOT/'preregistration'/'FROZEN_PROTOCOL.json')
    assert_blind_tree(ROOT)
    impl=implementation_verify(ROOT)
    if not impl['pass']:raise RuntimeError('implementation manifest mismatch: '+json.dumps(impl))
    out=phase_dir(pid,ROOT)
    if out.exists():shutil.rmtree(out)
    out.mkdir(parents=True)
    try:
        result=PHASES[pid](ROOT,out)
    except Exception as e:
        result={'schema':'A059-PHASE-RESULT-1','phase_id':pid,'status':'UNRESOLVED','evidence_class':'RUNTIME_EXCEPTION','reason':f'{type(e).__name__}: {e}','traceback':traceback.format_exc()}
    result['implementation_manifest_sha256']=impl.get('manifest_sha256')
    write_json(out/'RESULT.json',result)
    manifest=make_local_manifest(out)
    print(json.dumps({'phase':pid,'status':result.get('status'),'evidence_class':result.get('evidence_class'),'output':str(out),'phase_manifest_sha256':manifest.get('manifest_sha256')},indent=2))
    return 0 if result.get('status') in {'PASS','FAIL','UNRESOLVED','NOT_APPLICABLE','DEFERRED'} else 1

if __name__=='__main__':raise SystemExit(main())
