#!/usr/bin/env python3
"""Additive, fail-closed patch for A006 RoundFolded NearUnknot v0.4.0."""
import argparse,hashlib,json,os,re,shutil,sys
from pathlib import Path
P=Path(__file__).resolve().parent
MARK='A006_BORROMEAN_V041'
HOOK=f'if /I "%~1"=="BORROMEAN" goto {MARK}'
TAIL=(f':{MARK}\ncall "%~dp0extensions\\borromean\\run_borromean.cmd" %2 %3 %4 %5 %6 %7 %8 %9\nexit /b %errorlevel%\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(root):
    if not root.is_dir():raise RuntimeError('Target directory not found')
    required=['run_all.cmd','README.md','SEED_MANIFEST.json','src/knotplot_io.py','tools/run_campaign.py']
    for file in required:
        if not (root/file).is_file():raise RuntimeError('Missing v0.4.0 base file: '+file)
    readme=(root/'README.md').read_text(encoding='utf-8-sig')
    if 'RoundFolded NearUnknot v0.4.0' not in readme or 'Twist + Near-Circle Torus Knots' not in readme:
        raise RuntimeError('README does not match the audited v0.4.0 release')
    manifest=json.loads((root/'SEED_MANIFEST.json').read_text(encoding='utf-8'))
    if manifest.get('version')!='0.4.0' or manifest.get('count')!=26:
        raise RuntimeError('Unexpected seed manifest version/count')
    expected={(k,n):v['source_sha256'] for v in manifest['seeds'] for k,n in [(v.get('name'),v.get('n'))]}
    for k in ['5_2','6_1']:
      for n in (1024,2048):
        file=root/'output'/'seeds'/f'{k}_N{n}.kpt'
        if not file.is_file() or (k,n) not in expected or sha(file)!=expected[(k,n)]:
            raise RuntimeError(f'Native seed missing or checksum mismatch: {file}')
    run=root/'run_all.cmd';b=run.read_bytes()
    try:s=b.decode('utf-8-sig')
    except UnicodeDecodeError:raise RuntimeError('run_all.cmd encoding unsupported')
    if not re.search(r'(?m)^@echo off\s*$',s,re.I):raise RuntimeError('Unexpected CMD header')
    if any(f'"{x}"' not in s for x in ['BASIC','SMALL','MEDIUM','FULL','PREFLIGHT','ANALYZE']):
        raise RuntimeError('Unexpected v0.4.0 dispatch structure')
    if MARK in s or 'BORROMEAN' in s.upper():raise RuntimeError('Borromean handler already present')
    if (root/'extensions'/'borromean').exists():raise RuntimeError('Extension already exists')
    backup=root/'patch_backups'/'A006_BORROMEAN_v0.4.1'/'run_all.cmd.before'
    if backup.exists():raise RuntimeError('Patch backup already exists; refuse overwrite')
    return run,b,s,backup

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--base',required=True,type=Path)
    group=ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--check',action='store_true');group.add_argument('--apply',action='store_true')
    a=ap.parse_args();r=a.base.resolve()
    try:run,b,s,backup=check(r)
    except Exception as e:sys.exit('PATCH NOT APPLIED: '+str(e))
    print('TARGET PASS:',r,'\nBaseline run_all SHA256:',hashlib.sha256(b).hexdigest())
    if a.check:
        print('CHECK-ONLY PASS; existing shortcuts, RC, seeds, campaigns and output untouched.')
        return
    dest=r/'extensions'/'borromean';tmp=run.with_name('run_all.cmd.a006_tmp')
    if tmp.exists():sys.exit('PATCH NOT APPLIED: temporary file already exists')
    newline='\r\n' if b'\r\n' in b else '\n'
    pos=s.find('\n');prefix=s[:pos+1] if pos>=0 else s+'\n';rest=s[pos+1:] if pos>=0 else ''
    # Put dispatch before the existing setlocal/cd statements; extension wrapper sets cwd explicitly.
    new=prefix+HOOK+newline+rest
    if not new.endswith(('\n','\r')):new+=newline
    new+=TAIL.replace('\n',newline)
    try:
        backup.parent.mkdir(parents=True,exist_ok=True)
        backup.write_bytes(b)
        shutil.copytree(P/'payload'/'extensions'/'borromean',dest)
        tmp.write_bytes(new.encode('utf-8'))
        os.replace(tmp,run)
        receipt={'base':'A006 v0.4.0 TWIST_TORUS_MATRIX','patch':'BORROMEAN v0.4.1',
                 'original_sha256':sha(backup),'patched_sha256':sha(run),
                 'changes':['run_all.cmd dispatcher','extensions/borromean/'],
                 'original_shortcut_modified':False,'original_rc_modified':False,
                 'original_seeds_modified':False,'KnotPlot_runtime':'NOT_RUN'}
        (dest/'PATCH_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    except Exception:
        if backup.exists():run.write_bytes(b)
        if dest.exists():shutil.rmtree(dest)
        if tmp.exists():tmp.unlink()
        raise
    print('PATCH INSTALLED. Try: run_all.cmd BORROMEAN TEST')
if __name__=='__main__':main()
