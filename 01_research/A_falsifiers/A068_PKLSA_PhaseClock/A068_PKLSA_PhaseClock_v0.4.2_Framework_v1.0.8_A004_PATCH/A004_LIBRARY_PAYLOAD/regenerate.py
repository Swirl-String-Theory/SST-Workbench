#!/usr/bin/env python3
"""Transactional, self-verifying v0.2.2 geometry-only XYZ generator."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import zipfile

import regenerate_v0_2_1 as core
from verify_release import verify_directory

VERSION = "0.2.2"
DEFAULT_N = (600, 1200, 2400, 4800, 9600)

def build(sizes, out_dir: Path, zip_file: Path):
    out_dir=out_dir.resolve(); zip_file=zip_file.resolve()
    if out_dir.exists():
        raise FileExistsError(f"Refusing to overwrite/mix into existing directory: {out_dir}")
    if zip_file.exists():
        raise FileExistsError(f"Refusing to overwrite existing ZIP: {zip_file}")
    if out_dir == zip_file.parent:
        raise ValueError("Output directory and ZIP parent cannot be equal")
    out_dir.parent.mkdir(parents=True,exist_ok=True)
    zip_file.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="._hist022_", dir=out_dir.parent) as tmp:
        staging = Path(tmp)/out_dir.name
        m = core.generate(tuple(dict.fromkeys(sizes)), staging)
        m['version']=VERSION
        m['calculation_core_sha256']=hashlib.sha256(Path(core.__file__).read_bytes()).hexdigest()
        m['original_calculation_core_version']="0.2.1"
        m['generator_fix']="Complete 40-file defaults, fail-closed output directory, independent verification, distributable ZIP"
        (staging/'manifest.json').write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        files=sorted(x for x in staging.iterdir() if x.is_file() and x.suffix == '.xyz')
        with (staging/'SHA256SUMS.txt').open('w',encoding='utf-8',newline='\n') as f:
            for p in [*files,staging/'manifest.json']:
                f.write(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n")
        v=verify_directory(staging)
        if not v['ok']:raise RuntimeError(f"generated source verification failed: {v}")
        staging.rename(out_dir)
    try:
        temp_zip=zip_file.with_name(zip_file.name+'.part')
        if temp_zip.exists():raise FileExistsError(f"Refusing preexisting temporary ZIP: {temp_zip}")
        with zipfile.ZipFile(temp_zip,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as z:
            for p in sorted(out_dir.iterdir()):
                z.write(p,f"{out_dir.name}/{p.name}")
        with zipfile.ZipFile(temp_zip) as z:
            if z.testzip() is not None:raise RuntimeError("ZIP CRC failed")
            if len([x for x in z.namelist() if x.endswith('.xyz')])!=v['count']:raise RuntimeError("ZIP file count mismatch")
        temp_zip.rename(zip_file)
        (zip_file.parent/(zip_file.name+'.sha256')).write_text(hashlib.sha256(zip_file.read_bytes()).hexdigest()+f'  {zip_file.name}\n',encoding='ascii')
    except Exception:
        # Keep complete validated outputs; never leave partially valid ZIP.
        if 'temp_zip' in locals() and temp_zip.exists():temp_zip.unlink()
        raise
    return v

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--n',type=int,nargs='+',default=list(DEFAULT_N),help='Resolution(s) >=600; default 600,1200,2400,4800,9600')
    ap.add_argument('--out',type=Path,default=Path(__file__).resolve().parent/'generated'/f'SST_Historical_Trefoil_XYZ_v{VERSION}')
    ap.add_argument('--zip',type=Path,default=None,help='Output ZIP; default <out>.zip')
    args=ap.parse_args()
    if any(n<600 for n in args.n):ap.error('N must be >=600')
    v=build(args.n,args.out,args.zip or Path(str(args.out)+'.zip'))
    print(f"PASS: {v['count']} XYZ files in {args.out.resolve()} [SHA-256 verified]; ZIP generated")
    print('GEOMETRY ONLY: no physical vortex, Euler convergence or clock claim')
if __name__=='__main__':main()
