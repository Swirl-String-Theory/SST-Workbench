from __future__ import annotations
from pathlib import Path
import hashlib, json, re
from .util import sha256_file

DEFAULT_FORBIDDEN=()

def scan_tree(root, forbidden=DEFAULT_FORBIDDEN, suffixes=(".py",".json",".md",".txt",".toml",".cmd",".cpp",".h")):
    root=Path(root); hits=[]
    terms=[t.lower() for t in forbidden]
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in suffixes: continue
        if any(x.lower() in {"private","revealed","reveal_private"} for x in p.parts): continue
        try: text=p.read_text(encoding="utf-8",errors="ignore").lower()
        except Exception: continue
        for term in terms:
            if term in text: hits.append({"path":p.relative_to(root).as_posix(),"term":term})
    return hits

def reveal_commitment(path): return sha256_file(path)

def verify_reveal(path, commitment_path):
    expected=Path(commitment_path).read_text(encoding="utf-8").strip().split()[0]
    actual=sha256_file(path)
    return actual==expected, expected, actual

def opaque_id(seed: str, public_salt: str, n=16):
    return hashlib.sha256((public_salt+"|"+seed).encode()).hexdigest()[:n].upper()
