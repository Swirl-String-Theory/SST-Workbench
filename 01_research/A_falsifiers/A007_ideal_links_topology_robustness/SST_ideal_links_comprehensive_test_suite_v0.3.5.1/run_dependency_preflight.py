#!/usr/bin/env python3
from __future__ import annotations
import importlib
import json
import sys

required = ["numpy", "scipy", "pandas", "matplotlib", "pybind11"]
optional = ["tabulate"]

report = {
    "python_executable": sys.executable,
    "python_version": sys.version,
    "required": {},
    "optional": {},
    "ok": True,
}

for name in required:
    try:
        module = importlib.import_module(name)
        report["required"][name] = getattr(module, "__version__", "installed")
    except Exception as exc:
        report["required"][name] = f"MISSING: {type(exc).__name__}: {exc}"
        report["ok"] = False

for name in optional:
    try:
        module = importlib.import_module(name)
        report["optional"][name] = getattr(module, "__version__", "installed")
    except Exception as exc:
        report["optional"][name] = (
            f"not installed ({type(exc).__name__}); safe fallback renderer will be used"
        )

print(json.dumps(report, indent=2))
raise SystemExit(0 if report["ok"] else 1)
