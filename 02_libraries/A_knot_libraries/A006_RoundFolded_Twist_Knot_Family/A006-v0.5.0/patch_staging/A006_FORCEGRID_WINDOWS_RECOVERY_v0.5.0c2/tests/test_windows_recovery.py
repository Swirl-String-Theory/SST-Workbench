"""Reproduce Windows CRLF failure and verify v0.5.0c2 against the A006 v0.5.0a ZIP.
Run: py -3 tests/test_windows_recovery.py  (Python + numpy)
"""
import hashlib, importlib.util, json, shutil, subprocess, sys, tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]
REPAIR=HERE/'repair.py'
FIXTURE=HERE/'tests'/'fixture'
FILES=('run_all.cmd','knotplotrc.kps','tools/selection_v050.py','Output/v050/geometry/LINK_5_5_6_BALANCED_N1024_ORIG_CPFIXED61.xyz')
def seed(root):
 for p in FILES:
  dest=root/p;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(FIXTURE/p,dest)
 return root
def cli(root,operation):
 return subprocess.run([sys.executable,str(REPAIR),'--base',str(root),operation],text=True,capture_output=True)
def win_eol(p):
 p.write_bytes(p.read_bytes().replace(b'\r\n',b'\n').replace(b'\n',b'\r\n'))
def setup_windows_partial(root,plan=True,forcequal=True,aliases=False):
 target=root/'tools/force_grid_v050c.py';target.write_bytes((HERE/'payload/force_grid_v050c.py').read_bytes())
 spec=importlib.util.spec_from_file_location('fgmodule',target);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 if plan:
  module.prepare(root)
  for file in (root/'Output/qualification_v050c/scripts').glob('*.kps'):win_eol(file)
  fp=root/'Output/qualification_v050c/scripts/FQ_AMECH_140_ELEC.kps'
  m=json.loads((root/'Output/qualification_v050c/PLAN.json').read_text())
  assert hashlib.sha256(fp.read_bytes()).hexdigest()!=m['arms']['AMECH_140_ELEC']['script_sha256']
 if forcequal:(root/'tools/force_qualification_v050b.py').write_text('print("existing forcequal")\n')
 if aliases:
  f=root/'knotplotrc.kps';v=f.read_text()+'\n% >>> A006_FORCEGRID_v050c_ALIASES_BEGIN\n'
  v+='\n'.join(f'alias {alias} "read Output/qualification_v050c/scripts/FQ_{name}.kps"' for name,alias in module.ALIASES.items())
  f.write_text(v+'\n% <<< A006_FORCEGRID_v050c_ALIASES_END\n')
 return module

def verify(root):
 runner=(root/'run_all.cmd').read_text()
 assert 'if /I "%~1"=="FORCEGRID" goto forcegrid' in runner
 assert ':forcegrid\npy -3 tools\\force_grid_v050c.py' in runner
 assert 'alias fgB0 ' in (root/'knotplotrc.kps').read_text()
 assert len(list((root/'Output/qualification_v050c/scripts').glob('FQ_*.kps')))==14
 p=json.loads((root/'Output/qualification_v050c/PLAN.json').read_text())
 for item in p['arms'].values():
  file=root/item['script']
  assert hashlib.sha256(file.read_bytes().replace(b'\r\n',b'\n')).hexdigest()==item['script_sha256']

with tempfile.TemporaryDirectory(prefix='A006_c2_') as temp:
 d=Path(temp)
 for case in ('partial_crlf_with_c1_backup','crlf_with_aliases','clean','healthy','edited_script','alias_collision'):
  root=seed(d/case)
  if case in ('partial_crlf_with_c1_backup','crlf_with_aliases','healthy','edited_script'):
   m=setup_windows_partial(root,aliases=case in ('crlf_with_aliases','healthy'))
   if case=='partial_crlf_with_c1_backup':
    b=root/'patch_backups/v050c1_RUNNER_RECOVERY';b.mkdir(parents=True)
    shutil.copy2(root/'run_all.cmd',b/'run_all.cmd')
    shutil.copy2(root/'knotplotrc.kps',b/'knotplotrc.kps')
    assert not (b/'RECOVERY.json').exists()
   if case=='healthy':
    text=(root/'run_all.cmd').read_text()
    text=text.replace('cd /d "%~dp0"','cd /d "%~dp0"\nif /I "%~1"=="FORCEGRID" goto forcegrid',1)
    text=text.replace(':usage\n',':forcegrid\npy -3 tools\\force_grid_v050c.py %2 %3 %4 %5 %6 %7 %8 %9\nexit /b %errorlevel%\n:usage\n',1)
    (root/'run_all.cmd').write_bytes(text.encode())
   if case=='edited_script':
    f=root/'Output/qualification_v050c/scripts/FQ_AMECH_140_ELEC.kps'
    f.write_bytes(f.read_bytes().replace(b'charge = 15',b'charge = 99'))
  if case=='alias_collision':
   p=root/'knotplotrc.kps';p.write_text(p.read_text()+'\nalias fgB0 "foreign command"\n')
  before_script=None
  f=root/'Output/qualification_v050c/scripts/FQ_AMECH_140_ELEC.kps'
  if f.exists():before_script=f.read_bytes()
  a=cli(root,'--check')
  if case in ('edited_script','alias_collision'):
   assert a.returncode!=0,(case,a.stdout,a.stderr)
   assert cli(root,'--apply').returncode!=0
   assert not (root/'patch_backups/v050c2_WINDOWS_RECOVERY').exists()
   print('PASS refusal:',case)
   continue
  assert a.returncode==0,(case,a.stdout,a.stderr)
  if case=='partial_crlf_with_c1_backup':
   assert 'grid_plan' in a.stdout and 'VALID' in a.stdout
  original=(root/'run_all.cmd').read_bytes()
  out=cli(root,'--apply');assert out.returncode==0,(case,out.stdout,out.stderr)
  verify(root)
  if before_script is not None:assert before_script==f.read_bytes(), 'Prior script overwritten'
  if case=='partial_crlf_with_c1_backup':
   assert (root/'patch_backups/v050c1_RUNNER_RECOVERY/run_all.cmd').is_file(), 'Older backup lost'
  out=cli(root,'--apply');assert out.returncode==0,(case,'idempotence',out.stderr)
  if case!='healthy':
   out=cli(root,'--rollback');assert out.returncode==0,(case,'rollback',out.stderr)
   assert (root/'run_all.cmd').read_bytes()==original
  print('PASS recovery:',case)
print('ALL WINDOWS-CRLF REGRESSIONS PASS')
