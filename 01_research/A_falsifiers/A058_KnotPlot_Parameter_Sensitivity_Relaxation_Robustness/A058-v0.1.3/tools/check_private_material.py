from __future__ import annotations
from pathlib import Path
import hashlib, sys
ROOT=Path(__file__).resolve().parents[1]
EXPECTED=("private/OPAQUE_ID_KEY.bin","private/REVEAL_NONCE.bin")
def main():
    bad=[]
    for rel in EXPECTED:
        p=ROOT/rel
        if not p.is_file(): bad.append(f"missing: {rel}"); continue
        data=p.read_bytes()
        if len(data)!=32: bad.append(f"invalid size: {rel}: {len(data)} bytes (expected 32)")
        else: print(f"PRIVATE MATERIAL OK: {rel} bytes=32 sha256={hashlib.sha256(data).hexdigest()}")
    if bad:
        print("PRIVATE MATERIAL PREFLIGHT FAILED", file=sys.stderr)
        for x in bad: print(" - "+x, file=sys.stderr)
        return 2
    return 0
if __name__=="__main__": raise SystemExit(main())
