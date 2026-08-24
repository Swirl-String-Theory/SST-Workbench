from __future__ import annotations
from pathlib import Path
import json, sys

ROOT=Path(__file__).resolve().parent
PUB=ROOT/"prepared/selected/PUBLIC_ENTRIES.json"
UM=ROOT/"tbk_outputs/v048/01_screen_fp64/unblind_manifest.json"

def main():
    if not PUB.is_file():
        print("ERROR: selected PUBLIC_ENTRIES missing; run prepare first.")
        return 2
    if not UM.is_file():
        print("ERROR: existing v0.4.8 screen unblind_manifest missing.")
        return 3

    public=json.loads(PUB.read_text(encoding="utf-8"))
    target=json.loads(UM.read_text(encoding="utf-8"))
    expected={r["source"]:r["raw_sha256"] for r in public}
    actual={v["source"]:v["sha256"] for v in target.values()}

    if expected!=actual:
        print("EXISTING SCREEN LOCK FAIL")
        print("Expected selected sources:",sorted(expected))
        print("Actual screen sources   :",sorted(actual))
        only_e=sorted(set(expected)-set(actual))
        only_a=sorted(set(actual)-set(expected))
        mismatch=sorted(k for k in set(expected)&set(actual) if expected[k]!=actual[k])
        if only_e: print("Missing from screen:",only_e)
        if only_a: print("Unexpected in screen:",only_a)
        if mismatch: print("Hash mismatches:",mismatch)
        return 4

    print(f"EXISTING SCREEN LOCK PASS: {len(expected)} blinded inputs match byte-for-byte.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
