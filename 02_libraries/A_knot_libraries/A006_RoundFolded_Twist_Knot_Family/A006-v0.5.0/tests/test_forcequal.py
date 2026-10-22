"""In-place patch and 6-arm tests using a user-provided A006 v0.5.0a root."""
import json,os,subprocess,sys,tempfile,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];root=Path(os.environ['A006_ROOT'])
with tempfile.TemporaryDirectory(prefix='a006v050b_') as td:
 r=Path(td)
 (r/'tools').mkdir();(r/'Output/v050/geometry').mkdir(parents=True)
 for name in ('run_all.cmd','knotplotrc.kps'):
  shutil.copy2(root/name,r/name)
 shutil.copy2(root/'tools/selection_v050.py',r/'tools/selection_v050.py')
 shutil.copy2(root/'Output/v050/geometry/LINK_5_5_6_BALANCED_N1024_ORIG_CPFIXED61.xyz',r/'Output/v050/geometry/LINK_5_5_6_BALANCED_N1024_ORIG_CPFIXED61.xyz')
 def install(*args):
  return subprocess.run([sys.executable,str(P/'install_patch.py'),'--base',str(r),*args],capture_output=True,text=True)
 assert install('--check').returncode==0
 a=install('--apply');assert a.returncode==0,(a.stdout,a.stderr)
 assert install('--apply').returncode!=0
 sys.path.insert(0,str(r/'tools'))
 from force_qualification_v050b import selftest,analyze,read_components,REL,NAMES
 selftest(r)
 plan=json.loads((r/REL/'PLAN.json').read_text());assert len(plan['arms'])==6
 for name in NAMES:
  p=r/REL/'scripts'/f'FQ_{name}.kps'
  s=p.read_text();assert 'stop\n' not in s and '/s' not in s
  assert 'go beadlimit 4000' in s and 'collision\n' in s
 report=analyze(r);assert report['report_status']=='NO_KNOTPLOT_RUNTIME_DATA'
 # create a synthetic zero-checkpoint in two arms, verifying parser and output contract,
 # without creating ANY user-facing false simulation data.
 src=read_components(r/'Output/v050/geometry/LINK_5_5_6_BALANCED_N1024_ORIG_CPFIXED61.xyz')
 for name in NAMES[:2]:
  f=r/REL/'runs'/name/'i0000000.xyz';f.parent.mkdir(parents=True,exist_ok=True)
  f.write_text('\n\n'.join('\n'.join(' '.join(f'{v:.12g}' for v in p) for p in a) for a in src)+'\n')
 report=analyze(r);assert report['initial_xyz_equal']=='PASS'
 assert install('--rollback').returncode==0
 assert (r/'run_all.cmd').read_bytes()==(root/'run_all.cmd').read_bytes()
 assert (r/'knotplotrc.kps').read_bytes()==(root/'knotplotrc.kps').read_bytes()
 print('PASS: check, install, double apply refused, six scripts, analysis missing-data, component headers, initial equality, rollback')
