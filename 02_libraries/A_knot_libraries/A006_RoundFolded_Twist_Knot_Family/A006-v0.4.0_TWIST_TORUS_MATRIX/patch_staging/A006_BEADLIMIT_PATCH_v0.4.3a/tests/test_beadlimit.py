#!/usr/bin/env python3
from pathlib import Path
import sys,tempfile,shutil,subprocess,importlib.util
PATCH=Path(__file__).resolve().parents[1]
SRC=PATCH/'tools'/'selection_v043.py'
INSTALLER=PATCH/'install_patch.py'

def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path)
 mod=importlib.util.module_from_spec(spec)
 sys.modules[name]=mod
 spec.loader.exec_module(mod)
 return mod
m=load(SRC,'selector_v043a')
orig=load(PATCH/'tests'/'original_selection_v043.py','selector_v043_base') if (PATCH/'tests'/'original_selection_v043.py').exists() else None

def main():
 assert m.required_beadlimit([1000,1000,1000]) is None
 assert m.required_beadlimit([1024,1024,1024])==4000
 assert m.required_beadlimit([1138,1054,1024])==4000
 assert m.required_beadlimit([1150,1150,1040])==4000
 assert m.required_beadlimit([2048,2048,2048])==8000
 assert m.required_beadlimit([6000,6000,6000])==32000
 with tempfile.TemporaryDirectory() as folder:
  root=Path(folder);geo=root/'geometry';geo.mkdir()
  xyz=geo/'sample.xyz';xyz.write_text('1 2 3\n\n4 5 6\n\n7 8 9\n')
  ticks=[0,1,8,32,128,500]
  case=m.Case('LINK','5_5_6',1024,'ORIG','OFF','FLAT')
  kpc,run,key=m.script_and_dir(root,case,xyz,ticks,[1138,1054,1024]);s=kpc.read_text()
  assert 'load geometry/sample.xyz\ngo beadlimit 4000\ninformation' in s
  assert s.index('go beadlimit 4000')<s.index('ago 1')
  assert s.count('go beadlimit 4000')==1
  assert 'ago 1' in s and 'ago 7' in s
  kpc2,_,key2=m.script_and_dir(root,case,xyz,ticks,[1138,1054,1024])
  assert kpc2==kpc and key2==key
  many,_,_=m.script_and_dir(root,m.Case('LINK','6_6_5',2048,'ORIG','OFF','BALANCED'),xyz,ticks,[2276,2108,2048]);assert 'go beadlimit 8000' in many.read_text()
  small,_,_=m.script_and_dir(root,m.Case('KNOT','3_1',512,'ORIG','OFF'),xyz,ticks,[512]);assert 'go beadlimit' not in small.read_text()
  assert 'AUTO-GENERATED A006 selection v0.4.3, requires KnotPlot atomic ago' in small.read_text()
  if orig is not None:
   assert m.protocol(root,case,xyz,ticks,[512])==orig.protocol(root,case,xyz,ticks)
   sm_old,sm_dir,sm_hash=orig.script_and_dir(root,m.Case('KNOT','4_1',256,'ORIG','OFF'),xyz,ticks)
   sm_new,_,_=m.script_and_dir(root,m.Case('KNOT','4_1',256,'ORIG','OFF'),xyz,ticks,[256])
   assert sm_new==sm_old and sm_new.read_bytes()==sm_old.read_bytes()
  # Installer check/apply, unchanged run_all.cmd, backup and double-apply protection.
  base=root/'A006-v0.4.0_TWIST_TORUS_MATRIX';(base/'tools').mkdir(parents=True)
  baseline=PATCH/'tests'/'original_selection_v043.py'
  if baseline.exists():shutil.copy2(baseline,base/'tools'/'selection_v043.py')
  else:pass
  (base/'run_all.cmd').write_text('@echo off\r\nrem A006_SELECT_DISPATCH_v043\r\n')
  if baseline.exists():
   before=(base/'run_all.cmd').read_bytes()
   cmd=[sys.executable,str(INSTALLER),'--base',str(base)]
   assert subprocess.run(cmd+['--check'],capture_output=True).returncode==0
   assert subprocess.run(cmd+['--apply'],capture_output=True).returncode==0
   assert subprocess.run(cmd+['--apply'],capture_output=True).returncode!=0
   assert (base/'run_all.cmd').read_bytes()==before
   assert (base/'tools'/'selection_v043.py').read_bytes()==SRC.read_bytes()
   assert (base/'patch_backups'/'selection_v043a_beadlimit'/'selection_v043_before_v043a.py').read_bytes()==baseline.read_bytes()
 print('PASS: counts, insertion order, 4k/8k, 3-block total, hash-compatible low-N scripts, installer safety')

if __name__=='__main__':main()
