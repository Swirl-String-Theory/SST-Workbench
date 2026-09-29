from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / "A049_Isotropic_Euler_Vortex_Shear_Modulus_Falsifier_v0.4.1-outputs"
PARENT = ROOT.parent
stem = BASE.name

for suffix, src in [
    ("_BLIND", BASE / "BLIND"),
    ("_REVEALED", BASE / "REVEALED"),
    ("", BASE),
]:
    target = PARENT / f"{stem}{suffix}"
    zip_path = Path(str(target) + ".zip")
    if zip_path.exists():
        zip_path.unlink()
    shutil.make_archive(str(target), "zip", root_dir=src.parent, base_dir=src.name)
    print(zip_path)
