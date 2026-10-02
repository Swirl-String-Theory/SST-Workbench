from __future__ import annotations
import argparse,hashlib,secrets,shutil,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from sst_reciprocal.io import dump_json,load_json,sha256_file

def hid(salt,text,prefix): return f"{prefix}_{hashlib.sha256((salt+'|'+text).encode()).hexdigest()[:12].upper()}"

def main():
    ap=argparse.ArgumentParser(description="Freeze and blind Maxwell-5 SST campaign.")
    ap.add_argument("manifest"); ap.add_argument("--out",required=True); ap.add_argument("--private-key",required=True); ap.add_argument("--overwrite",action="store_true")
    args=ap.parse_args(); manifest_path=Path(args.manifest).resolve(); src=load_json(manifest_path); manifest_dir=manifest_path.parent; out=Path(args.out).resolve()
    if out.exists() and args.overwrite: shutil.rmtree(out)
    if out.exists() and any(out.iterdir()): raise RuntimeError(f"Blind output already exists and is non-empty: {out}. Use --overwrite explicitly.")
    data=out/"data"; data.mkdir(parents=True,exist_ok=True); salt=secrets.token_hex(32)
    blind_cases=[]; key={"salt":salt,"package":src.get("package"),"preset":src.get("preset"),"cases":{},"groups":{}}
    for c in src.get("cases",[]):
        p=Path(c["path"]).expanduser(); p=(manifest_dir/p).resolve() if not p.is_absolute() else p.resolve()
        if not p.exists(): raise FileNotFoundError(p)
        digest=sha256_file(p); cid=hid(salt,digest+"|"+str(p),"CASE"); group=str(c.get("group",p.stem)); gid=hid(salt,group,"GROUP"); dst=data/(cid+(p.suffix.lower() or ".txt")); shutil.copy2(p,dst)
        entry={"case_id":cid,"group_id":gid,"path":str(Path("data")/dst.name),"sha256":digest,"resolution":c.get("resolution"),"component_counts":c.get("component_counts"),
               "radius":c.get("radius"),"source_role":c.get("source_role","unknown"),"geometry_status":c.get("geometry_status","unknown"),"geometry_qc_pass":bool(c.get("geometry_qc_pass",True)),"complete_mechanical_model":bool(c.get("complete_mechanical_model",False)),"physical_force_scale_N":c.get("physical_force_scale_N")}
        for field,suffix in (("contact_sidecar","contacts.csv"),("kink_sidecar","kinks.csv")):
            if c.get(field):
                sp=Path(c[field]).expanduser(); sp=(manifest_dir/sp).resolve() if not sp.is_absolute() else sp.resolve(); sd=data/f"{cid}.{suffix}"; shutil.copy2(sp,sd); entry[field]=str(Path("data")/sd.name); entry[field+"_sha256"]=sha256_file(sp)
        blind_cases.append(entry)
        key["cases"][cid]={"original_path":str(p),"original_label":c.get("label",p.name),"group":group,"group_id":gid,"private_metrics":c.get("private_metrics",{})}
        key["groups"][gid]=group
    dump_json(out/"blind_manifest.json",{"blind":True,"package":src.get("package"),"preset":src.get("preset"),"cases":blind_cases,"preregistration":src.get("preregistration",{})})
    dump_json(args.private_key,key)
    print(f"[5_Maxwell] prepared {len(blind_cases)} blinded cases -> {out}")
    print(f"[5_Maxwell] PRIVATE map -> {Path(args.private_key).resolve()}")

if __name__=="__main__": main()
