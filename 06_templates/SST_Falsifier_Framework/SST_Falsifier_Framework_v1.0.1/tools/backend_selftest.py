from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import sys
from pathlib import Path

import numpy as np

FRAMEWORK = Path(__file__).resolve().parents[1]
if str(FRAMEWORK) not in sys.path:
    sys.path.insert(0, str(FRAMEWORK))

from sst_falsifier.backend_contract import parity_gate, require_backend
from sst_falsifier.backends import python_ref, cpp_pybind
from sst_falsifier import sycl_worker


def _circle(n: int = 192) -> tuple[np.ndarray, np.ndarray]:
    t = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
    p = np.column_stack((np.cos(t), np.sin(t), np.zeros_like(t)))
    u = np.linspace(-0.85, 0.85, 48)
    q = np.column_stack((0.31 * np.cos(2.7 * u), 0.27 * np.sin(1.9 * u), u))
    return p, q


def _trefoil(n: int = 240) -> tuple[np.ndarray, np.ndarray]:
    t = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
    R, r = 1.0, 0.32
    p = np.column_stack(((R + r * np.cos(3.0 * t)) * np.cos(2.0 * t),
                         (R + r * np.cos(3.0 * t)) * np.sin(2.0 * t),
                         r * np.sin(3.0 * t)))
    u = np.linspace(0.0, 2.0 * np.pi, 64, endpoint=False)
    q = np.column_stack((0.22 * np.cos(u), 0.17 * np.sin(2.0 * u), 0.45 * np.sin(u)))
    return p, q


def _prepare_runtime() -> Path:
    dst = FRAMEWORK / "build" / "backend_selftest_instance"
    if dst.exists():
        shutil.rmtree(dst)
    (dst / "native" / "cpp").mkdir(parents=True, exist_ok=True)
    (dst / "native_ext").mkdir(parents=True, exist_ok=True)
    shutil.copy2(FRAMEWORK / "instance_template" / "native" / "cpp" / "native.cpp", dst / "native" / "cpp" / "native.cpp")
    shutil.copy2(FRAMEWORK / "instance_template" / "native" / "cpp" / "sycl_worker.cpp", dst / "native" / "cpp" / "sycl_worker.cpp")
    (dst / "native_ext" / "__init__.py").write_text("", encoding="utf-8")
    return dst


def _finite_stats(a: np.ndarray) -> dict:
    a = np.asarray(a, dtype=np.float64)
    return {
        "shape": list(a.shape),
        "finite": bool(np.isfinite(a).all()),
        "l2_norm": float(np.linalg.norm(a)),
        "max_abs": float(np.max(np.abs(a))) if a.size else 0.0,
        "sum": float(np.sum(a)),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Cross-backend numerical parity selftest for SST Falsifier Framework.")
    ap.add_argument("--cpp-tol", type=float, default=1e-10)
    ap.add_argument("--sycl-fp64-tol", type=float, default=1e-9)
    ap.add_argument("--sycl-fp32-tol", type=float, default=5e-4)
    ap.add_argument("--allow-sycl-fp32", action="store_true")
    ap.add_argument("--force-build", action="store_true")
    ap.add_argument("--skip-cpp", action="store_true")
    ap.add_argument("--skip-sycl", action="store_true")
    ap.add_argument("--json", default=str(FRAMEWORK / "build" / "BACKEND_SELFTEST.json"))
    args = ap.parse_args()

    if args.allow_sycl_fp32:
        os.environ["SST_SYCL_ALLOW_FP32"] = "1"

    runtime = _prepare_runtime()
    scenarios = [
        ("circle", *_circle(), 1.23456789, 0.041),
        ("trefoil", *_trefoil(), -0.731, 0.057),
    ]
    report = {
        "schema": "SST-BACKEND-PARITY-SELFTEST-1",
        "framework_version": "1.0.1",
        "tolerances": {
            "cpp_vs_python_relative_l2": args.cpp_tol,
            "sycl_fp64_vs_python_relative_l2": args.sycl_fp64_tol,
            "sycl_fp32_vs_python_relative_l2": args.sycl_fp32_tol,
        },
        "backends": {},
        "scenarios": [],
    }

    cpp_ready = not args.skip_cpp
    cpp_build = None
    if cpp_ready:
        try:
            _, cpp_build = cpp_pybind.load(runtime, force_build=args.force_build, require=True, verbose=True)
            report["backends"]["cpp"] = {"available": True, "build": cpp_build.to_dict()}
        except Exception as e:
            cpp_ready = False
            report["backends"]["cpp"] = {"available": False, "error": f"{type(e).__name__}: {e}"}
    else:
        report["backends"]["cpp"] = {"available": False, "skipped": True}

    sycl_ready = not args.skip_sycl
    sycl_info = None
    if sycl_ready:
        sycl_info = sycl_worker.worker_info(runtime, start=False)
        sycl_ready = bool(sycl_info.get("available"))
        report["backends"]["sycl"] = sycl_info
    else:
        report["backends"]["sycl"] = {"available": False, "skipped": True}

    all_pass = True
    if not args.skip_cpp and not cpp_ready:
        all_pass = False
    if not args.skip_sycl and not sycl_ready:
        all_pass = False

    for name, points, queries, gamma, core in scenarios:
        ref = python_ref.biot_savart(points, queries, gamma=gamma, core=core)
        row = {
            "name": name,
            "n_filament_points": int(len(points)),
            "n_queries": int(len(queries)),
            "gamma": float(gamma),
            "core": float(core),
            "python": {"backend": "python-numpy-fp64", "precision": "float64", "stats": _finite_stats(ref)},
        }

        if cpp_ready:
            try:
                cpp, cres = cpp_pybind.biot_savart(runtime, points, queries, gamma=gamma, core=core, require=True)
                require_backend(cres, accepted_actual=["openmp", "serial"], authority="CERTIFICATION", precision="float64")
                parity = parity_gate(cpp, ref, args.cpp_tol)
                row["cpp"] = {"backend_result": cres.to_dict(), "stats": _finite_stats(cpp), "parity_vs_python": parity}
                all_pass = all_pass and bool(parity["pass"])
            except Exception as e:
                row["cpp"] = {"error": f"{type(e).__name__}: {e}", "pass": False}
                all_pass = False
        else:
            row["cpp"] = {"skipped": args.skip_cpp, "available": False}

        if sycl_ready:
            try:
                gpu, gres = sycl_worker.biot_savart(runtime, points, queries, gamma=gamma, core=core, require_fp64=False)
                accepted = ["sycl-worker-fp64"] if gres.precision == "float64" else ["sycl-worker-fp32"]
                required_authority = "CERTIFICATION" if gres.precision == "float64" else "SCREENING_ONLY"
                require_backend(gres, accepted_actual=accepted, authority=required_authority, precision=gres.precision)
                tol = args.sycl_fp64_tol if gres.precision == "float64" else args.sycl_fp32_tol
                parity = parity_gate(gpu, ref, tol)
                row["sycl"] = {"backend_result": gres.to_dict(), "stats": _finite_stats(gpu), "parity_vs_python": parity}
                all_pass = all_pass and bool(parity["pass"])
            except Exception as e:
                row["sycl"] = {"error": f"{type(e).__name__}: {e}", "pass": False}
                all_pass = False
        else:
            row["sycl"] = {"skipped": args.skip_sycl, "available": False}

        report["scenarios"].append(row)

    sycl_worker.shutdown_worker(runtime)
    report["overall_pass"] = bool(all_pass)
    out = Path(args.json)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("SST backend parity selftest")
    print("===========================")
    print(f"C++ backend available : {report['backends']['cpp'].get('available', False)}")
    print(f"SYCL backend available: {report['backends']['sycl'].get('available', False)}")
    for row in report["scenarios"]:
        print(f"\n[{row['name']}]")
        print(f"  Python norm: {row['python']['stats']['l2_norm']:.16e}")
        if "parity_vs_python" in row.get("cpp", {}):
            p = row["cpp"]["parity_vs_python"]
            print(f"  C++   rel-L2: {p['relative_l2']:.6e} <= {p['tolerance']:.6e} : {'PASS' if p['pass'] else 'FAIL'}")
        else:
            print(f"  C++   : {'SKIP' if row.get('cpp',{}).get('skipped') else 'UNAVAILABLE/FAIL'}")
        if "parity_vs_python" in row.get("sycl", {}):
            p = row["sycl"]["parity_vs_python"]
            br = row["sycl"]["backend_result"]
            print(f"  SYCL  ({br['precision']}): rel-L2 {p['relative_l2']:.6e} <= {p['tolerance']:.6e} : {'PASS' if p['pass'] else 'FAIL'}")
        else:
            print(f"  SYCL  : {'SKIP' if row.get('sycl',{}).get('skipped') else 'UNAVAILABLE/FAIL'}")
    print(f"\nReport: {out}")
    print(f"OVERALL: {'PASS' if all_pass else 'FAIL'}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
