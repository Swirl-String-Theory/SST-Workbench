#!/usr/bin/env python3
"""A006 v0.4.2b in-place PATCH. Strict v0.4.2a prerequisite, no run_all edits.

The previous generator and helpers are backed up; existing XYZ never overwritten.
Never writes KPC/KPT or modifies shortcut, knotplotrc, seed/ or existing runs.
"""
from pathlib import Path
import argparse,hashlib,json,os,shutil,sys,tempfile

HERE=Path(__file__).resolve().parent
DEST='extensions/borromean/whole'
FILES=('build_whole.py','strict_xyz.py','run_whole.cmd','test_whole.py')
BACK='patch_backups/A006_BORROMEAN_v0.4.2b'

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def inspect(root):
    root=root.resolve(); dest=root/DEST
    manifest=root/'SEED_MANIFEST.json'
    if not manifest.is_file() or json.loads(manifest.read_text()).get('version')!='0.4.0':
        raise RuntimeError('Expected A006-v0.4.0_TWIST_TORUS_MATRIX')
    if not (root/'extensions/borromean/run_borromean.cmd').exists():
        raise RuntimeError('Borromean v0.4.1 dispatcher not installed')
    receipts=('PATCH_RECEIPT.json','XYZ_ONLY_PATCH_RECEIPT.json')
    if any(not (dest/x).is_file() for x in receipts):
        raise RuntimeError('Install v0.4.2 and v0.4.2a before v0.4.2b')
    if json.loads((dest/receipts[1]).read_text()).get('patch')!='XYZ_ONLY_v0.4.2a':
        raise RuntimeError('Wrong v0.4.2a receipt')
    if (dest/'CLOSURE_PATCH_RECEIPT.json').exists():
        raise RuntimeError('Already installed v0.4.2b; no overwrite')
    if (root/BACK).exists():
        raise RuntimeError('Backup path already exists: '+str(root/BACK))
    expected=json.loads((HERE/'expected_v042a_sha256.json').read_text())
    for file in FILES:
        p=dest/file
        if not p.is_file():raise RuntimeError('Missing original '+file)
        if digest(p)!=expected[file]:
            raise RuntimeError('Unrecognized local modifications in '+file+': '+digest(p))
    # Verify patch content wasn't locally substituted
    new=json.loads((HERE/'patch_sha256.json').read_text())
    for file in FILES:
        src=HERE/'payload'/DEST/file
        if digest(src)!=new[file]:raise RuntimeError('Bad patch payload checksum for '+file)
    return dest,root/BACK

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--base',required=True,type=Path)
    x=parser.add_mutually_exclusive_group(required=True)
    x.add_argument('--check',action='store_true')
    x.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    base=args.base.resolve()
    try:dest,backup=inspect(base)
    except Exception as e:sys.exit('PATCH REJECTED: '+str(e))
    print('TARGET PASS:',base)
    print('Originals hash-qualified. New patch files hash-qualified.')
    print('Preserved: run_all, shortcuts, RC, seed exports, output/borromean old files')
    if args.check:
        print('CHECK-ONLY PASS; no changes.')
        return
    backup.mkdir(parents=True,exist_ok=False)
    updated=[]
    try:
        for filename in FILES:
            shutil.copy2(dest/filename,backup/filename)
        for filename in FILES:
            src=HERE/'payload'/DEST/filename
            tmp=dest/(filename+'.v042b.tmp')
            shutil.copyfile(src,tmp)
            os.replace(tmp,dest/filename)
            updated.append(filename)
        (dest/'CLOSURE_PATCH_RECEIPT.json').write_text(json.dumps({
            'patch':'A006_BORROMEAN_WHOLE_v0.4.2b',
            'source':'A006 v0.4.0 + v0.4.1 + v0.4.2 + v0.4.2a',
            'updated':list(FILES),'backups':str(backup.relative_to(base)),
            'outputs_suffix':'_v042b.xyz',
            'existing_outputs_unchanged':True,
            'KnotPlot_runtime':'NOT_RUN',
            'true_3component_Borromean_link':'UNRESOLVED'},indent=2)+'\n',encoding='utf-8')
    except Exception:
        for filename in updated:
            shutil.copy2(backup/filename,dest/filename)
        for filename in FILES:
            (dest/(filename+'.v042b.tmp')).unlink(missing_ok=True)
        (dest/'CLOSURE_PATCH_RECEIPT.json').unlink(missing_ok=True)
        shutil.rmtree(backup,ignore_errors=True)
        raise
    print('PATCH APPLIED: v0.4.2b. Run run_all.cmd BORROMEAN WHOLE TEST, then BUILD.')

if __name__=='__main__':main()
