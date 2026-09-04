from __future__ import annotations
from pathlib import Path
import zipfile, sys
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(".")
folders=sorted([p for p in root.glob("results_*_blind_*") if p.is_dir()],key=lambda p:p.stat().st_mtime)
if not folders: raise SystemExit("No results_*_blind_* folder found")
p=folders[-1]; z=p.with_suffix(".zip")
with zipfile.ZipFile(z,"w",zipfile.ZIP_DEFLATED) as zz:
    for f in p.rglob("*"):
        if f.is_file(): zz.write(f,f.relative_to(p.parent))
print(z)
