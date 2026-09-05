from pathlib import Path
import argparse,zipfile,hashlib
ROOT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument("name");a=ap.parse_args()
src=ROOT/"campaigns"/a.name
if not src.is_dir():raise SystemExit(f"Missing campaign {src}")
out=ROOT.parent/f"{ROOT.name}_{a.name}_outputs.zip"
with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as z:
    for p in sorted(src.rglob("*")):
        if p.is_file():z.write(p,arcname=p.relative_to(src).as_posix())
sha=hashlib.sha256(out.read_bytes()).hexdigest()
Path(str(out)+".sha256").write_text(f"{sha}  {out.name}\n")
print("Created:",out);print("SHA256:",sha)
