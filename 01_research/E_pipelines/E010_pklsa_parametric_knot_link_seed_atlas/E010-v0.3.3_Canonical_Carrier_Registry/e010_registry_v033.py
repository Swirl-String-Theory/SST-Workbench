#!/usr/bin/env python3
"""Create-only E010 v0.3.3 source-native carrier registry install and independent readback.

Installs by COPYING local E010 v0.3.2 to a new sibling. Never overwrites its parent.
Archive staging alone does not constitute locally committed source registration.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, shutil, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data'
SOURCE_ID='a003.fourier_torus.f3_f4.v0.1.2'
BASE_CONTRACT_SHA='d574756c5cae02948d7cd0f0e2360101334dcbf8527811c36842b31d3572b631'
CORE_SHA='6c39b44b0926b3959b27ace880788626c76271a7622f6e2ff8f0a8659869e5e3'
INDEX_SHA='1dfb8861eebe6ddbc843146d6901858144a4acfa5cf5b7408738d99e9767a08d'

class RegistryError(RuntimeError):pass

def digest(path:Path)->str:
 h=hashlib.sha256()
 with Path(path).open('rb') as stream:
  for chunk in iter(lambda: stream.read(1<<20),b''):h.update(chunk)
 return h.hexdigest()

def write_json(path:Path,obj):
 with path.open('x',encoding='utf8') as f:json.dump(obj,f,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False);f.write('\n')

def validate_inputs(base:Path,atlas:Path,wb:Path):
 base=base.resolve();atlas=atlas.resolve();wb=wb.resolve()
 if base.name!='E010-v0.3.2':raise RegistryError('Base must be E010-v0.3.2')
 if digest(base/'configs'/'source_contract_production_v2.json')!=BASE_CONTRACT_SHA:raise RegistryError('E010 v0.3.2 contract SHA mismatch')
 if digest(base/'sst_pklsa'/'core.py')!=CORE_SHA:raise RegistryError('E010 native resolver source SHA mismatch')
 if digest(DATA/'a003_v0.3.3_carriers.json')!=INDEX_SHA:raise RegistryError('Frozen staged index source SHA mismatch')
 if not (wb/'.sst-workbench-root').exists():raise RegistryError('Missing SST-Workbench root marker')
 try:relative=atlas.relative_to(wb).as_posix()
 except ValueError:raise RegistryError('Atlas not within Workbench root')
 if relative!='02_libraries/A_knot_libraries/A003_Fourier_Knot_Seed_Atlas/A003-v0.1.2':raise RegistryError('Unexpected atlas location')
 entries=json.loads((DATA/'a003_v0.3.3_carriers.json').read_text('utf8'))
 if len(entries['carriers'])!=8 or len({x['carrier_id'] for x in entries['carriers']})!=8:raise RegistryError('Exactly eight unique analytic carriers required')
 seen=set()
 for x in entries['carriers']:
  p=(atlas/x['atlas_relative_file']).resolve()
  if not p.is_relative_to(atlas):raise RegistryError('Carrier path traversal')
  if not p.is_file() or digest(p)!=x['sha256']:raise RegistryError('Raw carrier SHA mismatch: '+x['carrier_id'])
  seen.add(x['analytic_seed'])
 if seen!={'fibonacci_torus_F3','fibonacci_torus_F4'}:raise RegistryError('Unexpected seed family')
 return relative,entries

def native_readback(target,wb,atlas):
 core=target/'sst_pklsa'/'core.py'
 if digest(core)!=CORE_SHA:raise RegistryError('Native resolver SHA mismatch at readback')
 alias='e010_registry_v033_native_core'
 spec=importlib.util.spec_from_file_location(alias,core)
 m=importlib.util.module_from_spec(spec);sys.modules[alias]=m
 spec.loader.exec_module(m)
 result=[x for x in m.Workbench.open(wb,contract=target/'configs'/'source_contract_production_v2.json').resolve_sources() if x.source_id==SOURCE_ID]
 if len(result)!=1 or result[0].status!='RESOLVED' or Path(result[0].path).resolve()!=atlas.resolve():raise RegistryError('E010 native resolver cannot independently resolve committed source')
 return {'status':'PASS','source_id':result[0].source_id,'resolution_mode':result[0].resolution_mode,'native_core_sha256':CORE_SHA}

def verify(target:Path,wb:Path,atlas:Path,base:Path|None=None):
 target=target.resolve();wb=wb.resolve();atlas=atlas.resolve()
 r=target/'registries'/'a003_carriers_v033.json';c=target/'configs'/'source_contract_production_v2.json';release=target/'RELEASE_CARRIER_REGISTRY_v033.json'
 if not all(x.is_file() for x in (r,c,release)):raise RegistryError('Installed registry files missing')
 j=json.loads(release.read_text('utf8'))
 if j.get('status')!='INSTALLED_VERSIONED_REGISTRY_NOT_SCIENCE_CERTIFIED':raise RegistryError('Release contract mismatch')
 if digest(c)!=j['contract_sha256'] or digest(r)!=j['registry_sha256']:raise RegistryError('Installed E010 hash mismatch')
 records=json.loads(r.read_text('utf8'))
 if records.get('carrier_count')!=8 or len(records['carriers'])!=8:raise RegistryError('Index count mismatch')
 contract=json.loads(c.read_text('utf8'))
 matching=[x for x in contract['sources'] if x['source_id']==SOURCE_ID]
 if len(matching)!=1 or matching[0].get('provider_group')!='a003_analytic_seed_atlas':raise RegistryError('Registration duplicate/mismatch')
 for row in records['carriers']:
  p=(atlas/row['atlas_relative_file']).resolve()
  if not p.is_relative_to(atlas) or not p.is_file() or digest(p)!=row['sha256']:raise RegistryError('Carrier mutated/missing')
 if base:
  if digest(base/'configs'/'source_contract_production_v2.json')!=BASE_CONTRACT_SHA:raise RegistryError('Parent E010 has changed')
  if digest(base/'sst_pklsa'/'core.py')!=CORE_SHA:raise RegistryError('Parent E010 native resolver changed')
 return {'status':'PASS_INSTALLED_VERSIONED_REGISTRY','gate_scope':'E010 local copied release and hash/loader readback only',
  'native_readback':native_readback(target,wb,atlas),'carrier_count':8,'unique_source_families':2,
  'source_index_sha256':digest(r),'contract_sha256':digest(c),'release_sha256':digest(release),
  'a003_p8_evidence':True,'e010_v032_parent_untouched':True,'independent_empirical_carriers':0}

def install(base:Path,target:Path,atlas:Path,wb:Path):
 base=base.resolve();target=target.resolve();atlas=atlas.resolve();wb=wb.resolve()
 if target.exists():raise RegistryError('Target exists; create-only, will not overwrite')
 if target.name!='E010-v0.3.3' or target.parent!=base.parent:raise RegistryError('Target must be E010-v0.3.3 sibling')
 relative,entries=validate_inputs(base,atlas,wb)
 original=json.loads((base/'configs'/'source_contract_production_v2.json').read_text('utf8'))
 candidates=[x for x in original.get('sources',[]) if x['source_id']==SOURCE_ID]
 if candidates:raise RegistryError('Unexpected prior A003 registry entry; refusing duplicate')
 spec=next(x for x in json.loads((DATA/'source_contract_production_v2.json').read_text('utf8'))['sources'] if x['source_id']==SOURCE_ID)
 if spec.get('canonical_paths')!=[relative]:raise RegistryError('Canonical path mismatch')
 original['sources'].append(spec)
 rows=[]
 for entry in entries['carriers']:
  rows.append({k:v for k,v in entry.items() if k!='source_file'})
 registry={'schema':'E010-A003-CANONICAL-CARRIER-REGISTRY-1','version':'0.3.3',
  'source_id':SOURCE_ID,'carrier_count':len(rows),'carriers':rows,
  'producer':'A003 analytic F3/F4 atlas v0.1.2','independent_empirical_carriers':0,
  'registration_status':'VERSIONED_LOCAL_INSTALLED_REQUIRES_INDEPENDENT_QUALIFICATION'}
 tmp=target.parent/(target.name+'.STAGING_INCOMPLETE')
 if tmp.exists():raise RegistryError('Staging directory exists: '+str(tmp))
 try:
  shutil.copytree(base,tmp,ignore=shutil.ignore_patterns('__pycache__','.pytest_cache','results','*.pyc'))
  (tmp/'configs'/'source_contract_production_v2.json').unlink()
  write_json(tmp/'configs'/'source_contract_production_v2.json',original)
  (tmp/'registries').mkdir(exist_ok=True)
  write_json(tmp/'registries'/'a003_carriers_v033.json',registry)
  write_json(tmp/'RELEASE_CARRIER_REGISTRY_v033.json',{
    'schema':'E010-A003-CARRIER-REGISTRY-RELEASE-1','version':'0.3.3',
    'status':'INSTALLED_VERSIONED_REGISTRY_NOT_SCIENCE_CERTIFIED',
    'source_base_version':'0.3.2','source_base_contract_sha256':BASE_CONTRACT_SHA,
    'native_core_sha256':CORE_SHA,'source_index_proposal_sha256':INDEX_SHA,
    'contract_sha256':digest(tmp/'configs'/'source_contract_production_v2.json'),
    'registry_sha256':digest(tmp/'registries'/'a003_carriers_v033.json'),
    'a003_source':'analytic_only','static_source_admission_not_physical_dynamics':True,
    'not_a_framework_frozen_certification':True})
  verify(tmp,wb,atlas,base)
  tmp.rename(target)
  return verify(target,wb,atlas,base)
 except Exception:
  if tmp.exists():shutil.rmtree(tmp)
  raise

def main():
 p=argparse.ArgumentParser();p.add_argument('--base',type=Path);p.add_argument('--target',type=Path,required=True);p.add_argument('--workbench',type=Path,required=True);p.add_argument('--atlas',type=Path,required=True);p.add_argument('--verify',action='store_true');a=p.parse_args()
 try:
  result=verify(a.target,a.workbench,a.atlas,a.base) if a.verify else install(a.base,a.target,a.atlas,a.workbench)
  print(json.dumps(result,indent=2));return 0
 except Exception as ex:print('FAIL_CLOSED '+type(ex).__name__+': '+str(ex),file=sys.stderr);return 4
if __name__=='__main__':raise SystemExit(main())
