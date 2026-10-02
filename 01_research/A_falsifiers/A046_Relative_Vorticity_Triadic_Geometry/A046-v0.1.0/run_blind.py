from pathlib import Path
import json
from sst_triadic.campaign import run_blind_campaign

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parents[1] / "SST_Relative_Vorticity_Triadic_Geometry_Falsifier_v0.1.0-outputs" / "BLIND"
summary = run_blind_campaign(ROOT / "configs" / "default.json", OUT)
print(json.dumps(summary, indent=2))
