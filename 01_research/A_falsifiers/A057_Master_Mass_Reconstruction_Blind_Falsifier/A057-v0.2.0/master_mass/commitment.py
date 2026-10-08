from __future__ import annotations

"""A057 implementation commitment calculation and fail-closed verification.

The implementation bundle intentionally excludes science_contract.json so the
contract can contain the digest without a circular self-hash.  The coverage is
identical to the preregistered A057-v0.2.0 implementation commitment, including the E013 member contract.
"""

from pathlib import Path
import argparse
import hashlib
import json
import sys

COVERAGE = (
    "experiment/**/*.py",
    "master_mass/**/*.py",
    "native_ext/*.cpp",
    "native_ext/*.hpp",
    "native_ext/*.py",
    "configs/*.json",
    "requirements.txt",
    "data/HISTORICAL_MODEL_PUBLIC.json",
    "post_reveal_analysis.py",
    "tests/*.py",
    "cross_falsifier_contract.json",
)


def compute_implementation_bundle(root: str | Path) -> tuple[str, list[dict]]:
    root = Path(root).resolve()
    files: list[Path] = []
    for pattern in COVERAGE:
        files.extend(p for p in root.glob(pattern) if p.is_file())
    rows = []
    for p in sorted(set(files)):
        rows.append(
            {
                "path": p.relative_to(root).as_posix(),
                "size": p.stat().st_size,
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            }
        )
    payload = {"files": rows}
    raw = (
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest(), rows


def expected_commitment(root: str | Path) -> str | None:
    root = Path(root).resolve()
    science = json.loads((root / "science_contract.json").read_text(encoding="utf-8"))
    return science.get("implementation_commitment", {}).get("bundle_sha256")


def verify_implementation_commitment(root: str | Path) -> dict:
    expected = expected_commitment(root)
    actual, rows = compute_implementation_bundle(root)
    return {
        "schema": "A057-IMPLEMENTATION-VERIFICATION-1",
        "expected": expected,
        "actual": actual,
        "ok": bool(expected) and expected == actual,
        "files": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify A057 implementation commitment")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--verify", action="store_true", help="return non-zero on mismatch")
    args = parser.parse_args(argv)
    result = verify_implementation_commitment(args.root)
    print(json.dumps({k: v for k, v in result.items() if k != "files"}, indent=2))
    if args.verify and not result["ok"]:
        print("A057 implementation commitment mismatch; do not run/freeze this instance.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
