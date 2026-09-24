from __future__ import annotations
import hashlib, json, platform, sys, re
from pathlib import Path
import numpy as np

DENYLIST = {
    "alpha": r"(?<![A-Za-z0-9_])alpha(?![A-Za-z0-9_])",
    "v_circlearrow": r"v[_\\]?circlearrow",
    "gamma": r"(?<![A-Za-z0-9_])gamma(?![A-Za-z0-9_])",
    "circulation": r"(?<![A-Za-z0-9_])circulation(?![A-Za-z0-9_])",
    "rho_core": r"rho[_\\]?core",
    "rho_f": r"rho[_\\]?f(?![A-Za-z0-9_])",
    "r_c": r"(?<![A-Za-z0-9_])r_c(?![A-Za-z0-9_])",
}



def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def anon_id(record: dict, salt: str) -> str:
    h = hashlib.blake2b((salt+canonical_json(record)).encode(), digest_size=8).hexdigest()
    return "A"+h.upper()


def environment_manifest() -> dict:
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
    }


def source_leakage_audit(root: Path) -> dict:
    hits = []
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() in {".zip", ".png", ".jpg", ".pyc"}:
            continue
        if "private_reveal" in p.parts or "-outputs" in str(p.parent) or p.name == "provenance.py":
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore").lower()
        except Exception:
            continue
        for tok, pattern in DENYLIST.items():
            if re.search(pattern, txt, flags=re.IGNORECASE):
                hits.append({"file": str(p.relative_to(root)), "token": tok})
    return {"pass": len(hits)==0, "hits": hits, "denylist": list(DENYLIST)}
