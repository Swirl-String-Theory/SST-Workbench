from __future__ import annotations
import argparse, hashlib, json, os, shutil, subprocess, sys, zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HISTORY=ROOT/'release_history'
INPUTS=ROOT/'repro_inputs'
WORK=ROOT/'_history_work'
RESULTS=ROOT/'_history_results'
CAPSULE=HISTORY/'SST_MultiTopology_Knot_Link_TBK_RPO_Falsifier_v0.4.1.zip'


def sha256(p:Path):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest()


def run(cmd,cwd,env=None):
 print('[REPRO]', ' '.join(map(str,cmd)), flush=True)
 return subprocess.run([str(x) for x in cmd],cwd=str(cwd),env=env,check=False).returncode


def venv_python(root:Path):
 return root/'.venv_history'/'Scripts'/'python.exe' if os.name=='nt' else root/'.venv_history'/'bin'/'python'


def unpack_capsule():
 if not CAPSULE.exists(): raise FileNotFoundError(f'Missing scientific capsule: {CAPSULE}')
 caproot=WORK/'capsule_v0.4.1'
 if not caproot.exists():
  caproot.mkdir(parents=True,exist_ok=True)
  with zipfile.ZipFile(CAPSULE) as z:z.extractall(caproot)
 roots=[x for x in caproot.iterdir() if x.is_dir() and x.name.startswith('SST_MultiTopology_')]
 if not roots: raise RuntimeError('No v0.4.1 project root inside scientific capsule')
 return roots[0]


def prepare_project_from_zip(ver:str,zpath:Path,prefix:str,reinstall=False):
 dest=WORK/f'v{ver}'
 if not dest.exists():
  dest.mkdir(parents=True,exist_ok=True)
  with zipfile.ZipFile(zpath) as z:z.extractall(dest)
 roots=[x for x in dest.iterdir() if x.is_dir() and x.name.startswith(prefix)]
 if not roots: raise RuntimeError(f'No project root in {zpath}')
 proj=roots[0]; py=venv_python(proj)
 if reinstall and py.exists(): shutil.rmtree(py.parents[1],ignore_errors=True)
 if not py.exists():
  rc=run([sys.executable,'-m','venv','.venv_history'],proj)
  if rc: raise RuntimeError(f'venv creation failed for v{ver}')
  rc=run([py,'-m','pip','install','--upgrade','pip','setuptools','wheel'],proj)
  if rc: raise RuntimeError(f'pip bootstrap failed for v{ver}')
  rc=run([py,'-m','pip','install','-r','requirements.txt'],proj)
  if rc: raise RuntimeError(f'requirements failed for v{ver}')
 return proj,py


def reproduce(mode,reinstall=False):
 fser=INPUTS/'knot.3_1.fseries'; knot=INPUTS/'knot_3.1_final.txt'
 if not fser.exists() or not knot.exists(): raise FileNotFoundError('Bundled reproducibility inputs missing')
 RESULTS.mkdir(exist_ok=True); WORK.mkdir(exist_ok=True)
 capsule_root=unpack_capsule()
 nested=capsule_root/'release_history'
 old=[
  ('0.1.0',nested/'SST_Trefoil_Lobe_Orientation_Blind_Falsifier_v0.1.0.zip'),
  ('0.1.1',nested/'SST_Trefoil_Lobe_Orientation_Blind_Falsifier_v0.1.1.zip'),
  ('0.2.0',nested/'SST_Trefoil_Lobe_Orientation_Blind_Falsifier_v0.2.0.zip'),
  ('0.3.0',nested/'SST_Trefoil_Lobe_Orientation_Blind_Falsifier_v0.3.0.zip'),
 ]
 manifest={'mode':mode,'capsule_sha256':sha256(CAPSULE),'inputs':{'fseries':sha256(fser),'knotplot':sha256(knot)},'runs':[]}
 for ver,zpath in old:
  proj,py=prepare_project_from_zip(ver,zpath,'SST_Trefoil_',reinstall)
  out=RESULTS/f'v{ver}_{mode}'
  if out.exists(): shutil.rmtree(out)
  cfg=proj/'configs'/f'{mode}.json'
  rc=run([py,'run_blind.py','--fseries',fser,'--knotplot',knot,'--config',cfg,'--out-dir',out,'--backend','python'],proj)
  manifest['runs'].append({'version':ver,'returncode':rc,'result':str(out.relative_to(ROOT))})

 # v0.4.0 exact from nested capsule.
 z040=nested/'SST_MultiTopology_Knot_Link_TBK_RPO_Falsifier_v0.4.0.zip'
 proj040,py040=prepare_project_from_zip('0.4.0',z040,'SST_MultiTopology_',reinstall)
 out=RESULTS/f'v0.4.0_panel_{mode}'
 if out.exists(): shutil.rmtree(out)
 rc=run([py040,'run_panel.py','--config',proj040/'configs'/f'panel_{mode}.json','--out-dir',out,'--backend','python'],proj040)
 manifest['runs'].append({'version':'0.4.0-panel-exact','returncode':rc,'result':str(out.relative_to(ROOT))})

 # v0.4.1 exact project is the capsule root itself.
 proj041=capsule_root; py041=venv_python(proj041)
 if reinstall and py041.exists(): shutil.rmtree(py041.parents[1],ignore_errors=True)
 if not py041.exists():
  rc=run([sys.executable,'-m','venv','.venv_history'],proj041)
  if rc: raise RuntimeError('venv creation failed for v0.4.1')
  rc=run([py041,'-m','pip','install','--upgrade','pip','setuptools','wheel'],proj041)
  if rc: raise RuntimeError('pip bootstrap failed for v0.4.1')
  rc=run([py041,'-m','pip','install','-r','requirements.txt'],proj041)
  if rc: raise RuntimeError('requirements failed for v0.4.1')
 out=RESULTS/f'v0.4.1_panel_{mode}'
 if out.exists(): shutil.rmtree(out)
 rc=run([py041,'run_panel.py','--config',proj041/'configs'/f'panel_{mode}.json','--out-dir',out,'--backend','python'],proj041)
 manifest['runs'].append({'version':'0.4.1-panel-exact','returncode':rc,'result':str(out.relative_to(ROOT))})

 (RESULTS/f'reproduction_manifest_{mode}.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
 return 0 if all(r['returncode'] in (0,2) for r in manifest['runs']) else 1


def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--mode',choices=['basic','extended'],default='basic'); ap.add_argument('--reinstall',action='store_true'); a=ap.parse_args(); return reproduce(a.mode,a.reinstall)
if __name__=='__main__': raise SystemExit(main())
