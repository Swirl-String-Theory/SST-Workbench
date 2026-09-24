from pathlib import Path
from sst_triadic.campaign import seal_directory

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "A046_Relative_Vorticity_Triadic_Geometry_Falsifier_v0.2.0-outputs" / "BLIND"
print(seal_directory(OUT))
