from pathlib import Path
import zipfile,hashlib
ROOT=Path(__file__).resolve().parent
name=f"{ROOT.name}_outputs.zip"
out=ROOT/name
if out.exists(): out.unlink()
keep=["analysis","logs","out","runtime_kpc","stability_handoff","sst_v048_outputs","parameter_manifest.json","sst_v048_bridge_contract.json","parameters_full_source.txt","README.md","CHANGELOG.md","CHANGELOG_v0.3.3.md"]
with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as z:
    for rel in keep:
        p=ROOT/rel
        if not p.exists(): continue
        if p.is_file(): z.write(p,arcname=p.relative_to(ROOT).as_posix())
        else:
            for q in sorted(p.rglob("*")):
                if q.is_file(): z.write(q,arcname=q.relative_to(ROOT).as_posix())
sha=hashlib.sha256(out.read_bytes()).hexdigest()
(ROOT/(name+".sha256")).write_text(f"{sha}  {name}\n",encoding="ascii")
print("OUTPUT PACKAGE:",out)
print("SHA256:",sha)
