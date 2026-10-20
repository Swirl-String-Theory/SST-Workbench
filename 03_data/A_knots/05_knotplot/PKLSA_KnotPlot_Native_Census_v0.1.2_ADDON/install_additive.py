#!/usr/bin/env python3
"""Append-only local SST-Workbench / PKLSA v0.3.1 installer.
Only creates a NEW data dir and one new PKLSA module, and appends an optional source entry.
Never overwrites old data, exports or core.py; rollback information is emitted.
"""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, sys
from pathlib import Path
SOURCE_ID = "knotplot.native_census.v0.1.2"
DATA_REL = Path("03_data/A_knots/04_knotplot/PKLSA_KnotPlot_Native_Census_v0.1.2")
SPEC = {'source_id': SOURCE_ID,'kind':'geometry_catalog',
 'role':'native_geometry_baseline_opt_in_topology_identity_unverified',
 'canonical_paths':[DATA_REL.as_posix()],'legacy_globs':[],
 'provider_group':'knotplot','method_group':'knotplot_catalogue_and_procedural_native',
 'admit_geometry':False,'required':False,
 'extension_note':'Opt-in coordinates; not an independent provider or an automatically admitted evidence carrier.'}

def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument('--workbench',required=True,type=Path)
 p.add_argument('--pklsa',type=Path,help='Path to E010-v0.3.1; autodetect if omitted')
 p.add_argument('--data-only',action='store_true',help='Install data only, without registering with E010')
 a=p.parse_args(argv); wb=a.workbench.expanduser().resolve()
 if not wb.is_dir():p.error(f'Workbench folder missing: {wb}')
 kit=Path(__file__).resolve().parent; supplied=kit/'dataset'
 target=wb/DATA_REL
 pk=None; edits=[]
 if not a.data_only:
  if a.pklsa:
   pk=a.pklsa.resolve()
  else:
   poss=list((wb/'01_research'/'E_pipelines').glob('E010*/E010-v0.3.1'))
   poss=[x for x in poss if (x/'sst_pklsa/core.py').is_file()]
   if len(poss)!=1:
    p.error('Expected exactly one E010-v0.3.1; specify --pklsa or --data-only')
   pk=poss[0]
  if not (pk/'sst_pklsa/core.py').is_file() or not (pk/'configs/source_contract_v1.json').is_file():
   p.error(f'Not an E010 PKLSA v0.3.1 source tree: {pk}')
  mod=pk/'sst_pklsa/knotplot_census.py'
  if mod.exists() and mod.read_bytes() != (kit/'knotplot_census.py').read_bytes():
   p.error(f'Different version of extension already installed: {mod}')
  for rel in ('configs/source_contract_v1.json','configs/source_contract_production_v2.json'):
   f=pk/rel
   if not f.exists(): continue
   cfg=json.loads(f.read_text(encoding='utf-8'))
   ex=[s for s in cfg.get('sources',[]) if s.get('source_id')==SOURCE_ID]
   if ex and ex[0]!=SPEC:p.error(f'Conflicting source record in {f}')
  edits.append(mod)
 if target.exists():
  registry=target/'registry.json'
  if not registry.is_file() or registry.read_bytes() != (supplied/'registry.json').read_bytes():
   p.error(f'Destination exists with different registry: {target}; refusing overwrite')
  for path in supplied.rglob('*'):
   if path.is_file():
    old=target/path.relative_to(supplied)
    if not old.is_file() or old.read_bytes()!=path.read_bytes():p.error(f'Dataset files differ at {old}; refusing overwrite')
  print('DATASET_ALREADY_PRESENT_AND_IDENTICAL',target)
 else:
  target.parent.mkdir(parents=True,exist_ok=True)
  shutil.copytree(supplied,target)
  print('DATASET_CREATED',target)
 if pk is not None:
  mod=pk/'sst_pklsa/knotplot_census.py'
  if not mod.exists():shutil.copyfile(kit/'knotplot_census.py',mod)
  for rel in ('configs/source_contract_v1.json','configs/source_contract_production_v2.json'):
   f=pk/rel
   if not f.exists():continue
   cfg=json.loads(f.read_text(encoding='utf-8'))
   if not any(s.get('source_id')==SOURCE_ID for s in cfg.get('sources',[])):
    backup=f.with_name(f.name+'.before_knotplot_native_v012.bak')
    if not backup.exists():shutil.copy2(f,backup)
    cfg['sources'].append(SPEC)
    f.write_text(json.dumps(cfg,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('SOURCE_REGISTERED',f,'BACKUP',backup)
  print('PKLSA_EXTENSION_INSTALLED',mod)
 print('SUCCESS dataset='+SOURCE_ID+' objects=50 components=85; old defaults unchanged; opt-in only')
if __name__=='__main__': main()
