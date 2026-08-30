from __future__ import annotations
from pathlib import Path
import argparse,os,shutil,zipfile,json,glob

ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/"balance_design.json").read_text(encoding="utf-8"))
RESUME=int(D["continuation"]["resume_from"])

def rid_for(s):
    return f"K31__{s['id']}"

def required_folder_files(src):
    base=src/"out" if (src/"out").is_dir() else src
    req=[]
    for s in D["settings"]:
        rid=rid_for(s)
        req += [
            base/f"{rid}_i00000.txt",
            base/f"{rid}_i30000.txt",
            base/f"{rid}_i40000.txt",
            base/f"{rid}_i50000.txt",
            base/f"{rid}_i60000.txt",
            base/f"{rid}_i60000.k",
        ]
    return req

def folder_is_usable(src):
    if not src.is_dir():
        return False
    try:
        return all(p.is_file() and p.stat().st_size>0 for p in required_folder_files(src))
    except OSError:
        return False

def zip_is_usable(src):
    if not src.is_file():
        return False
    try:
        with zipfile.ZipFile(src) as z:
            names=set(z.namelist())
            for s in D["settings"]:
                rid=rid_for(s)
                for n in [
                    f"out/{rid}_i00000.txt",
                    f"out/{rid}_i30000.txt",
                    f"out/{rid}_i40000.txt",
                    f"out/{rid}_i50000.txt",
                    f"out/{rid}_i60000.txt",
                    f"out/{rid}_i60000.k",
                ]:
                    if n not in names:
                        return False
        return True
    except (OSError,zipfile.BadZipFile):
        return False

def auto_candidates():
    env=os.environ.get("TREFOIL_V021_SOURCE","").strip()
    if env:
        yield Path(env),"environment override"

    # Prefer packed repaired outputs over a mutable/stale working folder.
    patterns=[
        "Trefoil_Balance_Point_Campaign_v0.2.1_outputs*.zip",
        "Trefoil_Balance_Point_Campaign_v0.2.1*_outputs*.zip",
    ]
    seen=set()
    for pat in patterns:
        for p in sorted(ROOT.parent.glob(pat), key=lambda x:x.stat().st_mtime if x.exists() else 0, reverse=True):
            try:key=str(p.resolve()).lower()
            except OSError:key=str(p).lower()
            if key not in seen:
                seen.add(key)
                yield p,"packed outputs"

    yield ROOT.parent/"Trefoil_Balance_Point_Campaign_v0.2.1","sibling working folder"

def choose_source(explicit=None):
    if explicit:
        p=Path(explicit)
        ok=folder_is_usable(p) if p.is_dir() else zip_is_usable(p)
        if not ok:
            raise RuntimeError(f"Explicit source is incomplete/unusable: {p}")
        return p,"explicit --source"

    rejected=[]
    for p,why in auto_candidates():
        if p.is_dir():
            ok=folder_is_usable(p)
        else:
            ok=zip_is_usable(p)
        if ok:
            return p,why
        if p.exists():
            rejected.append(f"{p} ({why}: incomplete/unusable)")
    msg="No complete repaired v0.2.1 source found."
    if rejected:
        msg+=" Rejected: "+"; ".join(rejected)
    msg+=" Set TREFOIL_V021_SOURCE to the repaired outputs ZIP or folder."
    raise RuntimeError(msg)

def safe_copy_file(src,dst):
    """Copy bytes without Windows CopyFile2/copy2 metadata semantics."""
    src=Path(src);dst=Path(dst)
    dst.parent.mkdir(parents=True,exist_ok=True)
    # Write to a temporary file in destination dir, then atomic-ish replace.
    tmp=dst.with_name(dst.name+".importing")
    try:
        with src.open("rb") as fi,tmp.open("wb") as fo:
            shutil.copyfileobj(fi,fo,length=1024*1024)
        tmp.replace(dst)
    finally:
        try:
            if tmp.exists(): tmp.unlink()
        except OSError:
            pass

def safe_write_bytes(dst,data):
    dst=Path(dst);dst.parent.mkdir(parents=True,exist_ok=True)
    tmp=dst.with_name(dst.name+".importing")
    try:
        with tmp.open("wb") as f:
            f.write(data)
        tmp.replace(dst)
    finally:
        try:
            if tmp.exists(): tmp.unlink()
        except OSError:
            pass

def import_folder(src):
    base=src/"out" if (src/"out").is_dir() else src
    copied=0
    for s in D["settings"]:
        rid=rid_for(s)
        # Import all available historical coordinate checkpoints <=60k.
        files=[]
        for p in base.glob(f"{rid}_i*.txt"):
            m=__import__("re").search(r"_i(\d+)\.txt$",p.name)
            if m and int(m.group(1))<=RESUME:
                files.append(p)
        files.sort()
        for p in files:
            safe_copy_file(p,ROOT/"out"/p.name)
            copied+=1
        kp=base/f"{rid}_i60000.k"
        if not kp.is_file() or kp.stat().st_size==0:
            raise FileNotFoundError(f"Missing required 60k state: {kp}")
        safe_copy_file(kp,ROOT/"out"/kp.name)
        copied+=1

    for rel in ["analysis/REPORT.json","analysis/RESUME_CONTINUITY.json"]:
        p=src/rel
        if p.is_file():
            safe_copy_file(p,ROOT/"reference"/("imported_v021_"+p.name))
    return copied

def import_zip(src):
    copied=0
    with zipfile.ZipFile(src) as z:
        names=set(z.namelist())
        for s in D["settings"]:
            rid=rid_for(s)
            candidates=[]
            for n in names:
                if not n.startswith(f"out/{rid}_i") or not n.endswith(".txt"):
                    continue
                m=__import__("re").search(r"_i(\d+)\.txt$",n)
                if m and int(m.group(1))<=RESUME:
                    candidates.append(n)
            for n in sorted(candidates):
                safe_write_bytes(ROOT/"out"/Path(n).name,z.read(n))
                copied+=1

            kn=f"out/{rid}_i60000.k"
            if kn not in names:
                raise RuntimeError(f"Missing required state in ZIP: {kn}")
            safe_write_bytes(ROOT/"out"/Path(kn).name,z.read(kn))
            copied+=1

        for n in ["analysis/REPORT.json","analysis/RESUME_CONTINUITY.json"]:
            if n in names:
                safe_write_bytes(ROOT/"reference"/("imported_v021_"+Path(n).name),z.read(n))
    return copied

def validate():
    missing=[]
    for s in D["settings"]:
        rid=rid_for(s)
        for fn in [
            f"{rid}_i00000.txt",
            f"{rid}_i30000.txt",
            f"{rid}_i40000.txt",
            f"{rid}_i50000.txt",
            f"{rid}_i60000.txt",
            f"{rid}_i60000.k",
        ]:
            p=ROOT/"out"/fn
            if not p.is_file() or p.stat().st_size==0:
                missing.append(str(p))
    if missing:
        raise RuntimeError(f"Import incomplete: {len(missing)} missing; first={missing[:5]}")
    print("SOURCE IMPORT VALIDATION PASS: required 0..60k history + 20 i60000 states")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",default=None)
    a=ap.parse_args()
    src,reason=choose_source(a.source)
    print("SOURCE:",src)
    print("SOURCE SELECTION:",reason)
    n=import_folder(src) if src.is_dir() else import_zip(src)
    print("IMPORTED FILES:",n)
    validate()
    return 0

if __name__=="__main__":
    raise SystemExit(main())
