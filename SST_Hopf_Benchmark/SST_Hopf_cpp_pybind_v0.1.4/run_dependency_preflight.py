from __future__ import annotations
import importlib
import json
import sys
from pathlib import Path

REQUIRED = ("numpy", "pybind11", "setuptools", "wheel")
rows = []
ok = True
for name in REQUIRED:
    try:
        m = importlib.import_module(name)
        rows.append({"name": name, "ok": True, "version": getattr(m, "__version__", "unknown")})
    except Exception as exc:
        ok = False
        rows.append({"name": name, "ok": False, "error": repr(exc)})

payload = {"ok": ok, "python": sys.version, "requirements": rows}
print(json.dumps(payload, indent=2))
out = Path("results") / "dependency_preflight.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
raise SystemExit(0 if ok else 1)
