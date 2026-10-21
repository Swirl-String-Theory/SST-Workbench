"""Run with: python tests/test_patch_v043.py [optional-real-A006-root]."""
from pathlib import Path
import subprocess, tempfile, sys, json, shutil, importlib.util
PATCH=Path(__file__).resolve().parents[1]

def test_installer(source):
 with tempfile.TemporaryDirectory() as d:
  base=Path(d)/'A006-v0.4.0_TWIST_TORUS_MATRIX'
  (base/'src').mkdir(parents=True)
  (base/'extensions'/'borromean'/'whole').mkdir(parents=True)
  for f in ('run_all.cmd','SEED_MANIFEST.json'):
   shutil.copy2(source/f,base/f)
  shutil.copy2(source/'src'/'build_v040.py',base/'src'/'build_v040.py')
  shutil.copy2(source/'extensions'/'borromean'/'whole'/'build_whole.py',base/'extensions'/'borromean'/'whole'/'build_whole.py')
  orig=(base/'run_all.cmd').read_bytes()
  cmd=[sys.executable,str(PATCH/'install_patch.py'),'--base',str(base)]
  assert subprocess.run(cmd+['--check'],capture_output=True).returncode==0
  assert (base/'run_all.cmd').read_bytes()==orig
  assert subprocess.run(cmd+['--apply'],capture_output=True).returncode==0
  assert b'A006_SELECT_DISPATCH_v043' in (base/'run_all.cmd').read_bytes()
  assert (base/'patch_backups'/'selection_v043'/'run_all_before_v043.cmd').read_bytes()==orig
  assert subprocess.run(cmd+['--apply'],capture_output=True).returncode!=0
  assert (base/'tools'/'selection_v043.py').is_file()
  r=subprocess.run([sys.executable,str(base/'tools'/'selection_v043.py'),'--selftest'],capture_output=True)
  assert r.returncode==0,r.stderr
  # Legacy modes still appear in the dispatcher unaltered.
  text=(base/'run_all.cmd').read_text()
  for mode in ('BORROMEAN','BASIC','SMALL','MEDIUM','FULL','PREFLIGHT'):
   assert mode in text
 print('PASS: transactional installer, legacy dispatch preservation, idempotency fail-closed')

def test_plan(source):
 command=[sys.executable,str(PATCH/'tools'/'selection_v043.py'), '--root',str(source),
  '--knots=3_1,4_1,11_2','--links=5_5_6','--linkProfiles=BALANCED',
  '--minN=256','--maxN=512','--maxIteration=8000','--checkpointsEvery=500','--mirrored=BOTH',
  '--plan']
 cp=subprocess.run(command,capture_output=True,text=True)
 assert cp.returncode==0,cp.stderr
 p=json.loads((source/'output'/'selection_v043'/'PLAN.json').read_text())
 assert p['count']==16 # 3 knots+1 link x 2 N x 2 orientations
 assert p['checkpoint_count']==22
 print('PASS: command options, aliases, count 16, hybrid/linear checkpoint grid')

if __name__=='__main__':
 src=Path(sys.argv[1]) if len(sys.argv)>1 else None
 if src is None:
  print('Provide v0.4.2d A006 root for integration test');raise SystemExit(2)
 test_installer(src)
 test_plan(src)
