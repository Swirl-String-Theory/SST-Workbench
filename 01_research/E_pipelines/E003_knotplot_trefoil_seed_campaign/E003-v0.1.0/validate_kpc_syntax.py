from __future__ import annotations
from pathlib import Path
import re, sys

ROOT = Path(__file__).resolve().parent

FORBIDDEN = {
    "nbeads": "obsolete on target; use `refine nbeads`",
    "charge": "target log: unknown command",
    "hooke": "target log: unknown command",
    "power": "target log: unknown command",
    "timeincr": "target log: unknown command",
    "alex": "external KP-alex.exe unavailable on target",
}

# Command heads known from the user's working build_knot_0.1.kpc
# plus save/coords and stop, which are confirmed by target logs.
ALLOWED = {
    "%", "reset", "load", "refine", "mode", "centre", "fitto",
    "collision", "close", "max-dr", "mechforce", "elecforce",
    "bendforce", "bencon", "stusplit", "dstep", "bradius",
    "cradius", "energy", "echo", "safe", "dowker", "lnknum",
    "length", "distance", "angle", "acn", "save", "coords",
    "ago", "stop",
}

def audit_file(path: Path):
    problems = []
    for ln, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        s = raw.strip()
        if not s or s.startswith("%"):
            continue
        head = s.split()[0].lower()

        if head in FORBIDDEN:
            problems.append((ln, f"FORBIDDEN `{head}`: {FORBIDDEN[head]}", raw))
            continue

        if head not in ALLOWED:
            problems.append((ln, f"UNREGISTERED command `{head}`", raw))
            continue

        if head == "refine" and not re.fullmatch(r"refine\s+nbeads\s+300", s, re.I):
            problems.append((ln, "refine syntax must be exactly `refine nbeads 300`", raw))

    return problems

def main():
    files = [ROOT/"00_export_base.kpc"] + sorted((ROOT/"kpc/full").glob("*.kpc"))
    if not files:
        print("ERROR: no KPC files found")
        return 2

    bad = 0
    for p in files:
        problems = audit_file(p)
        if problems:
            bad += 1
            print(f"[KPC AUDIT] FAIL {p.relative_to(ROOT)}")
            for ln, msg, raw in problems[:20]:
                print(f"  line {ln}: {msg}")
                print(f"      {raw}")
        else:
            print(f"[KPC AUDIT] PASS {p.relative_to(ROOT)}")

    if bad:
        print(f"KPC SYNTAX AUDIT FAILED: {bad}/{len(files)} files")
        return 3

    print(f"KPC SYNTAX AUDIT PASS: {len(files)}/{len(files)} files")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
