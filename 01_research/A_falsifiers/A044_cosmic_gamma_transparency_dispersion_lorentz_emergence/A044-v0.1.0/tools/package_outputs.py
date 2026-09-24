\
from pathlib import Path
import zipfile, json, hashlib
NAME="SST_Cosmic_Gamma_Transparency_Dispersion_Lorentz_Emergence_Falsifier"
VER="v0.1.0"
root=Path.cwd(); out=root/f"{NAME}_{VER}-outputs"
if not (out/"blind").exists(): raise SystemExit("blind outputs missing")
def zip_tree(target, paths):
    target=Path(target)
    with zipfile.ZipFile(target,"w",zipfile.ZIP_DEFLATED) as z:
        for base in paths:
            base=Path(base)
            if base.is_file(): z.write(base,base.name)
            else:
                for p in base.rglob("*"):
                    if p.is_file(): z.write(p,p.relative_to(root))
    return hashlib.sha256(target.read_bytes()).hexdigest()
blind_zip=root.parent/f"{NAME}_{VER}-outputs_BLIND.zip"
sha_b=zip_tree(blind_zip,[out/"blind"])
print(f"BLIND: {blind_zip} sha256={sha_b}")
if (out/"revealed").exists():
    revealed_zip=root.parent/f"{NAME}_{VER}-outputs_REVEALED.zip"
    sha_r=zip_tree(revealed_zip,[out/"blind",out/"revealed"])
    print(f"REVEALED: {revealed_zip} sha256={sha_r}")
