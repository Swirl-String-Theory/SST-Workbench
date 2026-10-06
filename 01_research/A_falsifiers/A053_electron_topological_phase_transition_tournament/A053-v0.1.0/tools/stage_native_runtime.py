from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"
CACHE = BUILD / "CMakeCache.txt"


def cache_value(key: str) -> str | None:
    if not CACHE.exists():
        return None
    prefix = key + ":"
    for line in CACHE.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith(prefix) and "=" in line:
            return line.split("=", 1)[1].strip()
    return None


def run(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT).strip()


def main() -> int:
    pyds = sorted(BUILD.glob("a053_native*.pyd"))
    if not pyds:
        print("[ERROR] No a053_native*.pyd found in build/.")
        return 2

    compiler_raw = cache_value("CMAKE_CXX_COMPILER")
    if not compiler_raw:
        print("[ERROR] CMAKE_CXX_COMPILER not found in build/CMakeCache.txt.")
        return 3
    compiler = Path(compiler_raw)
    if not compiler.exists():
        print(f"[ERROR] Configured compiler does not exist: {compiler}")
        return 4

    print(f"[A053] Native module: {pyds[0]}")
    print(f"[A053] Compiler:      {compiler}")

    # Runtime DLLs commonly needed by MinGW/Strawberry-built Python extensions.
    candidates = [
        "libstdc++-6.dll",
        "libgcc_s_seh-1.dll",
        "libgcc_s_dw2-1.dll",
        "libwinpthread-1.dll",
    ]
    copied: list[str] = []
    if "gcc" in run([str(compiler), "--version"]).lower() or "gnu" in run([str(compiler), "--version"]).lower():
        for dll in candidates:
            try:
                resolved = run([str(compiler), f"-print-file-name={dll}"])
            except Exception:
                continue
            src = Path(resolved)
            # GCC echoes the bare name when it cannot resolve it.
            if resolved == dll or not src.is_file():
                continue
            dst = BUILD / src.name
            shutil.copy2(src, dst)
            copied.append(src.name)
            print(f"[A053] Staged runtime DLL: {src} -> {dst}")

    # Diagnostic import list via objdump when available.
    objdump_candidates = [
        compiler.with_name("objdump.exe"),
        compiler.with_name("objdump"),
    ]
    objdump = next((p for p in objdump_candidates if p.exists()), None)
    if objdump:
        try:
            out = run([str(objdump), "-p", str(pyds[0])])
            imports = re.findall(r"DLL Name:\s*([^\r\n]+)", out)
            if imports:
                print("[A053] PE imports:")
                for name in imports:
                    marker = " [staged]" if (BUILD / name.strip()).exists() else ""
                    print(f"        {name.strip()}{marker}")
        except Exception as exc:
            print(f"[A053] objdump diagnostic unavailable: {exc}")

    runtime_dir = compiler.parent
    (BUILD / "native_runtime_dir.txt").write_text(str(runtime_dir), encoding="utf-8")
    print(f"[A053] Runtime directory recorded: {runtime_dir}")
    if not copied:
        print("[A053] No MinGW runtime DLLs required/staged, or compiler did not resolve them.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
