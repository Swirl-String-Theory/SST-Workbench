from pathlib import Path
import sys

arg = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("build/resolved_input.txt")
if arg.is_file() and arg.name == "resolved_input.txt":
    root = Path(arg.read_text(encoding="utf-8").strip())
else:
    root = arg

files = sorted(root.glob("*_i10000.txt"))
print(f"[PFD] Dataset: {root}")
print(f"[PFD] Direct production i10000 files: {len(files)}")
if len(files) < 8:
    print("[PFD] INSUFFICIENT for confirmatory gate (need >= 8)")
    raise SystemExit(2)
print("[PFD] SAMPLE-SIZE PASS")
