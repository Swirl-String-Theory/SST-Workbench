from __future__ import annotations

import argparse
import hashlib
import importlib.machinery
import json
import os
import platform
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CPP = ROOT / "sst_ssdl_audit" / "cpp" / "ssdl_bem.cpp"
PKG = ROOT / "sst_ssdl_audit"
BUILD = ROOT / "build"
STAMP = BUILD / "ssdl_bem.stamp.json"


def _hash_files(paths: list[Path]) -> str:
    h = hashlib.sha256()
    for path in paths:
        h.update(str(path.relative_to(ROOT)).encode())
        h.update(b"\0")
        h.update(path.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def extension_path() -> Path:
    suffix = sysconfig.get_config_var("EXT_SUFFIX") or importlib.machinery.EXTENSION_SUFFIXES[0]
    return PKG / ("_ssdlbem" + suffix)


def have_pybind11() -> bool:
    try:
        subprocess.check_output([sys.executable, "-m", "pybind11", "--includes"], text=True, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def _run(cmd: list[str], cwd: Path, verbose: bool) -> bool:
    if verbose:
        print("[sst_ssdl_audit] compile:", " ".join(cmd), file=sys.stderr)
    proc = subprocess.run(cmd, cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode == 0:
        return True
    if verbose:
        print(f"[sst_ssdl_audit] build failed: {proc.returncode}", file=sys.stderr)
        print(proc.stderr, file=sys.stderr)
    return False


def build_if_needed(force: bool = False, verbose: bool = True) -> bool:
    out = extension_path()
    BUILD.mkdir(exist_ok=True)
    compiler = os.environ.get("CXX") or shutil.which("c++") or shutil.which("g++") or shutil.which("clang++")
    if not compiler or not have_pybind11():
        return out.exists()

    src_hash = _hash_files([CPP])
    meta = {"hash": src_hash, "compiler": compiler, "ext": out.name}
    if not force and out.exists() and STAMP.exists():
        try:
            if json.loads(STAMP.read_text()).get("hash") == src_hash:
                return True
        except Exception:
            pass

    includes = subprocess.check_output([sys.executable, "-m", "pybind11", "--includes"], text=True, stderr=subprocess.DEVNULL).split()
    base = [compiler, "-O3", "-std=c++17", "-shared"]
    if platform.system().lower() != "windows":
        base.append("-fPIC")
    cmd = [*base, *includes, str(CPP), "-o", str(out)]

    if platform.system().lower() == "windows":
        maj, minor = sys.version_info[:2]
        for p in [Path(sys.base_prefix), Path(sys.prefix)]:
            cmd.extend(["-L" + str(p / "libs")])
        cmd.extend([f"-lpython{maj}{minor}"])

    if _run(cmd, ROOT, verbose) and out.exists():
        STAMP.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        return True
    return out.exists()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    raise SystemExit(0 if build_if_needed(args.force) else 1)
