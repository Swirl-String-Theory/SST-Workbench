from __future__ import annotations

import argparse
import os
import re
import sys
from collections import Counter
from pathlib import Path

TARGET_BASENAME = "KnotPlot_3p1_MultiDynamics_Relaxation_Matrix_v0.1.0"


def full(p: str | Path) -> Path:
    return Path(p).expanduser().resolve(strict=False)


def add_unique(seq: list[Path], p: str | Path | None) -> None:
    if p is None or str(p).strip() == "":
        return
    q = full(p)
    key = os.path.normcase(str(q))
    if all(os.path.normcase(str(x)) != key for x in seq):
        seq.append(q)


def hits(directory: Path, pattern: str) -> list[Path]:
    if not directory.is_dir():
        return []
    try:
        return [p for p in directory.rglob(pattern) if p.is_file()]
    except OSError:
        return []


def checkpoint_summary(directory: Path) -> Counter[str]:
    out: Counter[str] = Counter()
    if not directory.is_dir():
        return out
    try:
        for p in directory.rglob("*_i*.txt"):
            if not p.is_file():
                continue
            m = re.search(r"_i([0-9]+)\.txt$", p.name, re.IGNORECASE)
            if m:
                out["i" + m.group(1)] += 1
    except OSError:
        pass
    return out


def matrix_like(name: str) -> bool:
    s = name.lower()
    return any(k in s for k in ("multidynamics", "relaxation", "matrix", "_3p1"))


def write_out(path: Path, outfile: Path) -> None:
    outfile.parent.mkdir(parents=True, exist_ok=True)
    outfile.write_text(str(path), encoding="ascii", errors="strict")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--explicit", default="")
    ap.add_argument("--repo-dir", required=True)
    ap.add_argument("--pattern", default="*_i10000.txt")
    ap.add_argument("--out-file", required=True)
    a = ap.parse_args()

    repo = full(a.repo_dir)
    outfile = full(a.out_file)
    candidates: list[Path] = []
    roots: list[Path] = []

    if a.explicit:
        add_unique(candidates, a.explicit)

    # Normal layouts: falsifier one or two levels below SST-Workbench.
    add_unique(candidates, repo / ".." / "KnotPlot" / TARGET_BASENAME)
    add_unique(candidates, repo / ".." / ".." / "KnotPlot" / TARGET_BASENAME)
    add_unique(candidates, repo / ".." / "KnotPlot" / "KnotPlot" / "_3p1_MultiDynamics_Relaxation_Matrix_v0.1.0")
    add_unique(candidates, repo / ".." / ".." / "KnotPlot" / "KnotPlot" / "_3p1_MultiDynamics_Relaxation_Matrix_v0.1.0")

    add_unique(roots, repo / ".." / "KnotPlot")
    add_unique(roots, repo / ".." / ".." / "KnotPlot")

    # Compatibility for both workspace spellings observed in this campaign.
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
    add_unique(roots, r"C:\workspace\projects\SST-Workbench\KnotPlot")

    # v0.1.5 broad fallback roots: search the complete SST-Workbench tree if the
    # expected KnotPlot roots do not contain the preregistered final checkpoint.
    broad_roots: list[Path] = []
    add_unique(broad_roots, r"C:\workspace\projects\SST-Workbench")
    add_unique(broad_roots, r"C:\workspace\projects\SST-Workbench")

    # Also infer an SST-Workbench ancestor from the falsifier's own location.
    for parent in [repo, *repo.parents]:
        if parent.name.lower() == "sst-workbench":
            add_unique(broad_roots, parent)
            break

    # Explicit valid path always wins.
    if a.explicit:
        exp = full(a.explicit)
        if exp.is_dir():
            hh = hits(exp, a.pattern)
            if hh:
                write_out(exp, outfile)
                print(f"[PFD] Input: {exp}")
                print(f"[PFD] Final-checkpoint files: {len(hh)} matching {a.pattern}")
                return 0
            print(f"[PFD] Requested input exists but contains 0 files matching {a.pattern}:")
            print(f"      {exp}")
            print("[PFD] Searching nearby KnotPlot roots instead...")

    # Add matrix-like candidate directories, capped at a modest depth.
    for root in list(roots):
        if not root.is_dir():
            continue
        root = full(root)
        try:
            for base, dirs, _files in os.walk(root):
                rel = Path(base).relative_to(root)
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
        key = os.path.normcase(str(full(path)))
        old = scored.get(key)
        if old is None or count > old[1]:
            scored[key] = (full(path), count)

    for c in candidates:
        if c.is_dir():
            hh = hits(c, a.pattern)
            if hh:
                score(c, len(hh))

    # Last resort: group final-checkpoint files by parent directory.
    for root in [*roots, *broad_roots]:
        if not root.is_dir():
            continue
        groups: Counter[Path] = Counter(p.parent for p in hits(root, a.pattern))
        for parent, count in groups.items():
            score(parent, count)


    # v0.1.5 final fallback: scan all of SST-Workbench and group matching final
    # checkpoints by their parent directory. This is deliberately only used
    # after the targeted KnotPlot candidates, so unrelated datasets do not win
    # when a normal matrix path is present.
    if not scored:
        print("[PFD] Targeted KnotPlot search found no final checkpoints.")
        print("[PFD] Broad-searching SST-Workbench for *_i10000.txt ...")
        for root in broad_roots:
            if not root.is_dir():
                continue
            groups: Counter[Path] = Counter(p.parent for p in hits(root, a.pattern))
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
            print(f"ERROR: Multiple input directories tie with {top_count} final-checkpoint files.")
            for p, n in top:
                print(f"  [{n}] {p}")
            print("Pass the desired directory explicitly to run_all.cmd.")
            return 3
        resolved, n = top[0]
        write_out(resolved, outfile)
        print(f"[PFD] Auto-resolved by file content: {resolved}")
        print(f"[PFD] Final-checkpoint files: {n} matching {a.pattern}")
        return 0

    print(f"ERROR: No files matching {a.pattern} were found in any candidate KnotPlot dataset.")
    print()
    print("Checkpoint diagnostics:")
    reported = False
    seen: set[str] = set()
    for root in [*roots, *broad_roots]:
        key = os.path.normcase(str(full(root)))
        if key in seen or not root.is_dir():
            continue
        seen.add(key)
        summary = checkpoint_summary(root)
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
        print("  No *_i*.txt KnotPlot checkpoints were found under the searched roots.")
    print()
    print("The blind preregistration requires a common i10000 checkpoint; it will not silently")
    print("fall back to i04000 or i01000.")
    print('Either finish the KnotPlot relaxation matrix to i10000, or pass it explicitly:')
    print(r'  run_all.cmd "C:\path\to\matrix-output" basic')
    return 2


if __name__ == "__main__":
    raise SystemExit(main())