from pathlib import Path
import argparse,os,shutil,zipfile,json,re
ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/"balance_design.json").read_text())
RESUME=100000

def rid(s):return f"K31__{s['id']}"

def safe_copy(src,dst):
    src=Path(src);dst=Path(dst);dst.parent.mkdir(parents=True,exist_ok=True)
    tmp=dst.with_name(dst.name+".importing")
    try:
        with src.open("rb") as fi,tmp.open("wb") as fo:shutil.copyfileobj(fi,fo,1024*1024)
        tmp.replace(dst)
    finally:
        try:
            if tmp.exists():tmp.unlink()
        except OSError:pass

def write_bytes(dst,b):
    dst=Path(dst);dst.parent.mkdir(parents=True,exist_ok=True);tmp=dst.with_name(dst.name+".importing")
    try:
        tmp.write_bytes(b);tmp.replace(dst)
    finally:
        try:
            if tmp.exists():tmp.unlink()
        except OSError:pass

def folder_ok(p):
    base=p/"out" if (p/"out").is_dir() else p
    return all((base/f"{rid(s)}_i100000.k").is_file() and (base/f"{rid(s)}_i100000.txt").is_file() for s in D["settings"])

def zip_ok(p):
    try:
        with zipfile.ZipFile(p) as z:
            n=set(z.namelist())
            return all(f"out/{rid(s)}_i100000.k" in n and f"out/{rid(s)}_i100000.txt" in n for s in D["settings"])
    except: return False

def choose(explicit):
    if explicit:
        p=Path(explicit)
        if (p.is_dir() and folder_ok(p)) or (p.is_file() and zip_ok(p)):return p,"explicit"
        raise RuntimeError(f"Unusable explicit source: {p}")
    env=os.environ.get("TREFOIL_V022_SOURCE","").strip()
    if env:
        p=Path(env)
        if (p.is_dir() and folder_ok(p)) or (p.is_file() and zip_ok(p)):return p,"environment"
        raise RuntimeError(f"Unusable TREFOIL_V022_SOURCE: {p}")
    # packed outputs first
    for p in sorted(ROOT.parent.glob("Trefoil_Balance_Point_Campaign_v0.2.2_outputs*.zip"),
                    key=lambda x:x.stat().st_mtime,reverse=True):
        if zip_ok(p):return p,"packed outputs"
    p=ROOT.parent/"Trefoil_Balance_Point_Campaign_v0.2.2"
    if folder_ok(p):return p,"sibling folder"
    raise RuntimeError("No complete v0.2.2 100k source found. Set TREFOIL_V022_SOURCE.")

def import_folder(src):
    base=src/"out" if (src/"out").is_dir() else src;n=0
    for s in D["settings"]:
        rr=rid(s)
        for p in sorted(base.glob(f"{rr}_i*.txt")):
            m=re.search(r"_i(\d+)\.txt$",p.name)
            if m and int(m.group(1))<=RESUME:safe_copy(p,ROOT/"out"/p.name);n+=1
        p=base/f"{rr}_i100000.k";safe_copy(p,ROOT/"out"/p.name);n+=1
    return n

def import_zip(src):
    n=0
    with zipfile.ZipFile(src) as z:
        names=set(z.namelist())
        for s in D["settings"]:
            rr=rid(s)
            for name in sorted(names):
                if name.startswith(f"out/{rr}_i") and name.endswith(".txt"):
                    m=re.search(r"_i(\d+)\.txt$",name)
                    if m and int(m.group(1))<=RESUME:
                        write_bytes(ROOT/"out"/Path(name).name,z.read(name));n+=1
            kn=f"out/{rr}_i100000.k";write_bytes(ROOT/"out"/Path(kn).name,z.read(kn));n+=1
        for name in ["analysis/REPORT.json","analysis/RESUME_CONTINUITY_60K.json"]:
            if name in names:write_bytes(ROOT/"reference"/("imported_v022_"+Path(name).name),z.read(name))
    return n

def validate():
    miss=[]
    for s in D["settings"]:
        rr=rid(s)
        for fn in [f"{rr}_i00000.txt",f"{rr}_i60000.txt",f"{rr}_i100000.txt",f"{rr}_i100000.k"]:
            p=ROOT/"out"/fn
            if not p.is_file() or p.stat().st_size==0:miss.append(str(p))
    if miss:raise RuntimeError(f"Import incomplete: {len(miss)} missing, first={miss[:5]}")
    print("SOURCE IMPORT VALIDATION PASS: <=100k history + 20 i100000 states")

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--source");a=ap.parse_args()
    p,why=choose(a.source);print("SOURCE:",p);print("SOURCE SELECTION:",why)
    n=import_folder(p) if p.is_dir() else import_zip(p);print("IMPORTED FILES:",n);validate()
if __name__=="__main__":main()
