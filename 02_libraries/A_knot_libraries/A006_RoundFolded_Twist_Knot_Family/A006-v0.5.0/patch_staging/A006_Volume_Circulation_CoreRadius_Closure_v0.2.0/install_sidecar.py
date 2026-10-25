"""Create-only, idempotent A006 v0.5.x VCCR sidecar installer. Never patches run_all.cmd.
Usage: py -3 install_sidecar.py --base "C:\\..\\A006-v0.5.0" --check/--apply
"""
import argparse,hashlib,json,shutil,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
DEST_REL=Path('tools/VCCR_v0.2.0')
WRAPPER_NAME='run_vccr_v020.cmd'
WRAPPER='''@echo off
setlocal
pushd "%~dp0tools\\VCCR_v0.2.0" || exit /b 1
call run_vccr.cmd %*
set "CODE=%errorlevel%"
popd
exit /b %CODE%
'''

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def install(base:Path,apply:bool):
    root=base.resolve()
    if not (root/'run_all.cmd').is_file() or not (root/'knotplotrc.kps').is_file():
        raise RuntimeError(f'Not an A006 project root (run_all.cmd/knotplotrc.kps missing): {root}')
    allowed={'vccr','tests','examples','docs'}
    files=[p for p in ROOT.rglob('*') if p.is_file() and (
        p.relative_to(ROOT).parts[0] in allowed or p.parent==ROOT and p.name in
        {'README.md','SCIENCE_CONTRACT.md','FORMULAE.md','FORMULAE_EULER.md','references.tex','requirements.txt','run_vccr.cmd','install_sidecar.py','test_manifest.json','release_manifest.json'})
        and '__pycache__' not in p.parts]
    dst=root/DEST_REL
    mutations=[]; checked=0
    for f in files:
        q=dst/f.relative_to(ROOT)
        if q.exists():
            if sha(q)!=sha(f): raise RuntimeError(f'EXISTING MODIFIED FILE — REFUSED: {q}')
            checked+=1
        else: mutations.append((f,q))
    cmd=root/WRAPPER_NAME
    if cmd.exists():
        if cmd.read_text(encoding='utf-8').replace('\r\n','\n')!=WRAPPER.replace('\r\n','\n'):
            raise RuntimeError('Existing run_vccr_v020.cmd differs; REFUSED')
    else:mutations.append((None,cmd))
    if apply:
        # verify all before writing; never overwrite
        for f,q in mutations:
            q.parent.mkdir(parents=True,exist_ok=True)
            if f is not None: shutil.copy2(f,q)
            else: q.write_text(WRAPPER,encoding='utf-8')
        print(f'INSTALLED {len(mutations)} new files, {checked} already valid. Existing A006 files unchanged.')
    else:
        print(f'CHECK PASS: {len(mutations)} create-only files, {checked} identical files. No changes.')
    print('Run: run_vccr_v020.cmd TEST  |  run_vccr_v020.cmd EULER')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base',required=True);a=p.add_mutually_exclusive_group(required=True);a.add_argument('--check',action='store_true');a.add_argument('--apply',action='store_true');ns=p.parse_args()
    try:install(Path(ns.base),ns.apply)
    except Exception as e:print(f'INSTALL REFUSED: {e}',file=sys.stderr);sys.exit(2)
