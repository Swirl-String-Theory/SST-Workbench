"""Guarded single-line bug fix for an UNFROZEN GPE v0.1.1 instance."""
from pathlib import Path
import hashlib
import sys

OLD = b"ROOT=Path(__file__).resolve().parents[1]"
NEW = b"ROOT=Path(__file__).resolve().parent"
EXPECTED_SHA256 = "22efba27e2e4f7ea63840c5f8fafe0645c47f726aa28cb044fd62e4d589edd3b"


def apply(instance: Path) -> None:
    instance = instance.resolve()
    assert instance.name == "GPE_EXT_001_GPE_GPU_Benchmark_v0.1.1", "unexpected target directory"
    source = instance / "preflight_report.py"
    frozen = instance / "preregistration" / "FROZEN_PROTOCOL.json"
    if frozen.exists():
        raise RuntimeError(f"Refusing to change frozen protocol instance: {frozen}")
    if not source.is_file():
        raise FileNotFoundError(source)
    original = source.read_bytes()
    if hashlib.sha256(original).hexdigest() != EXPECTED_SHA256:
        if original.count(NEW) == 1 and original.count(OLD) == 0:
            print("Already patched; no changes made.")
            return
        raise RuntimeError("Unexpected preflight source. Refusing unverified modification.")
    if original.count(OLD) != 1:
        raise RuntimeError("Expected buggy line not found exactly once")
    updated = original.replace(OLD, NEW)
    backup = source.with_suffix(".py.before_pathfix.bak")
    if backup.exists():
        raise RuntimeError(f"Backup path already exists; refusing overwrite: {backup}")
    with backup.open("xb") as fd:
        fd.write(original)
    source.write_bytes(updated)
    print("PATCHED:", source)
    print("Backup:", backup)
    print("Corrected ROOT expression; no frozen-science or framework files touched.")
    print("NEXT: cd /d \""+str(instance)+"\" && run_all.cmd BASIC")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python apply_patch.py <existing GPE v0.1.1 instance directory>")
    apply(Path(sys.argv[1]))
