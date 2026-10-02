from pathlib import Path
import json
from sst_triadic.campaign import run_blind_campaign

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "A046_Relative_Vorticity_Triadic_Geometry_Falsifier_v0.2.0-outputs" / "BLIND" / "python_backend"
summary = run_blind_campaign(ROOT / "configs" / "default.json", OUT)
print(json.dumps(summary, indent=2))
