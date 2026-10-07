from __future__ import annotations
from pathlib import Path
import zipfile, hashlib

def default_output_dir(package_root: Path):
    root=Path(package_root).resolve(); return root/f"{root.name}-outputs"

def ensure_layout(root):
    root=Path(root); (root/'BLIND').mkdir(parents=True,exist_ok=True); return root

def pack_outputs(root, prefix, destination=None):
    root=Path(root); dstbase=Path(destination) if destination else root.parent
    made=[]
    def pack(dst,sub=None):
        with zipfile.ZipFile(dst,'w',zipfile.ZIP_DEFLATED) as z:
            base=root/sub if sub else root
            if not base.exists(): return None
            for f in sorted(base.rglob('*')):
                if f.is_file(): z.write(f,f.relative_to(root.parent))
        h=hashlib.sha256(dst.read_bytes()).hexdigest()
        Path(str(dst)+'.sha256').write_text(h+'  '+dst.name+'\n',encoding='utf-8')
        made.append(str(dst)); return dst
    pack(dstbase/f'{prefix}-outputs_BLIND.zip','BLIND')
    if (root/'REVEALED').exists(): pack(dstbase/f'{prefix}-outputs_REVEALED.zip','REVEALED')
    pack(dstbase/f'{prefix}-outputs.zip')
    return made
