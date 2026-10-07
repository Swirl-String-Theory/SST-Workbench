from __future__ import annotations
from pathlib import Path
import os,sys
ROOT=Path(__file__).resolve().parent
try:
    import sst_falsifier
except ImportError:
    candidates=[]
    env=os.environ.get("SST_FALSIFIER_FRAMEWORK_ROOT")
    if env: candidates.append(Path(env))
    for parent in [ROOT,*ROOT.parents]:
        candidates += [parent/"04_tools"/"D_proof"/"SST_Falsifier_Framework_v1.0.0", parent/"SST_Falsifier_Framework_v1.0.0"]
    for c in candidates:
        if (c/"sst_falsifier").exists(): sys.path.insert(0,str(c)); break
    import sst_falsifier
from sst_falsifier.runner import run_mode
if __name__=="__main__":
    mode=sys.argv[1] if len(sys.argv)>1 else "BASIC"
    raise SystemExit(run_mode(ROOT,mode))
