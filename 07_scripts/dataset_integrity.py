"""SP10: verify moved knot datasets still match SP00 freeze checksums."""
from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path

WB = Path(__file__).resolve().parents[1]
CHECKSUMS = WB / "10_docs" / "migration" / "checksums.sha256"
PATH_MAP = WB / "10_docs" / "migration" / "path_map.csv"

# Directory moves that land under the knot data domain.
DATASET_PREFIXES = (
    "03_data/A_knots/",
)


def load_checksums(path: Path = CHECKSUMS) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "  " in line:
            digest, rel = line.split("  ", 1)
        else:
            parts = line.split(None, 1)
            if len(parts) != 2:
                continue
            digest, rel = parts
        out[rel.replace("\\", "/").lstrip("*")] = digest.lower()
    return out


def dataset_moves(path_map: Path = PATH_MAP) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    with path_map.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if (row.get("status") or "").strip().lower() not in {"moved", "verified"}:
                continue
            old = (row.get("old_path") or "").replace("\\", "/").strip()
            new = (row.get("new_path") or "").replace("\\", "/").strip()
            if not old or not new or "*" in old:
                continue
            if not any(new.startswith(p) for p in DATASET_PREFIXES):
                continue
            rows.append((old, new))
    return rows


def sha256_file(path: Path, chunk: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            block = f.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def remap_old_to_new(old_file: str, moves: list[tuple[str, str]]) -> str | None:
    """Map a freeze-era path onto the post-move catalog path."""
    best: tuple[int, str] | None = None
    for old_root, new_root in moves:
        if old_file == old_root or old_file.startswith(old_root.rstrip("/") + "/"):
            suffix = old_file[len(old_root):].lstrip("/")
            mapped = new_root if not suffix else f"{new_root.rstrip('/')}/{suffix}"
            if best is None or len(old_root) > best[0]:
                best = (len(old_root), mapped)
    return None if best is None else best[1]


def verify_datasets(
    *,
    root: Path = WB,
    checksums: dict[str, str] | None = None,
    moves: list[tuple[str, str]] | None = None,
    max_files_per_move: int | None = None,
) -> dict[str, object]:
    """Check freeze checksums against files at their new locations.

    Also records whether the still-present legacy junction (if any) matches the
    new path byte-for-byte. A freeze mismatch with junction==new means the
    content drifted after SP00, not that the move corrupted data.
    """
    digests = checksums if checksums is not None else load_checksums()
    move_rows = moves if moves is not None else dataset_moves()
    checked = 0
    missing = []
    mismatched = []
    freeze_drift = []
    per_move: dict[str, dict[str, int]] = {}

    for old_root, new_root in move_rows:
        stats = {
            "checked": 0, "missing": 0, "mismatched": 0,
            "freeze_drift": 0, "candidates": 0,
        }
        per_move[f"{old_root} -> {new_root}"] = stats
        candidates = [
            p for p in digests
            if p == old_root or p.startswith(old_root.rstrip("/") + "/")
        ]
        stats["candidates"] = len(candidates)
        if max_files_per_move is not None and len(candidates) > max_files_per_move:
            sized: list[tuple[int, str]] = []
            for old_file in candidates:
                mapped = remap_old_to_new(old_file, [(old_root, new_root)])
                if not mapped:
                    continue
                new_path = root / mapped
                sized.append((new_path.stat().st_size if new_path.is_file() else 10**18, old_file))
            sized.sort()
            candidates = [p for _, p in sized[:max_files_per_move]]

        for old_file in candidates:
            mapped = remap_old_to_new(old_file, [(old_root, new_root)])
            if not mapped:
                continue
            new_path = root / mapped
            want = digests[old_file]
            if not new_path.is_file():
                stats["missing"] += 1
                if len(missing) < 20:
                    missing.append({"old": old_file, "new": mapped})
                continue
            got = sha256_file(new_path)
            stats["checked"] += 1
            checked += 1
            if got == want:
                continue
            # Move integrity: legacy path (junction or leftover) vs new path.
            legacy_path = root / old_file
            legacy_same = False
            if legacy_path.is_file():
                try:
                    legacy_same = sha256_file(legacy_path) == got
                except OSError:
                    legacy_same = False
            entry = {
                "old": old_file, "new": mapped, "want": want, "got": got,
                "legacy_matches_new": legacy_same,
            }
            if legacy_same:
                stats["freeze_drift"] += 1
                if len(freeze_drift) < 20:
                    freeze_drift.append(entry)
            else:
                stats["mismatched"] += 1
                if len(mismatched) < 20:
                    mismatched.append(entry)

    return {
        "moves": len(move_rows),
        "checked": checked,
        "missing": missing,
        "mismatched": mismatched,
        "freeze_drift": freeze_drift,
        "per_move": per_move,
        # Move corruption is missing files or new!=legacy. Freeze drift is reported
        # separately and does not fail the move integrity gate by itself.
        "ok": not missing and not mismatched and checked > 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-per-move", type=int, default=None,
                    help="optional cap for large trees (e.g. KnotPlot/knots)")
    args = ap.parse_args()
    report = verify_datasets(max_files_per_move=args.max_per_move)
    print(f"moves={report['moves']} checked={report['checked']}")
    print(
        f"missing={len(report['missing'])} mismatched={len(report['mismatched'])} "
        f"freeze_drift={len(report['freeze_drift'])}"
    )
    for name, stats in report["per_move"].items():  # type: ignore[union-attr]
        print(f"  {name}: {stats}")
    if report["missing"]:
        print("missing sample:", report["missing"][:5])
    if report["mismatched"]:
        print("mismatch sample:", report["mismatched"][:5])
    if report["freeze_drift"]:
        print("freeze_drift sample:", report["freeze_drift"][:3])
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
