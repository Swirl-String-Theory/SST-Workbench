from pathlib import Path
import zipfile,hashlib
ROOT=Path(__file__).resolve().parent
p=ROOT.parent/f"{ROOT.name}_outputs.zip"
with zipfile.ZipFile(p,"w",zipfile.ZIP_DEFLATED) as z:
    for rel in ["analysis","logs","out","reference","balance_design.json","PREREGISTRATION.md","PREREGISTRATION_LOCK.json","VERSION.json"]:
        q=ROOT/rel
        if q.is_file():z.write(q,arcname=q.name)
        elif q.is_dir():
            for f in sorted(q.rglob("*")):
                if f.is_file():z.write(f,arcname=f.relative_to(ROOT).as_posix())
sha=hashlib.sha256(p.read_bytes()).hexdigest()
Path(str(p)+".sha256").write_text(f"{sha}  {p.name}\n")
print("CREATED",p);print("SHA256",sha)
