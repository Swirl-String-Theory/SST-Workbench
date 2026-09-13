from __future__ import annotations
import hashlib, json, secrets, math
from pathlib import Path


def _json_safe(obj):
    if isinstance(obj, float) and not math.isfinite(obj): return None
    if isinstance(obj, dict): return {k:_json_safe(v) for k,v in obj.items()}
    if isinstance(obj, (list,tuple)): return [_json_safe(v) for v in obj]
    return obj

def canonical_json(obj) -> bytes:
    return json.dumps(_json_safe(obj), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: str | Path, obj) -> None:
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(_json_safe(obj), indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def read_json(path: str | Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def random_token(nbytes: int = 24) -> str:
    return secrets.token_hex(nbytes)


def package_root() -> Path:
    return Path(__file__).resolve().parent.parent


def private_key_path(key_id: str) -> Path:
    return package_root() / "private_reveal_keys" / f"{key_id}.json"
