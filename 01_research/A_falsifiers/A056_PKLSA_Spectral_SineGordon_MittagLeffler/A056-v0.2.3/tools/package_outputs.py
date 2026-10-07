from pathlib import Path
import hashlib
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'A056-v0.2.3-outputs'
if not OUT.is_dir():
    raise SystemExit(f'missing output directory: {OUT}')

# Load the pinned canonical framework through the same instance resolver. This keeps
# revealed packaging semantics identical to framework v1.0.4 after the private
# smoke validator has appended A056_SMOKE_VALIDATION.json.
sys.path.insert(0,str(ROOT))
import run_instance  # noqa: F401,E402
from sst_falsifier.outputs import pack_revealed  # noqa: E402


def zip_tree(src: Path,dst: Path):
    with zipfile.ZipFile(dst,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(src.rglob('*')):
            if p.is_file() and not any(x in {'.venv','__pycache__','.pytest_cache','build'} for x in p.parts):
                rel=p.relative_to(src)
                info=zipfile.ZipInfo(rel.as_posix(),date_time=(1980,1,1,0,0,0))
                info.compress_type=zipfile.ZIP_DEFLATED
                info.external_attr=(0o100644&0xffff)<<16
                z.writestr(info,p.read_bytes())


def sha(path: Path):
    h=hashlib.sha256(path.read_bytes()).hexdigest()
    path.with_suffix(path.suffix+'.sha256').write_text(f'{h}  {path.name}\n',encoding='utf-8')
    return h

# REVEALED was initially created by framework REVEAL. Refresh it now so the
# post-reveal implementation-validation artifact is included as well.
revealed=ROOT.parent/'A056-v0.2.3-outputs_REVEALED.zip'
if (OUT/'revealed').is_dir():
    pack_revealed(OUT,revealed)

combined=ROOT.parent/'A056-v0.2.3-outputs.zip'
zip_tree(OUT,combined)
for path in (ROOT.parent/'A056-v0.2.3-outputs_BLIND.zip',revealed,combined):
    if path.exists():
        print(f'{path.name}: {sha(path)}')
