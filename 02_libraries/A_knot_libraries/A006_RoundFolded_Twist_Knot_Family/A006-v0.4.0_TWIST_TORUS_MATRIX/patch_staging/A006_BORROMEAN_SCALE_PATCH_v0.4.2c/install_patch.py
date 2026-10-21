#!/usr/bin/env python3
"""v0.4.2c add-on for an installed v0.4.2b A006 whole-component builder.

Fail-closed hash-qualified installer. Only replaces the three extension modules.
Does not edit run_all.cmd, KnotPlot preferences, shortcuts or prior outputs.
"""
from pathlib import Path
import argparse,hashlib,json,shutil,sys,os

HERE=Path(__file__).resolve().parent
DEST=Path('extensions/borromean/whole')
FILES=('build_whole.py','run_whole.cmd','test_whole.py')
BACK=Path('patch_backups/A006_BORROMEAN_v0.4.2c')
RECEIPT='SCALE_PATCH_RECEIPT.json'

def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def inspect(base):
    base=base.resolve(); dst=base/DEST
    p=base/'SEED_MANIFEST.json'
    if not p.exists() or json.loads(p.read_text()).get('version')!='0.4.0':
        raise RuntimeError('Not the v0.4.0 TWIST_TORUS_MATRIX base')
    cp=dst/'CLOSURE_PATCH_RECEIPT.json'
    if not cp.is_file() or json.loads(cp.read_text()).get('patch')!='A006_BORROMEAN_WHOLE_v0.4.2b':
        raise RuntimeError('v0.4.2b closure patch must be installed first')
    if (dst/RECEIPT).exists() or (base/BACK).exists():
        raise RuntimeError('Patch already installed or backup conflict')
    old=json.loads((HERE/'expected_v042b_sha256.json').read_text())
    new=json.loads((HERE/'patch_sha256.json').read_text())
    for name in FILES:
        dstfile=dst/name; src=HERE/'payload'/DEST/name
        if not dstfile.is_file() or digest(dstfile)!=old[name]:
            raise RuntimeError('Installed module modified or unknown: '+str(dstfile))
        if not src.is_file() or digest(src)!=new[name]:
            raise RuntimeError('Corrupted replacement: '+str(src))
    if not (dst/'strict_xyz.py').is_file():
        raise RuntimeError('Strict XYZ writer missing')
    return dst,base/BACK

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--base',type=Path,required=True)
    act=ap.add_mutually_exclusive_group(required=True)
    act.add_argument('--check',action='store_true')
    act.add_argument('--apply',action='store_true')
    args=ap.parse_args()
    root=args.base.resolve()
    try: dst,backup=inspect(root)
    except Exception as e:sys.exit('PATCH REJECTED: '+str(e))
    print('TARGET PASS:',root)
    print('v0.4.2b module SHA-256 verified; new payload SHA-256 verified')
    if args.check:
        print('CHECK-ONLY PASS; no files changed')
        return
    backup.mkdir(parents=True,exist_ok=False)
    updated=[]
    try:
        for fn in FILES: shutil.copy2(dst/fn,backup/fn)
        for fn in FILES:
            tmp=dst/(fn+'.v042c.tmp')
            shutil.copyfile(HERE/'payload'/DEST/fn,tmp)
            os.replace(tmp,dst/fn)
            updated.append(fn)
        (dst/RECEIPT).write_text(json.dumps({
            'patch':'A006_BORROMEAN_WHOLE_v0.4.2c',
            'prerequisite':'v0.4.2b',
            'updated':list(FILES),
            'backup':str(backup.relative_to(root)),
            'new_output_suffix':'_v042c.xyz',
            'original_xyz_unchanged':True,
            'run_all_unchanged':True,
            'KnotPlot_runtime':'NOT_RUN',
            'Milnor_mu123':'UNRESOLVED'},indent=2)+'\n')
    except Exception:
        for fn in updated:shutil.copy2(backup/fn,dst/fn)
        for fn in FILES:(dst/(fn+'.v042c.tmp')).unlink(missing_ok=True)
        (dst/RECEIPT).unlink(missing_ok=True)
        shutil.rmtree(backup,ignore_errors=True)
        raise
    print('PATCH INSTALLED v0.4.2c; no run_all.cmd or previous XYZ modified')
    print('Try: run_all.cmd BORROMEAN WHOLE BUILD BALANCED MIN 256')

if __name__=='__main__':main()
