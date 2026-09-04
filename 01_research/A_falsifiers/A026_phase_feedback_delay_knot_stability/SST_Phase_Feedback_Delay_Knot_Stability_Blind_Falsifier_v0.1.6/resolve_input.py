from __future__ import annotations

import argparse
import os
import re
from collections import Counter
from pathlib import Path

TARGET_BASENAME = "KnotPlot_3p1_MultiDynamics_Relaxation_Matrix_v0.1.0"
EXCLUDED_DIR_NAMES = {
    "example", "examples", "result", "results", "blind_work",
    "private_reveal", "__pycache__", ".venv", "build", "reference_fallback_quick"
}


def full(p: str | Path) -> Path:
    return Path(p).expanduser().resolve(strict=False)


def is_excluded_path(p: Path) -> bool:
    return any(part.lower() in EXCLUDED_DIR_NAMES for part in p.parts)


def add_unique(seq: list[Path], p: str | Path | None) -> None:
    if p is None or str(p).strip() == "":
        return
    q = full(p)
    key = os.path.normcase(str(q))
    if all(os.path.normcase(str(x)) != key for x in seq):
        seq.append(q)


def direct_hits(directory: Path, pattern: str) -> list[Path]:
    """Production matrix outputs are expected directly in the matrix output folder."""
    if not directory.is_dir():
        return []
    try:
        return [p for p in directory.glob(pattern) if p.is_file() and not is_excluded_path(p)]
    except OSError:
        return []


def recursive_hits(directory: Path, pattern: str) -> list[Path]:
    if not directory.is_dir():
        return []
    try:
        return [p for p in directory.rglob(pattern) if p.is_file() and not is_excluded_path(p)]
    except OSError:
        return []


def recursive_all_hits(directory: Path, pattern: str) -> list[Path]:
    """Diagnostic-only search including examples."""
    if not directory.is_dir():
        return []
    try:
        return [p for p in directory.rglob(pattern) if p.is_file()]
    except OSError:
        return []


def checkpoint_summary(directory: Path, include_examples: bool = False) -> Counter[str]:
    out: Counter[str] = Counter()
    source = recursive_all_hits(directory, "*_i*.txt") if include_examples else recursive_hits(directory, "*_i*.txt")
    for p in source:
        m = re.search(r"_i([0-9]+)\.txt$", p.name, re.IGNORECASE)
        if m:
            out["i" + m.group(1)] += 1
    return out


def matrix_like(name: str) -> bool:
    s = name.lower()
    return any(k in s for k in ("multidynamics", "relaxation", "matrix", "_3p1"))


def write_out(path: Path, outfile: Path) -> None:
    outfile.parent.mkdir(parents=True, exist_ok=True)
    outfile.write_text(str(path), encoding="utf-8")


def candidate_roots(repo: Path) -> tuple[list[Path], list[Path]]:
    roots: list[Path] = []
    broad_roots: list[Path] = []

    add_unique(roots, repo / ".." / "KnotPlot")
    add_unique(roots, repo / ".." / ".." / "KnotPlot")

    rtxt = str(repo)
    low = rtxt.lower()
    if "\\projects\\" in low:
        i = low.index("\\projects\\")
        alt = rtxt[:i] + "\\projects\\" + rtxt[i + len("\\projects\\"):]
        add_unique(roots, Path(alt) / ".." / ".." / "KnotPlot")
        add_unique(roots, Path(alt) / ".." / "KnotPlot")
    if "\\projects\\" in low:
        i = low.index("\\projects\\")
        alt = rtxt[:i] + "\\projects\\" + rtxt[i + len("\\projects\\"):]
        add_unique(roots, Path(alt) / ".." / ".." / "KnotPlot")
        add_unique(roots, Path(alt) / ".." / "KnotPlot")

    add_unique(roots, r"C:\workspace\projects\SST-Workbench\KnotPlot")
    add_unique(roots, r"C:\workspace\solo\_projects\SST-Workbench\KnotPlot")

    add_unique(broad_roots, r"C:\workspace\projects\SST-Workbench")
    add_unique(broad_roots, r"C:\workspace\solo\_projects\SST-Workbench")
    for parent in [repo, *repo.parents]:
        if parent.name.lower() == "sst-workbench":
            add_unique(broad_roots, parent)
            break

    return roots, broad_roots


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--explicit", default="")
    ap.add_argument("--repo-dir", required=True)
    ap.add_argument("--pattern", default="*_i10000.txt")
    ap.add_argument("--out-file", required=True)
    a = ap.parse_args()

    repo = full(a.repo_dir)
    outfile = full(a.out_file)
    roots, broad_roots = candidate_roots(repo)
    candidates: list[Path] = []

    if a.explicit:
        add_unique(candidates, a.explicit)

    # Expected layouts.
    add_unique(candidates, repo / ".." / "KnotPlot" / TARGET_BASENAME)
    add_unique(candidates, repo / ".." / ".." / "KnotPlot" / TARGET_BASENAME)
    add_unique(candidates, repo / ".." / "KnotPlot" / "KnotPlot" / "_3p1_MultiDynamics_Relaxation_Matrix_v0.1.0")
    add_unique(candidates, repo / ".." / ".." / "KnotPlot" / "KnotPlot" / "_3p1_MultiDynamics_Relaxation_Matrix_v0.1.0")

    # Explicit path only wins if it contains production final checkpoints,
    # not merely examples/.
    if a.explicit:
        exp = full(a.explicit)
        if exp.is_dir():
            hh = direct_hits(exp, a.pattern)
            if hh:
                write_out(exp, outfile)
                print(f"[PFD] Input: {exp}")
                print(f"[PFD] Production final-checkpoint files: {len(hh)} matching {a.pattern}")
                return 0
            ex = len(recursive_all_hits(exp / "examples", a.pattern)) if (exp / "examples").is_dir() else 0
            print(f"[PFD] Requested input contains 0 production files matching {a.pattern}:")
            print(f"      {exp}")
            if ex:
                print(f"[PFD] Ignoring {ex} example checkpoint(s) under examples\\.")
            print("[PFD] Searching other KnotPlot locations...")

    # Discover matrix-like directories beneath expected KnotPlot roots.
    for root in roots:
        if not root.is_dir():
            continue
        root = full(root)
        try:
            for base, dirs, _files in os.walk(root):
                rel = Path(base).relative_to(root)
                # Do not descend into known non-production trees.
                dirs[:] = [d for d in dirs if d.lower() not in EXCLUDED_DIR_NAMES]
                if len(rel.parts) >= 5:
                    dirs[:] = []
                    continue
                for d in dirs:
                    if matrix_like(d):
                        add_unique(candidates, Path(base) / d)
        except OSError:
            pass

    scored: dict[str, tuple[Path, int]] = {}

    def score(path: Path, count: int) -> None:
        q = full(path)
        if is_excluded_path(q):
            return
        key = os.path.normcase(str(q))
        old = scored.get(key)
        if old is None or count > old[1]:
            scored[key] = (q, count)

    # Preferred: direct files in a matrix root.
    for c in candidates:
        if c.is_dir():
            hh = direct_hits(c, a.pattern)
            if hh:
                score(c, len(hh))

    # Fallback: group production final checkpoints by their actual parent.
    if not scored:
        print("[PFD] No direct production final checkpoints found in expected matrix roots.")
        print("[PFD] Broad-searching SST-Workbench, excluding examples/results/build trees ...")
        for root in [*roots, *broad_roots]:
            if not root.is_dir():
                continue
            groups: Counter[Path] = Counter(p.parent for p in recursive_hits(root, a.pattern))
            for parent, count in groups.items():
                score(parent, count)

    ranked = sorted(scored.values(), key=lambda x: (-x[1], str(x[0]).lower()))
    if ranked:
        top_count = ranked[0][1]
        top = [x for x in ranked if x[1] == top_count]
        preferred = [x for x in top if x[0].name.lower() == TARGET_BASENAME.lower()]
        if len(preferred) == 1:
            top = preferred
        if len(top) != 1:
            print(f"ERROR: Multiple production input directories tie with {top_count} final-checkpoint files.")
            for p, n in top:
                print(f"  [{n}] {p}")
            print("Pass the desired production directory explicitly to run_all.cmd.")
            return 3
        resolved, n = top[0]
        write_out(resolved, outfile)
        print(f"[PFD] Auto-resolved production input: {resolved}")
        print(f"[PFD] Production final-checkpoint files: {n} matching {a.pattern}")
        return 0

    print(f"ERROR: No production files matching {a.pattern} were found.")
    print("Example/reference files are intentionally excluded from the blind campaign.")
    print()
    print("Checkpoint diagnostics (production only):")
    reported = False
    seen: set[str] = set()
    for root in [*roots, *broad_roots]:
        key = os.path.normcase(str(full(root)))
        if key in seen or not root.is_dir():
            continue
        seen.add(key)
        summary = checkpoint_summary(root, include_examples=False)
        if summary:
            reported = True
            print(f"  Root: {full(root)}")
            def ikey(x: str) -> int:
                try:
                    return int(x[1:])
                except ValueError:
                    return 0
            for k in sorted(summary, key=ikey):
                print(f"    {k:<10} {summary[k]:6d} files")
    if not reported:
        print("  No production *_i*.txt checkpoints were found.")

    example_count = 0
    for root in [*roots, *broad_roots]:
        if root.is_dir():
            for p in recursive_all_hits(root, a.pattern):
                if is_excluded_path(p):
                    example_count += 1
    if example_count:
        print()
        print(f"[PFD] Found {example_count} excluded example/result final checkpoint(s); these are not scientific inputs.")

    print()
    print("The preregistered campaign requires real KnotPlot i10000 outputs.")
    print('After the matrix has produced them, retry:')
    print('  run_04_inventory_input.cmd')
    print('  run_05_find_input.cmd')
    print('  run_all.cmd')
    return 2


if __name__ == "__main__":
    raise SystemExit(main())