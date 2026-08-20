from __future__ import annotations
import argparse, hashlib, json, os, shutil, subprocess, sys, zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HISTORY=ROOT/'release_history'
INPUTS=ROOT/'repro_inputs'
WORK=ROOT/'_history_work'
RESULTS=ROOT/'_history_results'

V040=HISTORY/'SST_MultiTopology_Knot_Link_TBK_RPO_Falsifier_v0.4.0.zip'

VERSIONS=[
 ('0.1.0', HISTORY/'SST_Trefoil_Lobe_Orientation_Blind_Falsifier_v0.1.0.zip'),
 ('0.1.1', HISTORY/'SST_Trefoil_Lobe_Orientation_Blind_Falsifier_v0.1.1.zip'),
 ('0.2.0', HISTORY/'SST_Trefoil_Lobe_Orientation_Blind_Falsifier_v0.2.0.zip'),
 ('0.3.0', HISTORY/'SST_Trefoil_Lobe_Orientation_Blind_Falsifier_v0.3.0.zip'),
]


def sha256(p:Path):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest()


def run(cmd,cwd,env=None):
 print('[REPRO]', ' '.join(map(str,cmd)))
 return subprocess.run([str(x) for x in cmd],cwd=str(cwd),env=env,check=False).returncode


def venv_python(root:Path):
 return root/'.venv_history'/'Scripts'/'python.exe' if os.name=='nt' else root/'.venv_history'/'bin'/'python'


def prepare_old(ver,zpath,reinstall=False):
 dest=WORK/f'v{ver}'
 if not dest.exists():
  dest.mkdir(parents=True,exist_ok=True)
  with zipfile.ZipFile(zpath) as z:z.extractall(dest)
 roots=[p for p in dest.iterdir() if p.is_dir() and p.name.startswith('SST_Trefoil_')]
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
 manifest={'mode':mode,'inputs':{'fseries':sha256(fser),'knotplot':sha256(knot)},'runs':[]}
 for ver,zpath in VERSIONS:
  proj,py=prepare_old(ver,zpath,reinstall=reinstall)
  out=RESULTS/f'v{ver}_{mode}'
  if out.exists(): shutil.rmtree(out)
  cfg=proj/'configs'/f'{mode}.json'
  cmd=[py,'run_blind.py','--fseries',fser,'--knotplot',knot,'--config',cfg,'--out-dir',out,'--backend','python']
  rc=run(cmd,proj); manifest['runs'].append({'version':ver,'returncode':rc,'result':str(out.relative_to(ROOT))})
 # Exact prior v0.4.0 multi-topology release.
 dest=WORK/'v0.4.0'
 if not dest.exists():
  dest.mkdir(parents=True,exist_ok=True)
  with zipfile.ZipFile(V040) as z:z.extractall(dest)
 roots=[p for p in dest.iterdir() if p.is_dir() and p.name.startswith('SST_MultiTopology_')]
 if not roots: raise RuntimeError('No v0.4.0 project root in historical ZIP')
 proj040=roots[0]; py040=venv_python(proj040)
 if reinstall and py040.exists(): shutil.rmtree(py040.parents[1],ignore_errors=True)
 if not py040.exists():
  rc=run([sys.executable,'-m','venv','.venv_history'],proj040)
  if rc: raise RuntimeError('venv creation failed for v0.4.0')
  rc=run([py040,'-m','pip','install','--upgrade','pip','setuptools','wheel'],proj040)
  if rc: raise RuntimeError('pip bootstrap failed for v0.4.0')
  rc=run([py040,'-m','pip','install','-r','requirements.txt'],proj040)
  if rc: raise RuntimeError('requirements failed for v0.4.0')
 out=RESULTS/f'v0.4.0_panel_{mode}'
 if out.exists(): shutil.rmtree(out)
 cmd=[py040,'run_panel.py','--config',proj040/'configs'/f'panel_{mode}.json','--out-dir',out,'--backend','python']
 rc=run(cmd,proj040); manifest['runs'].append({'version':'0.4.0-panel-exact','returncode':rc,'result':str(out.relative_to(ROOT))})
 # Current v0.4.1 panel basis, kept separate from archive EXTRA_EXTENDED/FULL campaigns.
 out=RESULTS/f'v0.4.1_panel_{mode}'
 if out.exists(): shutil.rmtree(out)
 cfg_current=ROOT/'configs'/f'panel_{mode}.json'
 cmd=[sys.executable,ROOT/'run_panel.py','--config',cfg_current,'--out-dir',out,'--backend','python']
 rc=run(cmd,ROOT); manifest['runs'].append({'version':'0.4.1-panel','returncode':rc,'result':str(out.relative_to(ROOT))})
 (RESULTS/f'reproduction_manifest_{mode}.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
 return 0 if all(r['returncode'] in (0,2) for r in manifest['runs']) else 1


def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--mode',choices=['basic','extended'],default='basic');ap.add_argument('--reinstall',action='store_true');a=ap.parse_args();return reproduce(a.mode,a.reinstall)
if __name__=='__main__': raise SystemExit(main())
