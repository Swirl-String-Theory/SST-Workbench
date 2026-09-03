
from __future__ import annotations
import sys, random, json
from pathlib import Path
from .common import read_csv, write_csv, dump_json, sha256_file

HIDDEN = {"carrier_id","family","mode_label","condition","profile","seed_name"}

def main(inp, out_csv, key_json):
    rows=read_csv(inp)
    if not rows:
        raise SystemExit("empty input")
    rng=random.Random(20260903)
    order=list(range(len(rows))); rng.shuffle(order)
    blinded=[]
    key=[]
    for anon_i, idx in enumerate(order):
        src=rows[idx]
        opaque=f"A{anon_i:06d}"
        br={"opaque_id":opaque}
        for k,v in src.items():
            if k not in HIDDEN:
                br[k]=v
        blinded.append(br)
        key.append({"opaque_id":opaque, **{k:src.get(k,"") for k in HIDDEN}})
    write_csv(out_csv, blinded)
    dump_json(key_json, {
        "format":"SST-WP-BLIND-KEY-1.0",
        "source_sha256":sha256_file(inp),
        "hidden_fields":sorted(HIDDEN),
        "mapping":key
    })
    print(json.dumps({
        "rows":len(rows),
        "blind_csv":out_csv,
        "key":key_json,
        "source_sha256":sha256_file(inp),
        "hidden_fields":sorted(HIDDEN)
    }, indent=2))

if __name__=="__main__":
    if len(sys.argv)!=4:
        raise SystemExit("usage: python -m sst_wp.action_prepare INPUT.csv BLIND.csv KEY.json")
    main(*sys.argv[1:])
