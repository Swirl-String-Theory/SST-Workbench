from __future__ import annotations
import argparse, hashlib, json, os, secrets, shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sst_reciprocal.io import dump_json, load_json, sha256_file


def hid(salt: str, text: str, prefix: str) -> str:
    h=hashlib.sha256((salt+"|"+text).encode()).hexdigest()[:12].upper()
    return f"{prefix}_{h}"


def main():
    ap=argparse.ArgumentParser(description="Freeze and blind an SST relaxed-knot/contact campaign.")
    ap.add_argument("manifest", help="private input datasets manifest JSON")
    ap.add_argument("--out", default="blind_campaign")
    ap.add_argument("--private-key", default="private_blind_key.json")
    ap.add_argument("--copy", action="store_true", help="copy inputs into blind campaign (recommended; default is also copy for portability)")
    args=ap.parse_args()
    manifest_path=Path(args.manifest).expanduser().resolve()
    src=load_json(manifest_path); manifest_dir=manifest_path.parent
    out=Path(args.out); data=out/"data"; data.mkdir(parents=True,exist_ok=True)
    salt=secrets.token_hex(32)
    blind_cases=[]; key={"salt":salt,"cases":{},"groups":{}}
    for c in src.get("cases",[]):
        p=Path(c["path"]).expanduser()
        if not p.is_absolute(): p=manifest_dir/p
        p=p.resolve()
        if not p.exists(): raise FileNotFoundError(p)
        digest=sha256_file(p)
        cid=hid(salt,digest+"|"+str(p),"CASE")
        group=str(c.get("group",p.stem)); gid=hid(salt,group,"GROUP")
        ext=p.suffix.lower() or ".xyz"; dst=data/(cid+ext)
        shutil.copy2(p,dst)
        entry={
            "case_id":cid,"group_id":gid,"path":str(Path("data")/dst.name),"sha256":digest,
            "resolution":c.get("resolution"),"radius":c.get("radius"),"source_role":c.get("source_role","unknown"),
            "geometry_status":c.get("geometry_status","unknown"),
            "complete_mechanical_model":bool(c.get("complete_mechanical_model",False)),
            "physical_force_scale_N":c.get("physical_force_scale_N"),
        }
        for field,suffix in (("contact_sidecar","contacts.csv"),("kink_sidecar","kinks.csv")):
            if c.get(field):
                sp=Path(c[field]).expanduser()
                if not sp.is_absolute(): sp=manifest_dir/sp
                sp=sp.resolve()
                if not sp.exists(): raise FileNotFoundError(sp)
                sd=data/f"{cid}.{suffix}"; shutil.copy2(sp,sd)
                entry[field]=str(Path("data")/sd.name)
                entry[field+"_sha256"]=sha256_file(sp)
        blind_cases.append(entry)
        key["cases"][cid]={"original_path":str(p),"original_label":c.get("label",p.name),"group":group,"group_id":gid}
        key["groups"][gid]=group
    prereg=src.get("preregistration",{})
    dump_json(out/"blind_manifest.json",{"blind":True,"cases":blind_cases,"preregistration":prereg})
    dump_json(args.private_key,key)
    print(f"Prepared {len(blind_cases)} blinded cases in {out}")
    print(f"PRIVATE mapping written separately to {args.private_key}; do not place it in the run directory.")

if __name__=="__main__": main()
