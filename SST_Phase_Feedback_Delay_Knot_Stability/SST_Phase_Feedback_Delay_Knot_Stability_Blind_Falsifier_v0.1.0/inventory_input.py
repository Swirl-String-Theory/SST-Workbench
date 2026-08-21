from pathlib import Path
import os, re
from collections import Counter

roots = [
    Path(r"C:\workspace\solo_projects\SST-Workbench"),
    Path(r"C:\workspace\solo\_projects\SST-Workbench"),
]
patterns = ["*_i00000.txt", "*_i01000.txt", "*_i04000.txt", "*_i10000.txt"]
print("SST Phase-Delay input inventory")
print("=" * 72)
found_any = False
for root in roots:
    if not root.is_dir():
        print(f"[missing root] {root}")
        continue
    print(f"\nROOT: {root}")
    for pat in patterns:
        files = [p for p in root.rglob(pat) if p.is_file()]
        print(f"  {pat:<16} {len(files):6d}")
        by_parent = Counter(p.parent for p in files)
        for parent, n in by_parent.most_common(20):
            print(f"      [{n:4d}] {parent}")
        if files:
            found_any = True
if not found_any:
    print("\nNo KnotPlot checkpoint text files were found in either SST-Workbench tree.")
    raise SystemExit(2)
