from __future__ import annotations
import importlib, platform, sys, json
from pathlib import Path

mods=["numpy","pybind11","setuptools"]
rows={}
ok=True
for m in mods:
    try:
        x=importlib.import_module(m)
        rows[m]=getattr(x,"__version__","available")
    except Exception as e:
        rows[m]=f"MISSING: {e}"
        ok=False

# Build-system regression guard: setuptools >=80 rejects ambiguous flat-layout
# discovery if the generated setup() does not explicitly declare packages.
_builder = Path(__file__).resolve().parent / "sst_thread_falsifier" / "native_ext" / "build_ext_if_needed.py"
_builder_text = _builder.read_text(encoding="utf-8")
_required = 'packages=["sst_thread_falsifier", "sst_thread_falsifier.native_ext"]'
_pyproject = Path(__file__).resolve().parent / "pyproject.toml"
_pyproject_text = _pyproject.read_text(encoding="utf-8")
_pyproject_required = 'packages = ["sst_thread_falsifier", "sst_thread_falsifier.native_ext"]'
build_system_ok = (_required in _builder_text and _pyproject_required in _pyproject_text)
if not build_system_ok:
    ok=False
    rows["build_system"]="FAIL: explicit setuptools package declaration missing in builder or pyproject"
else:
    rows["build_system"]="explicit setuptools package discovery = PASS"

print(json.dumps({"python":sys.version,"platform":platform.platform(),"dependencies":rows,"status":"PASS" if ok else "FAIL"},indent=2))
raise SystemExit(0 if ok else 1)
