from pathlib import Path
import subprocess, sys, tempfile

repo = Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as td:
    root = Path(td) / "matrix"
    root.mkdir()
    (root / "F10_M_only_i10000.txt").write_text("0 0 0\n1 0 0\n0 1 0\n", encoding="ascii")
    (root / "examples").mkdir()
    (root / "examples" / "example_i10000.txt").write_text("0 0 0\n", encoding="ascii")
    out = Path(td) / "resolved.txt"
    cmd = [
        sys.executable, str(repo / "resolve_input.py"),
        "--explicit", str(root),
        "--repo-dir", str(repo),
        "--pattern", "*_i10000.txt",
        "--out-file", str(out),
    ]
    cp = subprocess.run(cmd, text=True, capture_output=True)
    print(cp.stdout, end="")
    if cp.stderr:
        print(cp.stderr, end="", file=sys.stderr)
    assert cp.returncode == 0, cp.returncode
    assert out.exists()
    assert Path(out.read_text(encoding="utf-8").strip()).resolve() == root.resolve()
print("RESOLVER SELFTEST PASS")
