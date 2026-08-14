from __future__ import annotations
import importlib, json, platform, sys
mods={}
for name in ["numpy","pybind11","setuptools"]:
    try:
        m=importlib.import_module(name); mods[name]=getattr(m,"__version__","unknown")
    except Exception as e:
        mods[name]="MISSING: "+repr(e)
print(json.dumps({"python":sys.version,"platform":platform.platform(),"modules":mods},indent=2))
if any(str(v).startswith("MISSING") for v in mods.values()): raise SystemExit(2)
