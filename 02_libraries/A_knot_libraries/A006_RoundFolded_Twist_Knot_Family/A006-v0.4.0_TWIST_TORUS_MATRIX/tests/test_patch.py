"""Installer fail-closed regression tests using the audited v0.4.0 ZIP if available."""
from pathlib import Path
import subprocess,sys,zipfile,tempfile,hashlib,json
SRC=Path(__file__).resolve().parents[1]
ORIGINAL=Path('/mnt/data/RoundFolded_NearUnknot_v0.4.0_TWIST_TORUS_MATRIX.zip')
def run(*args):
 return subprocess.run([sys.executable,str(SRC/'install_patch.py'),*map(str,args)],capture_output=True,text=True)
def test():
 assert ORIGINAL.exists(),'Local source ZIP missing for test harness'
 with tempfile.TemporaryDirectory(prefix='a006_patch_test_') as td:
  tmp=Path(td)
  with zipfile.ZipFile(ORIGINAL) as z:z.extractall(tmp)
  root=tmp/'RoundFolded_NearUnknot_v0.4.0_TWIST_TORUS_MATRIX'
  original=(root/'run_all.cmd').read_bytes()
  seedpaths=[root/'output'/'seeds'/f'{k}_N{n}.kpt' for k in ('5_2','6_1') for n in (1024,2048)]
  hashes=[hashlib.sha256(x.read_bytes()).hexdigest() for x in seedpaths]
  for arg in ['--check','--apply']:
   cp=run('--base',root,arg);assert cp.returncode==0,cp.stdout+cp.stderr
  assert (root/'run_all.cmd').read_bytes()!=original
  assert (root/'patch_backups'/'A006_BORROMEAN_v0.4.1'/'run_all.cmd.before').read_bytes()==original
  assert [hashlib.sha256(x.read_bytes()).hexdigest() for x in seedpaths]==hashes
  content=(root/'run_all.cmd').read_text();assert 'A006_BORROMEAN_V041' in content
  for text in ['BASIC','SMALL','MEDIUM','FULL','ANALYZE','PREFLIGHT']:
   assert text in content
  assert (root/'extensions'/'borromean'/'build_borromean.py').exists()
  assert run('--base',root,'--apply').returncode!=0
  # Negative input tamper test on a second clean fixture
  with tempfile.TemporaryDirectory(prefix='a006_patch_tamper_') as td2:
   temp=Path(td2)
   with zipfile.ZipFile(ORIGINAL) as z:z.extractall(temp)
   rr=temp/'RoundFolded_NearUnknot_v0.4.0_TWIST_TORUS_MATRIX'
   with open(rr/'output/seeds/5_2_N1024.kpt','ab') as f:f.write(b'BAD')
   b=(rr/'run_all.cmd').read_bytes()
   assert run('--base',rr,'--apply').returncode!=0
   assert (rr/'run_all.cmd').read_bytes()==b
   assert not (rr/'extensions'/'borromean').exists()
 print('PASS 5/5: real-v040 compatibility, reversible backup, seed-preservation, no-double-install, fail-closed tamper')
if __name__=='__main__':test()
