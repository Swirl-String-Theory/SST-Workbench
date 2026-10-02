from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / "A046_Relative_Vorticity_Triadic_Geometry_Falsifier_v0.2.0-outputs"
PARENT = BASE.parent
stem = "A046_Relative_Vorticity_Triadic_Geometry_Falsifier_v0.2.0-outputs"

def zip_tree(src, dst, prefix=None):
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(src.rglob("*")):
            if p.is_file():
                rel = p.relative_to(src).as_posix()
                arc = f"{prefix}/{rel}" if prefix else rel
                zf.write(p, arcname=arc)

zip_tree(BASE / "BLIND", PARENT / f"{stem}_BLIND.zip", "BLIND")
zip_tree(BASE / "REVEALED", PARENT / f"{stem}_REVEALED.zip", "REVEALED")
zip_tree(BASE, PARENT / f"{stem}.zip", BASE.name)
print(PARENT / f"{stem}_BLIND.zip")
print(PARENT / f"{stem}_REVEALED.zip")
print(PARENT / f"{stem}.zip")
