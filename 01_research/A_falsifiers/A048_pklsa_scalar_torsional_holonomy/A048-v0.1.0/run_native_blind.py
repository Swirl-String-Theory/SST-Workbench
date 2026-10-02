from pathlib import Path
import json, os
os.environ['SST_BACKEND']='native'
from sst_torsion.campaign import analyze_input
ROOT=Path(__file__).resolve().parent
OUT=ROOT.parent/'A048_PKLSA_Scalar_Torsional_Holonomy_Falsifier_v0.1.0-outputs'
CFG=json.loads((ROOT/'configs'/'default.json').read_text(encoding='utf-8'))
if __name__=='__main__':
    s,_=analyze_input(OUT/'BLIND'/'input',OUT/'BLIND'/'native_backend',CFG)
    print(json.dumps(s,indent=2))
