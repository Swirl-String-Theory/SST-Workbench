"""Fail-closed restore for two omitted v1.1.0 runtime sources in A077.

No mutation of any preexisting file, snapshot manifest, or scientific protocol.
"""
from __future__ import annotations
import argparse, hashlib, json, os, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent

def digest(p: Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def run(instance: Path, verify_only: bool = False) -> int:
    instance = instance.resolve()
    runtime = instance / '_sst_runtime'
    snapshot_file = runtime / 'RUNTIME_SNAPSHOT_MANIFEST.json'
    pack_info = HERE / 'PATCH_MANIFEST.json'
    if not snapshot_file.is_file() or not pack_info.is_file():
        print('[RESTORE][REFUSED] Required runtime/patch manifests absent.', file=sys.stderr)
        return 2
    try:
        expected = json.loads(snapshot_file.read_text(encoding='utf-8'))
        patch = json.loads(pack_info.read_text(encoding='utf-8'))
        if expected.get('version') != '1.1.0' or patch.get('framework_version') != '1.1.0':
            raise ValueError('Unexpected framework version')
        inventory = {x['path']:x for x in expected['files']}
        planned = {x['path']:x for x in patch['files']}
        if set(planned) != {'sst_falsifier/outputs.py','tests/test_outputs.py'}:
            raise ValueError('Patch contains unexpected paths')
        missing=[]
        other=[]
        for rel,item in inventory.items():
            if Path(rel).is_absolute() or '..' in Path(rel).parts:
                raise ValueError('Invalid runtime inventory path: '+rel)
            f=runtime/rel
            if not f.is_file():
                if rel in planned:
                    missing.append(rel)
                else:
                    other.append('MISSING: '+rel)
            elif digest(f)!=item['sha256']:
                other.append('HASH_MISMATCH: '+rel)
        for rel,item in planned.items():
            if rel not in inventory or inventory[rel]['sha256'] != item['sha256']:
                raise ValueError('Patch source not authorized by installed snapshot: '+rel)
            src = HERE / 'files' / rel
            if not src.is_file() or digest(src) != item['sha256'] or src.stat().st_size!=item['size_bytes']:
                raise ValueError('Patch file altered/missing: '+rel)
        if other:
            print('[RESTORE][REFUSED] Non-patch runtime problems:',file=sys.stderr)
            for problem in other:print(' - '+problem,file=sys.stderr)
            print('No file written.',file=sys.stderr)
            return 3
        if verify_only:
            if missing:
                print('[RESTORE][VERIFY] Missing: '+', '.join(missing))
                return 4
            print('[RESTORE][PASS] All '+str(len(inventory))+' runtime inventory files match SHA-256.')
            return 0
        if not missing:
            print('[RESTORE][PASS] No restoration needed; all '+str(len(inventory))+' files are intact.')
            return 0
        # Prevalidated sources. Exclusive creation prevents overwriting any existing file.
        for rel in missing:
            dst = runtime/rel
            dst.parent.mkdir(parents=True,exist_ok=True)
            try:
                with dst.open('xb') as f:
                    f.write((HERE/'files'/rel).read_bytes())
            except FileExistsError:
                print('[RESTORE][REFUSED] File appeared while restoring: '+rel,file=sys.stderr)
                return 5
            if digest(dst) != inventory[rel]['sha256']:
                print('[RESTORE][FAIL] Post-write hash mismatch: '+rel,file=sys.stderr)
                return 6
            print('[RESTORE][RESTORED] '+rel)
        for rel,item in inventory.items():
            if not (runtime/rel).is_file() or digest(runtime/rel) != item['sha256']:
                print('[RESTORE][FAIL] Full snapshot validation failed at '+rel,file=sys.stderr)
                return 7
        print('[RESTORE][PASS] Complete v1.1.0 runtime inventory validated: '
              +str(len(inventory))+'/'+str(len(inventory))+' source files. Manifest unchanged.')
        return 0
    except (ValueError,KeyError,TypeError,PermissionError,OSError,json.JSONDecodeError) as e:
        print('[RESTORE][REFUSED] '+str(e),file=sys.stderr)
        return 8

if __name__=='__main__':
    p=argparse.ArgumentParser(description='Verify and safely restore A077 embedded framework files')
    p.add_argument('--instance',type=Path,default=HERE.parent,help='A077 version directory (default: patch parent)')
    p.add_argument('--verify-only',action='store_true')
    a=p.parse_args()
    sys.exit(run(a.instance,a.verify_only))
