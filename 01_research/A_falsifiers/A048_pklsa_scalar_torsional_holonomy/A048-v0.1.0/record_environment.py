from pathlib import Path
import json,platform,sys
import numpy,scipy
ROOT=Path(__file__).resolve().parent
OUT=ROOT.parent/'A048_PKLSA_Scalar_Torsional_Holonomy_Falsifier_v0.1.0-outputs'/'BLIND'
info={'python':sys.version,'platform':platform.platform(),'numpy':numpy.__version__,'scipy':scipy.__version__}
(OUT/'runtime_python.json').write_text(json.dumps(info,indent=2),encoding='utf-8')
print(json.dumps(info,indent=2))
