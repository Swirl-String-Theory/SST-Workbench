from __future__ import annotations
import argparse, json, re
from pathlib import Path
from .util import read_json, canonical_json, sha256_bytes, sha256_file, write_json


def _family(name: str) -> str:
    stem=Path(name).stem
    m=re.search(r"(?:knot[._-]?)?(\d+)[._](\d+)",stem,re.I)
    return f"{m.group(1)}_{m.group(2)}" if m else stem


def reveal(outdir: str):
    out=Path(outdir)
    public=read_json(out/"BLIND_MANIFEST.json")
    seal=read_json(out/"BLIND_SEAL.json")
    for rel,expected_hash in seal["files"].items():
        got_hash=sha256_file(out/rel)
        if got_hash!=expected_hash:
            raise RuntimeError(f"blind seal mismatch for {rel}: expected {expected_hash}, got {got_hash}")
    if seal["private_mapping_commitment_sha256"]!=public["private_mapping_commitment_sha256"]:
        raise RuntimeError("blind seal/private mapping commitment mismatch")
    private=read_json(out/"_private"/"PRIVATE_MAPPING.json")
    got=sha256_bytes(canonical_json(private))
    exp=public["private_mapping_commitment_sha256"]
    if got!=exp:
        raise RuntimeError(f"private mapping commitment mismatch: expected {exp}, got {got}")
    analysis=read_json(out/"ANALYSIS_BLIND.json")
    pmap={p["pair_id"]:p for p in private["pairs"]}
    revealed=[]
    for r in analysis["pairs"]:
        p=pmap[r["pair_id"]]
        q=dict(r)
        q.update({"source_name":p["source_name"],"source_path":p["source_path"],"family":_family(p["source_name"]),
                  "A_role":p["role"]["A"],"B_role":p["role"]["B"]})
        orig_lab="A" if p["role"]["A"]=="original" else "B"
        mir_lab="B" if orig_lab=="A" else "A"
        q["pi_original"]=r[f"{orig_lab}_pi"]
        q["pi_mirror"]=r[f"{mir_lab}_pi"]
        q["xiH_original"]=r[f"{orig_lab}_xiH"]
        q["xiH_mirror"]=r[f"{mir_lab}_xiH"]
        revealed.append(q)
    payload={"format":"SST-CHIRALITY-REVEAL-1.0","commitment_verified":True,"blind_seal_verified":True,
             "commitment_sha256":got,"blind_seal_sha256":sha256_file(out/"BLIND_SEAL.json"),"pairs":revealed}
    write_json(out/"REVEALED_RESULTS.json",payload)
    md=["# SST Chirality–Helicity Transport Polarity Falsifier — Revealed","",f"Commitment verified: `{got}`","",
        "| family/source | N | a/L | original Pi | mirror Pi | original XiH | mirror XiH | blind status |",
        "|---|---:|---:|---:|---:|---:|---:|---|"]
    for r in revealed:
        md.append(f"| {r['family']} / `{r['source_name']}` | {r['resolution']} | {r['core_fraction']:.5g} | {r['pi_original']:+.4g} | {r['pi_mirror']:+.4g} | {r['xiH_original']:+.4g} | {r['xiH_mirror']:+.4g} | {r['status']} |")
    (out/"REPORT_REVEALED.md").write_text("\n".join(md)+"\n",encoding="utf-8")
    print(json.dumps({"commitment_verified":True,"blind_seal_verified":True,"n_revealed_rows":len(revealed),
                      "report":str(out/"REPORT_REVEALED.md")},indent=2))


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("outdir"); a=ap.parse_args(); reveal(a.outdir)
if __name__=="__main__": main()
