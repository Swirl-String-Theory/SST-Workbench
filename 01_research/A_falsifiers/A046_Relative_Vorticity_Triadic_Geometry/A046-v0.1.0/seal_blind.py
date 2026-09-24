from pathlib import Path
from sst_triadic.campaign import seal_directory

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parents[1] / "SST_Relative_Vorticity_Triadic_Geometry_Falsifier_v0.1.0-outputs" / "BLIND"
print(seal_directory(OUT))
