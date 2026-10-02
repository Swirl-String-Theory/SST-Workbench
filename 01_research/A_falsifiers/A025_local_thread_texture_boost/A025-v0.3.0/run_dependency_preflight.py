from __future__ import annotations
import importlib,platform,sys,json
mods=["numpy","pybind11","setuptools"]
rows={}
ok=True
for m in mods:
    try:
        x=importlib.import_module(m); rows[m]=getattr(x,"__version__","available")
    except Exception as e:
        rows[m]=f"MISSING: {e}"; ok=False
print(json.dumps({"python":sys.version,"platform":platform.platform(),"dependencies":rows,"status":"PASS" if ok else "FAIL"},indent=2))
raise SystemExit(0 if ok else 1)
