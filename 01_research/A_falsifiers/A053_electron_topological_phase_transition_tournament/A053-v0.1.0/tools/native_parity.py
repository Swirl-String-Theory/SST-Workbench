from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"

if not BUILD.exists():
    raise SystemExit("[ERROR] build directory is missing. Run run_build_cpp.cmd first.")

# Python 3.8+ on Windows no longer searches arbitrary PATH entries for extension
# dependencies as broadly as older versions did. Explicitly register both the
# module directory and the configured compiler runtime directory.
_dll_handles = []
if os.name == "nt" and hasattr(os, "add_dll_directory"):
    for directory in [BUILD]:
        if directory.is_dir():
            _dll_handles.append(os.add_dll_directory(str(directory)))
    runtime_file = BUILD / "native_runtime_dir.txt"
    if runtime_file.exists():
        runtime_dir = Path(runtime_file.read_text(encoding="utf-8").strip())
        if runtime_dir.is_dir():
            _dll_handles.append(os.add_dll_directory(str(runtime_dir)))
            print(f"[A053] DLL search directory: {runtime_dir}")

sys.path.insert(0, str(BUILD))

try:
    import a053_native
except ImportError as exc:
    pyds = sorted(BUILD.glob("a053_native*.pyd"))
    print(f"[ERROR] Failed to import native module: {exc}")
    print(f"[A053] Found PYD files: {[str(p) for p in pyds]}")
    dlls = sorted(p.name for p in BUILD.glob("*.dll"))
    print(f"[A053] Runtime DLLs beside PYD: {dlls}")
    print("[HINT] Re-run run_build_cpp.cmd. It now stages MinGW runtime DLLs and prints PE imports.")
    raise SystemExit(22) from exc

from a053_etptf.metrics import circular_order

p = [0.1, 0.2, 0.3]
a = a053_native.circular_order(p)
b = circular_order(p)
print("[A053] native=", a, "python=", b)
if abs(a - b) >= 1e-12:
    raise SystemExit(f"[ERROR] Native/Python parity mismatch: {a!r} vs {b!r}")
print("[A053] Native/Python parity PASS.")
