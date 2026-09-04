from __future__ import annotations
import hashlib, secrets, json
from pathlib import Path

def new_salt(): return secrets.token_hex(32)
def blind_id(path: Path, salt: str, prefix="K"):
    h = hashlib.sha256((salt + "|" + str(path.resolve())).encode()).hexdigest()[:12].upper()
    return f"{prefix}_{h}"
def write_private_manifest(path: Path, salt: str, mapping: dict):
    path.write_text(json.dumps({"salt": salt, "mapping": mapping}, indent=2), encoding="utf-8")
def read_private_manifest(path: Path): return json.loads(path.read_text(encoding="utf-8"))
