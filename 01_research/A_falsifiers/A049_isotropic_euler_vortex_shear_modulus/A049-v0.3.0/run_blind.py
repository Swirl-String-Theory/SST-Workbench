from pathlib import Path
from sst_vortex_shear.campaign import run_blind_campaign

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / "A049_Isotropic_Euler_Vortex_Shear_Modulus_Falsifier_v0.3.0-outputs"
run_blind_campaign(ROOT / "configs" / "default.json", BASE / "BLIND" / "python_backend")
