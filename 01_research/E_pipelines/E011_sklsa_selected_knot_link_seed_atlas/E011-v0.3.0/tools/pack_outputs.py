from __future__ import annotations
from pathlib import Path
import argparse, hashlib, zipfile

HERE = Path(__file__).resolve().parents[1]
DEFAULT_NAME = "E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-root", default=str(HERE / DEFAULT_NAME))
    ap.add_argument("--zip-path")
    args = ap.parse_args()
    src = Path(args.output_root)
    if not src.is_dir():
        raise SystemExit(f"output folder not found: {src}")
    zip_path = Path(args.zip_path) if args.zip_path else HERE.parent / f"{src.name}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for p in sorted(src.rglob("*")):
            if p.is_file():
                zf.write(p, arcname=f"{src.name}/{p.relative_to(src).as_posix()}")
    h = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    zip_path.with_suffix(zip_path.suffix + ".sha256").write_text(f"{h}  {zip_path.name}\n", encoding="utf-8")
    print(zip_path)
    print(h)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
