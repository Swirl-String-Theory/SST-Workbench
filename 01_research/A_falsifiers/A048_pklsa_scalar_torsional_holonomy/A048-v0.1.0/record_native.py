from pathlib import Path
import hashlib, importlib.util, json
ROOT=Path(__file__).resolve().parent
OUT=ROOT.parent/'A048_PKLSA_Scalar_Torsional_Holonomy_Falsifier_v0.1.0-outputs'/'BLIND'
spec=importlib.util.find_spec('torsion_native')
if spec is None or not spec.origin: raise RuntimeError('torsion_native not importable')
p=Path(spec.origin).resolve()
h=hashlib.sha256(p.read_bytes()).hexdigest()
info={'module_path':str(p),'size_bytes':p.stat().st_size,'sha256':h}
(OUT/'runtime_native.json').write_text(json.dumps(info,indent=2),encoding='utf-8')
print(json.dumps(info,indent=2))
