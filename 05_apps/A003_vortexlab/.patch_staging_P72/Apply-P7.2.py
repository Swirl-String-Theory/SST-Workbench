#!/usr/bin/env python3
"""P7 v0.7.2 / CMD-r1. Preserve local package.json; strict code source hashes."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for part in iter(lambda:f.read(1024*1024),b''): h.update(part)
    return h.hexdigest()

def fail(message): raise RuntimeError(message)

def main():
    default=Path(r'C:\workspace\projects\SST-Workbench\05_apps\A003_vortexlab') if os.name=='nt' else None
    parser=argparse.ArgumentParser(description='A003 TwistFlow P7 v0.7.2 installer (CMD-r1).')
    parser.add_argument('--target',type=Path,default=default,required=default is None,
                        help='Existing A003_vortexlab root folder')
    parser.add_argument('--dry-run',action='store_true',help='Check exact source versions and exit')
    parser.add_argument('--skip-tests',action='store_true',help='Not recommended: skip post-install regression tests')
    args=parser.parse_args()
    root=args.target.resolve(strict=True)
    patch_root=Path(__file__).resolve().parent
    manifest=json.loads((patch_root/'P72_PATCH_MANIFEST.json').read_text(encoding='utf-8'))
    if manifest['version']!='v0.7.2': fail('Unsupported manifest version')
    if not (root/'package.json').is_file() or not (root/'apps/web').is_dir():
        fail(f'Not an A003 VortexLab root: {root}')
    # Do not compare or write the local package.json: user may have installed
    # dependencies or made independent script changes. Validate only the
    # essential project identity + start contract; all actual physics/runtime
    # source files remain subject to exact SHA-256 checks below.
    package_path=root/'package.json'
    try:
        package=json.loads(package_path.read_text(encoding='utf-8-sig'))
    except (OSError, ValueError) as exc:
        fail(f'Unparseable local package.json (preserved): {exc}')
    if (not isinstance(package,dict) or
        package.get('name')!='vortexlab-modular' or
        not isinstance(package.get('scripts'),dict) or
        package['scripts'].get('start')!='node tools/serve.mjs'):
        fail('Local package.json is not recognizable as the expected A003 VortexLab project; not overwritten')
    print(f'PRESERVE local package.json (not replaced); SHA256={digest(package_path)}',flush=True)
    items=[];installed=0
    for f in manifest['files']:
        rel=Path(f['path'])
        if rel.is_absolute() or '..' in rel.parts: fail('Unsafe relative path: '+f['path'])
        src=patch_root/'payload'/rel
        dst=root/rel
        if not src.is_file(): fail(f'Missing patch payload: {rel}')
        if digest(src)!=f['patched_sha256']:fail(f'Payload SHA256 mismatch: {rel}')
        parent=f['parent_sha256']
        if parent is None:
            if dst.exists():
                if dst.is_file() and digest(dst)==f['patched_sha256']:
                    installed+=1
                else: fail(f'Existing new-file collision: {dst}')
        elif not dst.is_file():
            fail(f'Required original file missing: {dst}')
        else:
            actual=digest(dst)
            if actual==f['patched_sha256']:
                installed+=1
            elif actual != parent:
                fail(f'EXISTING MODIFIED FILE - REFUSED: {dst}; SHA256={actual}')
        items.append((rel,src,dst,parent))
    if installed and installed != len(items):
        fail(f'PARTIALLY INSTALLED PATCH - REFUSED: {installed}/{len(items)} payload files already patched')
    if installed==len(items):
        print('PASS: P7 v0.7.2 source files already installed; local package.json unchanged.')
        return 0
    print(f'PASS preflight: {len(items)} versioned payload files match exact source; P7 v0.7.2 CMD-r1')
    if args.dry_run:
        print('DRY RUN: no files changed.')
        return 0
    backup=root/'.A003_P72_backups'/('CMD_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    # Back up all originals before touching the project.
    backup.mkdir(parents=True,exist_ok=False)
    for rel,src,dst,parent in items:
        if parent is not None:
            b=backup/rel;b.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(dst,b)
    applied=[]
    try:
        for rel,src,dst,parent in items:
            # Prevent stale preflight if files changed during the backup phase.
            if parent is not None and digest(dst)!=parent: fail(f'RACE: original changed before install: {rel}')
            if parent is None and dst.exists():fail(f'RACE: new file appeared: {rel}')
            dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(src,dst)
            applied.append((rel,dst,parent))
            if digest(dst)!=digest(src):fail(f'Copy verification failed: {rel}')
        if not args.skip_tests:
            # Run all required tests directly: tests do not depend on any
            # potentially customized package.json scripts.
            testfiles=[
                'apps/web/src/legacy/vortexlab-runtime.js',
                'apps/web/twist-flow/twist-flow.js',
                'tools/test-model-a-ideal-stretch.mjs',
                'tools/test-tube-ropelength-p71.mjs',
                'tools/test-ideal-volume-transfer-p72.mjs',
                'tools/test-twist-flow.mjs',
                'tools/test-twist-flow-motion-p4.mjs',
                'tools/test-twist-flow-current-motion.mjs',
                'tools/test-tube-probe-motion.mjs',
                'tools/test-native-resolution.mjs',
                'tools/test-native-runtime.mjs',
                'tools/test-parse-xyz.mjs',
                'tools/test-catalog-geometry.mjs',
                'tools/test-fluid-qualification.mjs',
                'tools/test-twist-flow-cfl-p5.mjs',
                'tools/verify-parity.mjs',
            ]
            commands=[['node',f] if f.endswith('.mjs') else ['node','--check',f] for f in testfiles]
            for command in commands:
                print('RUN: '+' '.join(command),flush=True)
                result=subprocess.run(command,cwd=root,shell=(os.name=='nt'),check=False)
                if result.returncode:fail(f'TEST FAILED: {" ".join(command)} exited {result.returncode}')
        print(f'P7 v0.7.2 installed (CMD-r1). Backup: {backup}; package.json preserved.')
        print('Note: npm run check may also require the native Node.js sst-core addon; Python pip SSTcore is separate.')
        return 0
    except BaseException:
        print('ERROR: rolling back all modified files.',file=sys.stderr,flush=True)
        for rel,dst,parent in reversed(applied):
            if parent is None:
                dst.unlink(missing_ok=True)
            else:
                shutil.copy2(backup/rel,dst)
        raise

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:
        print(f'INSTALL REFUSED/FAILED: {exc}',file=sys.stderr)
        sys.exit(1)
