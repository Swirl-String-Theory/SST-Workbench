#!/usr/bin/env python3
"""Regenerate MANIFEST_SHA256.txt for tracked release files."""
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKIP_DIRS = {".venv", "__pycache__", "outputs", ".pytest_cache", "build", "dist", "*.egg-info"}
SKIP_SUFFIXES = {".pyc", ".pyd", ".so", ".dll"}
# Include package + docs + tests + scripts, exclude heavy/local
INCLUDE_PREFIXES = (
    "CHANGELOG.md",
    "README.md",
    "THIRD_PARTY.md",
    "VALIDATION.md",
    "configs/",
    "cpp/",
    "docs/",
    "examples/",
    "pyproject.toml",
    "reference_validation.json",
    "requirements.txt",
    "run_",
    "setup.py",
    "sst_knotlib/",
    "tests/",
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def wanted(rel: str) -> bool:
    rel = rel.replace("\\", "/")
    if any(part in SKIP_DIRS for part in Path(rel).parts):
        return False
    if Path(rel).suffix.lower() in SKIP_SUFFIXES:
        return False
    return any(rel == p or rel.startswith(p) for p in INCLUDE_PREFIXES)


def main() -> None:
    rows = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel == "MANIFEST_SHA256.txt":
            continue
        if not wanted(rel):
            continue
        rows.append((sha256_file(path), rel))
    lines = [
        "# SST Knot Library v0.2.1 release integrity manifest",
        "# SHA-256  relative/path",
    ]
    lines.extend(f"{h}  {rel}" for h, rel in rows)
    (ROOT / "MANIFEST_SHA256.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {len(rows)} entries")


if __name__ == "__main__":
    main()
