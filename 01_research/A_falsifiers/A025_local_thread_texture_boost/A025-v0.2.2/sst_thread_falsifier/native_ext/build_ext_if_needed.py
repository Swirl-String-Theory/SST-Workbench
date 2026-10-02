from __future__ import annotations
import argparse, hashlib, json, os, platform, subprocess, sys
from pathlib import Path
from ._config import CPP_REL, LOG_PREFIX, STAMP_REL

ROOT = Path(__file__).resolve().parents[2]
CPP = ROOT / CPP_REL
STAMP = ROOT / STAMP_REL


def _hash_inputs():
    h = hashlib.sha256()
    h.update(CPP.read_bytes())
    h.update(sys.version.encode())
    try:
        import pybind11
        h.update(pybind11.__version__.encode())
    except Exception:
        pass
    return h.hexdigest()


def _extension_exists():
    d = Path(__file__).resolve().parent
    return any(d.glob("_native*.pyd")) or any(d.glob("_native*.so"))


def build(force=False, strict=False, quiet=False):
    wanted = _hash_inputs()
    if not force and STAMP.exists() and _extension_exists():
        try:
            old = json.loads(STAMP.read_text(encoding="utf-8"))
            if old.get("sha256") == wanted:
                if not quiet: print(LOG_PREFIX, "native extension is up to date")
                return True
        except Exception:
            pass
    try:
        import pybind11  # noqa
    except Exception as e:
        print(LOG_PREFIX, "pybind11 unavailable:", e)
        if strict: raise SystemExit(1)
        return False

    setup_py = ROOT / "build" / "_setup_native.py"
    setup_py.parent.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        compile_args = "['/O2', '/std:c++17', '/openmp']"
        link_args = "[]"
    else:
        compile_args = "['-O3', '-std=c++17', '-fopenmp']"
        link_args = "['-fopenmp']"
    setup_py.write_text(f'''\
from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension, build_ext
setup(
    name="sst_thread_falsifier_native",
    # setuptools >=80 performs flat-layout auto-discovery when packages are
    # omitted.  This repository intentionally also contains top-level cpp/
    # and config/ directories, so declare the real Python packages explicitly.
    packages=["sst_thread_falsifier", "sst_thread_falsifier.native_ext"],
    py_modules=[],
    ext_modules=[Pybind11Extension(
        "sst_thread_falsifier.native_ext._native",
        # IMPORTANT: keep the source path relative to ROOT.  Passing the
        # absolute repository path makes setuptools mirror that full path
        # below build\\temp.* for the object file.  On Windows this can
        # exceed MAX_PATH and MSVC then fails with C1083 / an empty compiler-
        # generated filename.
        [r"{Path(CPP_REL).as_posix()}"],
        cxx_std=17,
        extra_compile_args={compile_args},
        extra_link_args={link_args},
    )],
    cmdclass={{"build_ext": build_ext}},
)
''', encoding="utf-8")
    # Use a deliberately short object directory as a second Windows path-length
    # guard.  With cwd=ROOT this produces e.g. build\\temp_native\\cpp\\native.obj
    # instead of build\\temp.win-...\\Release\\<entire absolute repo path>\\cpp\\native.obj.
    cmd = [sys.executable, str(setup_py), "build_ext", "--inplace",
           "--build-temp", str(Path("build") / "temp_native")]
    if not quiet: print(LOG_PREFIX, "compile:", " ".join(cmd))
    cp = subprocess.run(cmd, cwd=ROOT)
    ok = cp.returncode == 0 and _extension_exists()
    if ok:
        STAMP.write_text(json.dumps({
            "sha256": wanted,
            "python": sys.version,
            "platform": platform.platform(),
        }, indent=2), encoding="utf-8")
    elif strict:
        raise SystemExit(cp.returncode or 1)
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    ok = build(a.force, a.strict, a.quiet)
    raise SystemExit(0 if ok or not a.strict else 1)

if __name__ == "__main__":
    main()
