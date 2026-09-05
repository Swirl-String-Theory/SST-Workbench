"""Import the VortexLab spec-clock-proxy-decomposition campaign and its analyses.

The campaign is one coherent run series from 2026-07-15 to 2026-07-18 across VortexLab
7.6.22 to 7.6.25b: session logs, decomposition results and CSV summaries, about 513 MB.

It lands in 03_data/D_generated/ and stays **gitignored**. That follows the restructure
invariant that outputs are runtime artifacts: they live in the catalog where they belong
but do not enter git history unless a specific run is registered as scientifically
relevant.

The handful of VortexLab analysis documents are different - they are written arguments,
not run output - so those are tracked under 10_docs/architecture/.

Run with --apply to write; default is a dry run.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WB = Path(__file__).resolve().parents[1]
DOWNLOADS = Path.home() / "Downloads"

RUNS_HOME = WB / "03_data" / "D_generated" / "vortexlab_spec_clock_runs"
DOCS_HOME = WB / "10_docs" / "architecture"

RUN_FILE = re.compile(r"^vortexlab-(session|spec-clock-proxy)", re.I)
RUN_SUFFIXES = {".txt", ".json", ".csv"}

#: Analyses and roadmaps: arguments about the Workbench, not run output.
DOCS = {
    "SSTCORE_VORTEXLAB_CAPABILITY_GAP_ANALYSIS.md",
    "VortexLab-hoge-resolutie-analyse-en-roadmap-v7.6.23-v7.7.0.md",
    "VortexLab-v7_6_21-speculatieve-herinterpretatie.md",
    "Minimale-ropelength-trefoil.md",
    "sst_source_map_open_frontiers.md",
}

DUP = re.compile(r"\s*\(\d+\)(?=\.[^.]+$)")


def clean(name: str) -> str:
    return DUP.sub("", name)


def plan() -> tuple[list[tuple[Path, Path]], list[tuple[Path, Path]]]:
    runs: list[tuple[Path, Path]] = []
    docs: list[tuple[Path, Path]] = []
    for item in sorted(DOWNLOADS.iterdir()):
        if not item.is_file():
            continue
        name = clean(item.name)
        if item.suffix.lower() in RUN_SUFFIXES and RUN_FILE.match(item.name):
            runs.append((item, RUNS_HOME / name))
        elif name in DOCS:
            docs.append((item, DOCS_HOME / name))
    return runs, docs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    runs, docs = plan()
    run_mb = sum(s.stat().st_size for s, _ in runs) / 1024 / 1024
    doc_mb = sum(s.stat().st_size for s, _ in docs) / 1024 / 1024

    print(f"campaign run files : {len(runs)}  ({run_mb:.1f} MB)  -> "
          f"{RUNS_HOME.relative_to(WB).as_posix()}  [gitignored]")
    print(f"analysis documents : {len(docs)}  ({doc_mb:.1f} MB)  -> "
          f"{DOCS_HOME.relative_to(WB).as_posix()}  [tracked]")
    for _src, dst in docs:
        print(f"    {dst.name}")

    if not args.apply:
        print("\n(dry run)")
        return 0

    for home in (RUNS_HOME, DOCS_HOME):
        home.mkdir(parents=True, exist_ok=True)

    copied = skipped = 0
    for src, dst in runs + docs:
        if dst.exists() and dst.stat().st_size == src.stat().st_size:
            skipped += 1
            continue
        shutil.copy2(src, dst)
        copied += 1
    print(f"\ncopied {copied}, skipped {skipped} already present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
