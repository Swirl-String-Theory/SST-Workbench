from pathlib import Path
import sys

root = Path(__file__).resolve().parent
bad = []
for p in sorted(root.glob("*.cmd")):
    b = p.read_bytes()
    literal = b.count(b"\\r\\n")
    crlf = b.count(b"\r\n")
    lf = b.count(b"\n")
    print(f"{p.name:28s} literal\\r\\n={literal:2d} CRLF={crlf:2d} LF={lf:2d}")
    if literal:
        bad.append(p.name)
if bad:
    print("ERROR: literal \\r\\n sequences found in CMD files:")
    for x in bad:
        print("  ", x)
    raise SystemExit(2)
print("CMD LINE-ENDING AUDIT PASS")
