from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import re
from pathlib import Path


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _expected_version(release: Path) -> str | None:
    m = re.search(r"E010-v(\d+\.\d+\.\d+)", release.name)
    return m.group(1) if m else None


def probe(release: str | Path) -> tuple[int, dict]:
    rr = Path(release).resolve()
    out: dict = {"release": str(rr), "ready": False}
    if not rr.is_dir():
        out["reason"] = "release_missing"
        return 20, out

    try:
        pkg = importlib.import_module("pklsa_builder")
    except Exception as exc:
        out.update(reason="pklsa_builder_import_failed", error_type=type(exc).__name__)
        return 21, out

    pkg_file = Path(getattr(pkg, "__file__", "") or "").resolve()
    out["package_file"] = str(pkg_file)
    if not _inside(pkg_file, rr):
        out["reason"] = "installed_package_not_from_selected_release"
        return 22, out

    expected = _expected_version(rr)
    try:
        installed = importlib.metadata.version("sst-pklsa")
    except importlib.metadata.PackageNotFoundError:
        installed = None
    out["installed_version"] = installed
    out["expected_version"] = expected
    if expected and installed != expected:
        out["reason"] = "installed_version_mismatch"
        return 23, out

    try:
        native = importlib.import_module("pklsa_builder._native")
    except Exception as exc:
        out.update(reason="pklsa_native_import_failed", error_type=type(exc).__name__)
        return 24, out

    native_file = Path(getattr(native, "__file__", "") or "").resolve()
    out["native_file"] = str(native_file)
    if not _inside(native_file, rr):
        out["reason"] = "native_not_from_selected_release"
        return 25, out

    src = rr / "cpp" / "pklsa_native.cpp"
    if src.exists() and native_file.exists():
        out["native_source_mtime_ns"] = src.stat().st_mtime_ns
        out["native_binary_mtime_ns"] = native_file.stat().st_mtime_ns
        if src.stat().st_mtime_ns > native_file.stat().st_mtime_ns:
            out["reason"] = "native_binary_older_than_source"
            return 26, out

    out.update(ready=True, reason="selected_release_and_native_already_active")
    return 0, out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Check whether the selected E010 release is already active with its native extension.")
    ap.add_argument("--release", required=True)
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    rc, info = probe(a.release)
    if not a.quiet:
        print(json.dumps(info, indent=2))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
