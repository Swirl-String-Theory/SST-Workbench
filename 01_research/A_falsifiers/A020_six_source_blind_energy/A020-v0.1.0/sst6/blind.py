from __future__ import annotations
import hashlib
import json
from pathlib import Path


def stable_seed(*parts: str) -> int:
    h=hashlib.sha256("\x1f".join(parts).encode("utf-8")).digest()
    return int.from_bytes(h[:8],"little") & 0x7fffffff


def canonical_hash(obj) -> str:
    b=json.dumps(obj,sort_keys=True,separators=(",",":"),default=str).encode("utf-8")
    return hashlib.sha256(b).hexdigest()


def select_blind(items, n: int | None, campaign_hash: str):
    if n is None or n<=0 or n>=len(items): return list(items)
    ranked=sorted(items,key=lambda x: hashlib.sha256((campaign_hash+":"+x.sha256).encode()).hexdigest())
    return ranked[:n]
