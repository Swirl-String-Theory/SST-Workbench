from __future__ import annotations
import argparse, json, re
from pathlib import Path
from .util import read_json, write_json, canonical_json, sha256_bytes, sha256_file, private_key_path


def _family(name:str)->str:
    stem=Path(name).stem
    m=re.search(r"torus[^0-9]*(\d+)[._-](\d+)",stem,re.I)
    if m: return f"T({m.group(1)},{m.group(2)})"
    m=re.search(r"(?:knot[^0-9]*)?(\d+)[._-](\d+)",stem,re.I)
    if m: return f"{m.group(1)}_{m.group(2)}"
    return stem


def reveal(outdir:str):
    out=Path(outdir); public=read_json(out/"BLIND_MANIFEST.json"); seal=read_json(out/"BLIND_SEAL.json")
    for rel,expected in seal["files"].items():
        got=sha256_file(out/rel)
        if got!=expected: raise RuntimeError(f"blind seal mismatch for {rel}: expected {expected}, got {got}")
    if seal["private_mapping_commitment_sha256"]!=public["private_mapping_commitment_sha256"]: raise RuntimeError("seal/manifest commitment mismatch")
    if seal["private_key_id"]!=public["private_key_id"]: raise RuntimeError("seal/manifest key-id mismatch")
    keyfile=private_key_path(public["private_key_id"])
    if not keyfile.exists(): raise FileNotFoundError(f"Reveal key not found: {keyfile}")
    private=read_json(keyfile); got=sha256_bytes(canonical_json(private)); exp=public["private_mapping_commitment_sha256"]
    if got!=exp: raise RuntimeError(f"private mapping commitment mismatch: expected {exp}, got {got}")
    analysis=read_json(out/"ANALYSIS_BLIND.json"); pmap={p["pair_id"]:p for p in private["pairs"]}; revealed=[]
    for r in analysis["pairs"]:
        p=pmap[r["pair_id"]]; q=dict(r); q.update({"source_name":p["source_name"],"source_path":p["source_path"],"family":_family(p["source_name"]),
            "component_parse":p["component_parse"],"source_n_components":p["n_components"],"A_role":p["role"]["A"],"B_role":p["role"]["B"]})
        olab="A" if p["role"]["A"]=="original" else "B"; mlab="B" if olab=="A" else "A"
        q["pi_original"]=r[f"{olab}_pi"]; q["pi_mirror"]=r[f"{mlab}_pi"]; q["xiH_original"]=r[f"{olab}_xiH"]; q["xiH_mirror"]=r[f"{mlab}_xiH"]
        q["gauss_original"]=r[f"{olab}_gauss"]; q["gauss_mirror"]=r[f"{mlab}_gauss"]
        revealed.append(q)
    single=[r for r in revealed if r["source_n_components"]==1]; multi=[r for r in revealed if r["source_n_components"]>1]
    payload={"format":"SST-CHIRALITY-REVEAL-2.0","commitment_verified":True,"blind_seal_verified":True,"commitment_sha256":got,
             "blind_seal_sha256":sha256_file(out/"BLIND_SEAL.json"),"private_key_id":public["private_key_id"],
             "summary":{"rows":len(revealed),"single_component_rows":len(single),"multi_component_rows":len(multi),
                        "single_component_pass_rows":sum(r["status"].startswith("PASS_SINGLE") for r in single),"multi_component_pass_rows":sum(r["status"].startswith("PASS_MULTI") for r in multi)},
             "pairs":revealed}
    write_json(out/"REVEALED_RESULTS.json",payload); write_json(out/"REVEAL_MAPPING.json",private)
    md=["# SST Chirality–Helicity Transport Polarity Falsifier v0.2.0 — Revealed","",f"Commitment verified: `{got}`",f"Blind seal verified: `{payload['blind_seal_sha256']}`","",
        "| family/source | C | N | a/L | original Pi | mirror Pi | original XiH | RE max | shape drift | blind status |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    for r in revealed:
        md.append(f"| {r['family']} / `{r['source_name']}` | {r['source_n_components']} | {r['resolution_requested']} | {r['core_fraction']:.5g} | {r['pi_original']:+.4g} | {r['pi_mirror']:+.4g} | {r['xiH_original']:+.4g} | {r['relative_equilibrium_max']:.3g} | {r['shape_drift_max']:.3g} | {r['status']} |")
    md += ["","## Source parser provenance","","Multi-component sources are represented as separate closed filaments. No connector segment is inserted between components.",""]
    for p in private["pairs"]: md.append(f"- `{p['pair_id']}` → `{p['source_name']}`: {p['n_components']} component(s), parser `{p['component_parse'].get('component_parse')}`")
    (out/"REPORT_REVEALED.md").write_text("\n".join(md)+"\n",encoding="utf-8")
    print(json.dumps({"commitment_verified":True,"blind_seal_verified":True,"n_revealed_rows":len(revealed),"report":str(out/"REPORT_REVEALED.md")},indent=2))


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("outdir"); a=ap.parse_args(); reveal(a.outdir)
if __name__=="__main__": main()
