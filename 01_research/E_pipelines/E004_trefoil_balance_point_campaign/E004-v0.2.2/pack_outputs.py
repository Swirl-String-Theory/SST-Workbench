from pathlib import Path
import zipfile,hashlib
ROOT=Path(__file__).resolve().parent
out=ROOT.parent/f"{ROOT.name}_outputs.zip"
with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as z:
    for rel in ["analysis","logs","out","balance_design.json","PREREGISTRATION.md","PREREGISTRATION_LOCK.json","VERSION.json"]:
        p=ROOT/rel
        if p.is_file():z.write(p,arcname=p.name)
        elif p.is_dir():
            for q in sorted(p.rglob("*")):
                if q.is_file():z.write(q,arcname=q.relative_to(ROOT).as_posix())
sha=hashlib.sha256(out.read_bytes()).hexdigest()
Path(str(out)+".sha256").write_text(f"{sha}  {out.name}\n",encoding="ascii")
print("CREATED:",out);print("SHA256:",sha)
