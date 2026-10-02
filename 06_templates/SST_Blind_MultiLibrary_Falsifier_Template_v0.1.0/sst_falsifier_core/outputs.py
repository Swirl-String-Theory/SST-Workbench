from __future__ import annotations
from pathlib import Path
import json, zipfile, shutil
from .util import write_json, sha256_file
from .blind import scan_tree

def output_root(project_dir,name,version): return Path(project_dir)/f"{name}_{version}-outputs"

def pack_tree(root,zip_path,exclude_names=("private","revealed","reveal_private")):
    root=Path(root); zip_path=Path(zip_path); zip_path.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(zip_path,"w",zipfile.ZIP_DEFLATED) as z:
        for p in sorted(root.rglob("*")):
            if not p.is_file(): continue
            if any(x.lower() in exclude_names for x in p.parts): continue
            z.write(p,p.relative_to(root.parent))
    return {"zip":str(zip_path),"sha256":sha256_file(zip_path)}

def pack_blind(root,zip_path,forbidden=()):
    hits=scan_tree(root,forbidden=forbidden) if forbidden else []
    if hits: raise RuntimeError(f"blind contamination: {hits[:10]}")
    return pack_tree(root,zip_path)

def pack_revealed(root,zip_path): return pack_tree(root,zip_path,exclude_names=("private","reveal_private"))
