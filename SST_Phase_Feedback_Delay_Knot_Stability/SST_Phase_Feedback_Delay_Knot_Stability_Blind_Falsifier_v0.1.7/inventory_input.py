from pathlib import Path
from collections import Counter

EXCLUDED = {
    "example", "examples", "result", "results", "blind_work",
    "private_reveal", "__pycache__", ".venv", "build", "reference_fallback_quick"
}
roots = [
    Path(r"C:\workspace\projects\SST-Workbench"),
    Path(r"C:\workspace\solo\_projects\SST-Workbench"),
]
patterns = ["*_i00000.txt", "*_i01000.txt", "*_i04000.txt", "*_i10000.txt"]

def excluded(p: Path) -> bool:
    return any(part.lower() in EXCLUDED for part in p.parts)

print("SST Phase-Delay input inventory v0.1.6")
print("=" * 76)

production_final = 0
example_final = 0
existing_root = False

for root in roots:
    if not root.is_dir():
        print(f"[missing root] {root}")
        continue
    existing_root = True
    print(f"\nROOT: {root}")
    for pat in patterns:
        all_files = [p for p in root.rglob(pat) if p.is_file()]
        prod = [p for p in all_files if not excluded(p)]
        excl = [p for p in all_files if excluded(p)]
        print(f"  {pat:<16} production={len(prod):5d}  excluded={len(excl):5d}")
        by_parent = Counter(p.parent for p in prod)
        for parent, n in by_parent.most_common(20):
            print(f"      PROD [{n:4d}] {parent}")
        if pat == "*_i10000.txt":
            production_final += len(prod)
            example_final += len(excl)

print()
if not existing_root:
    print("ERROR: Neither known SST-Workbench root exists.")
    raise SystemExit(3)

if production_final == 0:
    print("NO PRODUCTION FINAL CHECKPOINTS.")
    if example_final:
        print(f"Found {example_final} i10000 file(s) only in excluded example/result directories.")
    print("Run the KnotPlot MultiDynamics relaxation matrix until real *_i10000.txt files exist.")
    raise SystemExit(2)

print(f"INVENTORY PASS: {production_final} production *_i10000.txt file(s) found.")
raise SystemExit(0)