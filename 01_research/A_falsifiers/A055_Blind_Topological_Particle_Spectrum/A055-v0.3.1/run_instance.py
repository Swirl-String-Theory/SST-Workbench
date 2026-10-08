from __future__ import annotations
from pathlib import Path
import json,os,re,sys,shutil,hashlib
ROOT=Path(__file__).resolve().parent; LOCATOR=ROOT/'.sst_framework_root'

def _vkey(p):
 m=re.search(r'_v(\d+)\.(\d+)\.(\d+)$',p.name); return tuple(map(int,m.groups())) if m else (-1,-1,-1)
def _candidates():
 out=[]
 if os.environ.get('SST_FALSIFIER_FRAMEWORK_ROOT'): out.append(Path(os.environ['SST_FALSIFIER_FRAMEWORK_ROOT']))
 if LOCATOR.exists():
  raw=LOCATOR.read_text().strip(); p=Path(raw); out.append(p if p.is_absolute() else ROOT/p)
 for parent in [ROOT,*ROOT.parents]:
  fam=parent/'06_templates'/'SST_Falsifier_Framework'
  if fam.is_dir(): out.extend(sorted([p for p in fam.glob('SST_Falsifier_Framework_v*') if p.is_dir()],key=_vkey,reverse=True))
 return out
def _load_framework():
 try: import sst_falsifier; return
 except ImportError: pass
 for p in _candidates():
  if (p/'sst_falsifier'/'__init__.py').is_file(): sys.path.insert(0,str(p.resolve())); import sst_falsifier; return
 raise RuntimeError('SST Falsifier Framework v1.0.4 not found; set SST_FALSIFIER_FRAMEWORK_ROOT or install canonical 06_templates version.')
_load_framework()
from sst_falsifier.runner import run_mode,instance_output_root
from sst_falsifier.config import load_instance_config
from sst_falsifier.outputs import make_output_manifest,pack_revealed
from sst_falsifier.report import write_auto_results_tex,publish_instance_report
from sst_falsifier.util import write_json

def _refresh_reveal():
 cfg=load_instance_config(ROOT); out=instance_output_root(ROOT,cfg)
 from private.reveal_analysis import run_reveal_analysis
 run_reveal_analysis(ROOT,out)
 make_output_manifest(out,out/'OUTPUT_MANIFEST.json')
 write_auto_results_tex(ROOT,out,out/'report'/'AUTO_RESULTS.tex')
 render=publish_instance_report(ROOT,out/'report'/'FALSIFIER_REPORT.tex',strict=False); write_json(out/'REPORT_RENDER.json',render)
 make_output_manifest(out,out/'OUTPUT_MANIFEST.json')
 z=ROOT.parent/f"{cfg['project']['name']}_{cfg['project']['version']}-outputs_REVEALED.zip"
 pack_revealed(out,z)

def main():
 mode=sys.argv[1].upper() if len(sys.argv)>1 else 'FULL'
 rc=run_mode(ROOT,mode)
 if rc==0 and mode=='REVEAL': _refresh_reveal()
 return rc
if __name__=='__main__': raise SystemExit(main())
