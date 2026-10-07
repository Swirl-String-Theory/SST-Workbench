from pathlib import Path
import hashlib
from .util import sha256_file

def scan_tree(root, forbidden, suffixes=(".py",".json",".toml",".cmd",".cpp",".h")):
    root=Path(root); hits=[]; terms=[str(t).lower() for t in forbidden]
    skip={'PRIVATE','REVEALED'}
    for p in root.rglob('*'):
        if not p.is_file() or p.suffix.lower() not in suffixes or any(x in skip for x in p.parts): continue
        txt=p.read_text(encoding='utf-8',errors='ignore').lower()
        for term in terms:
            if term in txt: hits.append({"path":p.relative_to(root).as_posix(),"term":term})
    return hits

def opaque_id(seed, public_salt='A056-v0.1.0', n=16):
    return hashlib.sha256((public_salt+'|'+seed).encode()).hexdigest()[:n].upper()

def verify_reveal(path, commitment_path):
    expected=Path(commitment_path).read_text(encoding='utf-8').strip().split()[0]
    actual=sha256_file(path)
    return actual==expected, expected, actual
