from __future__ import annotations
from pathlib import Path
import json, shutil

ROOT = Path(__file__).resolve().parent
CFG = json.loads((ROOT/"campaign_config.json").read_text(encoding="utf-8"))
RES = ROOT/"seeds/resolved_manifest.json"

def yn(v):
    return "on" if v else "off"

def relax_lines():
    r = CFG["relaxation"]
    # IMPORTANT: These forms are copied from the user's known-working
    # build_knot_0.1.kpc. Do not "normalize" them.
    return [
        "refine nbeads 300",
        f"mode {r['mode']}",
        "",
        "centre",
        f"fitto mindist {CFG['fitto_mindist']}",
        "",
        f"collision {r['collision']}",
        f"close = {r['close']:.1f}",
        f"max-dr = {r['max-dr']:.2f}",
        "",
        f"mechforce = {yn(r['mechforce'])}",
        f"elecforce = {yn(r['elecforce'])}",
        f"bendforce = {yn(r['bendforce'])}",
        f"bencon = {r['bencon']:.1f}",
        "",
        f"stusplit = {r['stusplit']}",
        f"dstep = {r['dstep']}",
        "",
        f"bradius = {r['bradius']:.1f}",
        f"cradius = {r['cradius']:.2f}",
        "",
        f"energy model {r['energy_model']}",
        "energy",
    ]

def checkpoint(cid, it):
    tag = f"i{it:05d}"
    out = "__CAMPAIGN_ROOT__/out"
    lines = [
        f"echo CHECKPOINT {cid}_{tag}",
        "safe",
        "dowker",
        "lnknum",
        "length",
        "distance",
        "angle",
        "acn",
        f"save {out}/{cid}_{tag}.k float",
        f"coords {out}/{cid}_{tag}.txt",
    ]
    return lines

def main():
    if not RES.is_file():
        raise SystemExit(
            "ERROR: seeds/resolved_manifest.json missing; "
            "run run_10_generate_seeds.cmd first."
        )
    d = json.loads(RES.read_text(encoding="utf-8"))
    rows = [r for r in d["seeds"] if r["safety_pass"]]

    kd = ROOT/"kpc/full"
    if kd.exists():
        shutil.rmtree(kd)
    kd.mkdir(parents=True)

    index = []
    for row in rows:
        cid = f"{row['seed_id']}_{row['family']}"
        lines = [
            "% AUTO-GENERATED Trefoil Seed Campaign v0.1.3",
            f"% candidate={cid}",
            "reset all",
            f"load __CAMPAIGN_ROOT__/seeds/{row['file']}",
            *relax_lines(),
            "",
            *checkpoint(cid, 0),
            "",
            "ago 1000",
            *checkpoint(cid, 1000),
            "",
            "ago 3000",
            *checkpoint(cid, 4000),
            "",
            "ago 6000",
            *checkpoint(cid, 10000),
            "stop",
        ]
        p = kd/f"{cid}.kpc"
        p.write_text("\n".join(lines)+"\n", encoding="utf-8", newline="\n")
        index.append({
            "candidate": cid,
            "script": str(p.relative_to(ROOT)),
            "seed_file": row["file"]
        })

    (kd/"index.json").write_text(json.dumps(index, indent=2)+"\n", encoding="utf-8")
    print(f"[KPC] generated {len(index)} full relaxation scripts")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
