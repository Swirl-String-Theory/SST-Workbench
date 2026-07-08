from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from . import _config


def write_json(path: str | Path, data: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


def write_csv(path: str | Path, rows: list[dict[str, Any]]) -> None:
    import csv

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        p.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with p.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _load_cpp_backend(*, force_build: bool = False, build_verbose: bool = False):
    try:
        from .build_ext_if_needed import build_if_needed

        build_if_needed(force=force_build, verbose=build_verbose)
        mod = __import__(f"{_config.PACKAGE_NAME}.{_config.EXT_BASENAME}", fromlist=["*"])
        return mod
    except Exception:
        return None


def run(
    a: float,
    b: float,
    *,
    force_python: bool = False,
    skip_build: bool = False,
    force_build: bool = False,
    build_verbose: bool = False,
) -> dict[str, Any]:
    """Call C++ kernel when available, else Python fallback."""
    if not force_python and not skip_build:
        backend = _load_cpp_backend(force_build=force_build, build_verbose=build_verbose)
        if backend is not None:
            try:
                return {"backend": "cpp", "a": a, "b": b, "value": float(backend.add(a, b))}
            except Exception as exc:
                print(f"{_config.LOG_PREFIX} C++ failed: {exc}", file=sys.stderr)

    from .fallback import add

    return {"backend": "python", "a": a, "b": b, "value": float(add(a, b))}


def run_audit(
    a: float = 2.0,
    b: float = 3.0,
    *,
    expected: float | None = None,
    force_python: bool = False,
    skip_build: bool = False,
    force_build: bool = False,
    build_verbose: bool = False,
) -> dict[str, Any]:
    """Replace with your audit / experiment entry point."""
    if expected is None:
        expected = a + b
    probe = run(
        a,
        b,
        force_python=force_python,
        skip_build=skip_build,
        force_build=force_build,
        build_verbose=build_verbose,
    )
    return {
        "audit_name": "SST cpp_pybind_audit template smoke test",
        "probe": probe,
        "expected": expected,
        "ok": abs(probe["value"] - expected) < 1e-12,
    }


def run_sweep(
    values_a: list[float],
    values_b: list[float],
    *,
    force_python: bool = False,
    skip_build: bool = False,
    force_build: bool = False,
    build_verbose: bool = False,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for a in values_a:
        for b in values_b:
            row = run(
                a,
                b,
                force_python=force_python,
                skip_build=skip_build,
                force_build=force_build,
                build_verbose=build_verbose,
            )
            row["expected"] = a + b
            row["ok"] = abs(row["value"] - row["expected"]) < 1e-12
            rows.append(row)
    return rows


def run_all_checks(
    *,
    out_dir: str | Path = "audit_out",
    force_python: bool = False,
    force_build: bool = False,
) -> dict[str, Any]:
    """Run a small battery of checks (extend for your audit)."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    smoke_cpp = run_audit(a=2.0, b=3.0, force_python=force_python, force_build=force_build)
    write_json(out / "smoke_cpp.json", smoke_cpp)

    smoke_py = run_audit(a=2.0, b=3.0, force_python=True, skip_build=True)
    write_json(out / "smoke_python.json", smoke_py)

    sweep = run_sweep([1.0, 2.0, 3.0], [0.5, 1.5], force_python=force_python, skip_build=True)
    write_json(out / "sweep.json", sweep)
    write_csv(out / "sweep.csv", sweep)

    summary = {
        "audit_name": "SST cpp_pybind_audit template full check",
        "out_dir": str(out),
        "smoke_cpp_ok": smoke_cpp["ok"],
        "smoke_python_ok": smoke_py["ok"],
        "sweep_ok": all(r["ok"] for r in sweep),
        "ok": smoke_cpp["ok"] and smoke_py["ok"] and all(r["ok"] for r in sweep),
    }
    write_json(out / "audit_summary.json", summary)
    return summary
