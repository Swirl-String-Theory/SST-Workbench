from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parent
exclude={".venv","build","__pycache__",".pytest_cache","SST_Euler_Regularity_BKM_Singularity_Gate_v0.2.0-outputs"}
rows=[]
for f in sorted(ROOT.rglob('*')):
    if not f.is_file() or any(p in exclude for p in f.parts): continue
    if f.suffix.lower() in {".so",".pyd",".pyc"} or f.name=="campaign_console.txt": continue
    if f.name in {"PACKAGE_MANIFEST.json","MANIFEST_SHA256.txt"}: continue
    rows.append({"path":str(f.relative_to(ROOT)).replace('\\','/'),"bytes":f.stat().st_size,"sha256":hashlib.sha256(f.read_bytes()).hexdigest()})
obj={"format":"SST-BKM-PACKAGE-MANIFEST-2","package":ROOT.name,"version":"0.2.0","files":rows}
(ROOT/'PACKAGE_MANIFEST.json').write_text(json.dumps(obj,indent=2)+'\n')
(ROOT/'MANIFEST_SHA256.txt').write_text('\n'.join(f"{r['sha256']}  {r['path']}" for r in rows)+'\n')
zip_path=ROOT.parent/(ROOT.name+'.zip')
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
    for f in sorted(ROOT.rglob('*')):
        if f.is_file() and not any(p in exclude for p in f.parts) and f.suffix.lower() not in {".so",".pyd",".pyc"} and f.name!="campaign_console.txt": z.write(f,f.relative_to(ROOT.parent))
print(zip_path)
