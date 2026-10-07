from __future__ import annotations
from pathlib import Path
import hashlib

DEFAULT_SUFFIXES=(".py",".json",".md",".txt",".toml",".cmd",".cpp",".h",".tex",".yaml",".yml")
PRIVATE_PARTS={"private","revealed","reveal_private"}

def scan_tree(root, forbidden=(), suffixes=DEFAULT_SUFFIXES):
    root=Path(root); hits=[]; terms=[t.lower() for t in forbidden]
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in suffixes: continue
        if any(x.lower() in PRIVATE_PARTS for x in p.parts): continue
        try: txt=p.read_text(encoding="utf-8",errors="ignore").lower()
        except Exception: continue
        for term in terms:
            if term in txt: hits.append({"path":p.relative_to(root).as_posix(),"term":term})
    return hits

def sha256_file(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

def reveal_commitment(path): return sha256_file(path)

def verify_reveal(path, commitment_path):
    expected=Path(commitment_path).read_text(encoding="utf-8").strip().split()[0]
    actual=sha256_file(path)
    return actual==expected, expected, actual

def opaque_id(seed: str, public_salt: str, n=16):
    return hashlib.sha256((public_salt+"|"+seed).encode()).hexdigest()[:n].upper()
