from pathlib import Path
import os
from sst_vortex_shear.campaign import run_blind_campaign

if os.environ.get("SST_BACKEND", "").lower() != "native":
    raise SystemExit("SST_BACKEND=native is required")
ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / "A049_Isotropic_Euler_Vortex_Shear_Modulus_Falsifier_v0.4.1-outputs"
run_blind_campaign(ROOT / "configs" / "default.json", BASE / "BLIND" / "native_backend")
