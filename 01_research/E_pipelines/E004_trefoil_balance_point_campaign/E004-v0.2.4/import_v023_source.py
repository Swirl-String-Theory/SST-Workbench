from pathlib import Path
import argparse,os,zipfile,hashlib,json,shutil
ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/"balance_design.json").read_text(encoding="utf-8"))

def safe_write(dst,data):
    dst=Path(dst);dst.parent.mkdir(parents=True,exist_ok=True)
    tmp=dst.with_name(dst.name+".importing")
    try:
        with tmp.open("wb") as f:f.write(data)
        tmp.replace(dst)
    finally:
        try:
            if tmp.exists():tmp.unlink()
        except OSError:pass

def zip_ok(p):
    try:
        with zipfile.ZipFile(p) as z:
            names=set(z.namelist())
            req=["analysis/REPORT.json","balance_design.json","out/K31__Q01_i00000.txt"]
            req += [f"out/K31__{q}_i200000.txt" for q in ["Q18","Q19","Q20"]]
            return all(x in names for x in req)
    except Exception:return False

def choose(explicit=None):
    if explicit:
        p=Path(explicit)
        if zip_ok(p):return p,"explicit"
        raise RuntimeError(f"Unusable v0.2.3 outputs zip: {p}")
    env=os.environ.get("TREFOIL_V023_SOURCE","").strip()
    if env:
        p=Path(env)
        if zip_ok(p):return p,"environment"
        raise RuntimeError(f"Unusable TREFOIL_V023_SOURCE: {p}")
    for p in sorted(ROOT.parent.glob("Trefoil_Balance_Point_Campaign_v0.2.3_outputs*.zip"),
                    key=lambda x:x.stat().st_mtime,reverse=True):
        if zip_ok(p):return p,"packed outputs"
    raise RuntimeError("No complete v0.2.3 outputs ZIP found. Set TREFOIL_V023_SOURCE.")

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--source");a=ap.parse_args()
    src,why=choose(a.source)
    print("SOURCE:",src);print("SOURCE SELECTION:",why)
    with zipfile.ZipFile(src) as z:
        # Verify the critical provenance fact: all 20 i0 coordinate exports are identical.
        hashes={}
        for i in range(1,21):
            n=f"out/K31__Q{i:02d}_i00000.txt"
            b=z.read(n);hashes[f"Q{i:02d}"]=hashlib.sha256(b).hexdigest()
        unique=set(hashes.values())
        if len(unique)!=1:
            raise RuntimeError(f"Historical i0 geometry not common: {len(unique)} unique hashes")
        common=next(iter(unique))
        expected=D["source"]["common_i0_sha256"]
        if common!=expected:
            raise RuntimeError(f"Common i0 SHA mismatch: got {common} expected {expected}")
        safe_write(ROOT/"reference/FROZEN_K31_i00000.txt",z.read("out/K31__Q01_i00000.txt"))
        for q in ["Q18","Q19","Q20"]:
            safe_write(ROOT/"reference/historical"/f"{q}_i200000.txt",z.read(f"out/K31__{q}_i200000.txt"))
        safe_write(ROOT/"reference/historical/REPORT_v023.json",z.read("analysis/REPORT.json"))
        safe_write(ROOT/"reference/historical/balance_design_v023.json",z.read("balance_design.json"))
    (ROOT/"reference/I0_PROVENANCE.json").write_text(
        json.dumps({"common_sha256":common,"hashes":hashes,"all_identical":True},indent=2)+"\n",
        encoding="utf-8")
    print("I0 PROVENANCE PASS: 20/20 historical i0 exports byte-identical")
    print("HISTORICAL OVERLAP IMPORT PASS: Q18/Q19/Q20 @ 200k")
    return 0
if __name__=="__main__":raise SystemExit(main())
