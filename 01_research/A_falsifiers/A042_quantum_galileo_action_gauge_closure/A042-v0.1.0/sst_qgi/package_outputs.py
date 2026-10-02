from __future__ import annotations
from pathlib import Path
import zipfile

def _zip_tree(zip_path: Path, roots: list[Path], base: Path):
    with zipfile.ZipFile(zip_path,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for root in roots:
            if not root.exists(): continue
            if root.is_file():
                z.write(root,root.relative_to(base))
            else:
                for p in sorted(root.rglob("*")):
                    if p.is_file():
                        z.write(p,p.relative_to(base))

def package(project_root: Path, project_name: str):
    out=project_root/f"{project_name}-outputs"
    parent=project_root.parent
    blind_zip=parent/f"{project_name}-outputs_BLIND.zip"
    revealed_zip=parent/f"{project_name}-outputs_REVEALED.zip"

    # BLIND: public blind artifacts only. Never private/, never revealed/.
    _zip_tree(blind_zip,[out/"blind"],project_root)

    # REVEALED: public blind + revealed artifacts. Still excludes private HMAC secret.
    _zip_tree(revealed_zip,[out/"blind",out/"revealed"],project_root)
    return blind_zip,revealed_zip
