from __future__ import annotations
import hashlib, json, os
from pathlib import Path


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(path: str | Path) -> str:
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()


def canonical_json(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",",":"), ensure_ascii=False).encode("utf-8")


def write_json(path: str | Path, obj):
    path=Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


def read_json(path: str | Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def random_token(n=24) -> str:
    return os.urandom(n).hex()
