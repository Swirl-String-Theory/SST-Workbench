from pathlib import Path
import zipfile,hashlib,json
ROOT=Path(__file__).resolve().parent
OUT=ROOT.parent/(ROOT.name+"_outputs.zip")
include=["out","logs","analysis","seeds","base","campaign_config.json","seed_manifest.json","PREREGISTRATION.md","CHANGELOG.md"]
with zipfile.ZipFile(OUT,"w",zipfile.ZIP_DEFLATED) as z:
    for name in include:
        p=ROOT/name
        if p.is_file():
            z.write(p,arcname=p.name)
        elif p.is_dir():
            for q in sorted(p.rglob("*")):
                if q.is_file(): z.write(q,arcname=q.relative_to(ROOT).as_posix())
sha=hashlib.sha256(OUT.read_bytes()).hexdigest()
Path(str(OUT)+".sha256").write_text(f"{sha}  {OUT.name}\n",encoding="ascii")
print("Created:",OUT)
print("SHA256:",sha)
