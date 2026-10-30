"""Create a new portable payload from exact source pins, without running science."""
from collections import Counter, defaultdict
from pathlib import Path
import json
import platform
import shutil
import sys
import numpy as np
from sst_pklsa.combined_atlas import (SCHEMA, CombinedSeedAtlas, need, safe_path, sha,
    load_historical, load_ruban_component, verify_file_manifest)
from pklsa_builder.hashing import geometry_sha256

VERSION_ROOT = Path(__file__).resolve().parent
OUTPUT_NAME = 'SST_Parametric_Knot_Link_Seed_Atlas_v0.4.0_outputs'


def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))


def write(p, obj):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(obj, f, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False); f.write('\n')


def checked_copy(source, target, expected):
    need(source.is_file() and sha(source) == expected, 'Source changed: '+str(source))
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        need(sha(target) == expected, 'Conflicting target: '+str(target))
    else:
        with source.open('rb') as inp, target.open('xb') as out:
            shutil.copyfileobj(inp, out)
    need(sha(target) == expected, 'Copy changed: '+str(target))


def verify_sources(workbench):
    contract = read(VERSION_ROOT/'configs/SOURCE_INTAKE.json')
    for key, base in [('history', workbench/contract['history_relative']),
                      ('ruban', workbench/contract['ruban_relative']), ('raw_sources', workbench)]:
        for rel, expected in contract[key].items():
            p = safe_path(base, rel)
            need(p.is_file() and sha(p) == expected, 'Input integrity: '+str(p))
    for rel, expected in contract['parent_code'].items():
        need(sha(safe_path(VERSION_ROOT, rel)) == expected, 'Frozen parser modified: '+rel)
    return contract


def build_payload(workbench, stage):
    need(not stage.exists(), 'Existing build target')
    contract = verify_sources(workbench)
    stage.mkdir()
    history = workbench/contract['history_relative']
    ruban = workbench/contract['ruban_relative']
    for key, base, dest in [('history', history, stage/'history/v031'),
                            ('ruban', ruban, stage/'research/v036')]:
        print('Copying', key, len(contract[key]), 'files', flush=True)
        for rel, expected in contract[key].items():
            checked_copy(safe_path(base, rel), safe_path(dest, rel), expected)
    for name in ['SOURCE_INTAKE.json','DRIVE_PROVENANCE.json','DRIVE_MANIFEST_SHA256.txt']:
        src = VERSION_ROOT/'configs'/name
        checked_copy(src, stage/'provenance'/name, sha(src))
    raw_map = {}
    for rel, expected in contract['raw_sources'].items():
        src = safe_path(workbench, rel)
        local = f'raw/{expected}/{src.name}'
        checked_copy(src, safe_path(stage, local), expected)
        raw_map[rel] = local
    write(stage/'provenance/RAW_PATH_MAP.json', raw_map)
    campaign = read(history/'CAMPAIGN_INDEX.json')
    status = {t:'PASS' for t in campaign['passed']} | {t:'FAIL' for t in campaign['failed']}
    need(len(status) == contract['expected']['historical_topologies'], 'Historical topology count')
    metrics = {t: {x['carrier_id']:x for x in read(history/f'atlas/{t}/qualification/geometry_metrics.json')['carriers']}
               for t in status}
    records = []
    print('Checking parsed geometry of every historical carrier...', flush=True)
    for ordinal, item in enumerate(read(VERSION_ROOT/'configs/CARRIERS.json')):
        c = item['carrier']; rel = Path(c['source_path']).relative_to(workbench).as_posix()
        parts = load_historical(c, stage/raw_map[rel])
        digest = geometry_sha256(parts)
        need(digest == item['geometry_sha256'], 'Historical geometry changed: '+c['carrier_id'])
        m = metrics[c['topology_id']][c['carrier_id']]
        records.append({'id':c['carrier_id'], 'original_carrier_id':c['carrier_id'],
            'collection':'historical_v031', 'topology_id':c['topology_id'],
            'source_document':'history/v031/'+item['document'],
            'carrier':{**c, 'source_path':raw_map[rel]}, 'raw_path':raw_map[rel],
            'raw_sha256':c['raw_sha256'], 'geometry_sha256':digest,
            'component_count':len(parts), 'component_points':[len(a) for a in parts],
            'units':'Source-native units; see preserved scale_context; not automatically SI',
            'source_provider':c.get('provider_group'), 'source_independence_group':c.get('independence_group'),
            'research_only':False, 'production_admission':None,
            'historical_topology_status':status[c['topology_id']],
            'historical_carrier_qualification':m,
            'gates':{'integrity':'PASS_SOURCE_AND_PARSED_HASH',
                     'geometry':'HISTORICAL_RESULT_PRESERVED', 'scientific':'NOT_REEVALUATED'}})
        if (ordinal+1)%1000 == 0: print('Historical carriers:',ordinal+1,flush=True)
    family = read(ruban/'FAMILY_INDEX.json')
    need(family['research_only'] is True and family['production_admission'] is False, 'Ruban admission drift')
    need(len(family['seeds']) == 3630, 'Ruban count')
    xyz_count = 0
    for seed in family['seeds']:
        need(seed['state']=='RESEARCH_GEOMETRY_UNADMITTED' and seed['dynamic_stability']=='NOT_TESTED'
             and seed['finite_core_qualified'] is False, 'Upstream qualification drift')
        for variant in ['nominal','perturbed']:
            identity = f"RUBAN_v036_{seed['seed_id']}_{variant}"
            parts=[]; components=[]
            for i,c in enumerate(seed['components']):
                need(i == c['component_index'], 'Upstream component ordering')
                path_key, hash_key = ('xyz_path','sha256') if variant=='nominal' else ('perturbed_xyz_path','perturbed_sha256')
                rel=c[path_key]; expected=c[hash_key]
                need(contract['ruban'].get(rel)==expected, 'Family/manifest hash mismatch')
                part=load_ruban_component(safe_path(stage/'research/v036',rel));parts.append(part)
                components.append({'component_index':i,'path':'research/v036/'+rel,'sha256':expected,'point_count':1024})
                xyz_count+=1
            need(len(parts)==seed['component_count'], 'Ruban component count')
            records.append({'id':identity, 'collection':'ruban_v036', 'source_seed_id':seed['seed_id'],
                'variant':variant, 'parent_id':f"RUBAN_v036_{seed['seed_id']}_nominal" if variant=='perturbed' else None,
                'topology_id':seed.get('topology_id'), 'parametric_embedding':seed['parametric_embedding'],
                'topology_mapping_status':'UNMAPPED' if seed.get('topology_id') is None else 'SOURCE_LABEL_PRESERVED_NOT_NEWLY_CERTIFIED',
                'source_document':'research/v036/FAMILY_INDEX.json', 'components':components,
                'component_count':len(parts), 'component_points':[1024]*len(parts),
                'geometry_sha256':geometry_sha256(parts), 'B0':seed['B0'],'R0':seed['R0'],
                'units':'Dimensionless analytic coordinates, R0=1; no calibrated SI length',
                'source_provider':'ruban_analytic', 'source_independence_group':seed['source_independence_group'],
                'state':seed['state'], 'research_only':True,'production_admission':False,
                'dynamic_stability':seed['dynamic_stability'], 'finite_core_qualified':False,
                'polygon_embedding_certificate':seed['polygon_embedding_certificate'],
                'vortexlab_historical_state':seed.get('vortexlab_historical_state'),
                'gates':{'integrity':'PASS_SOURCE_AND_PARSED_HASH','geometry':'PASS_FINITE_COORDINATE_STRUCTURE_ONLY',
                         'scientific':'NOT_RUN'}})
    need(xyz_count==10164, 'Ruban XYZ total')
    pending=read(ruban/'DYNAMICS_PENDING.json')
    need(len(pending['scenarios'])==pending['scenario_count']==54450, 'Scenario count')
    need(all(s['gate']=='PENDING' and s['dynamics_backend']=='NOT_RUN' for s in pending['scenarios']), 'Scenario status changed')
    need(len(records)==len({r['id'] for r in records})==11757,'Record IDs/count')
    geometric=defaultdict(list); raw_groups=defaultdict(list)
    for r in records:
        geometric[r['geometry_sha256']].append(r['id'])
        if r['collection']=='historical_v031':raw_groups[r['raw_sha256']].append(r['id'])
        else:
            for c in r['components']:raw_groups[c['sha256']].append(r['id']+f"/C{c['component_index']:02}")
    write(stage/'DUPLICATES.json', {'policy':'Retain every logical record; raw equality is not carrier equality; geometry equality is ordered float64 equality, not isotopy',
        'exact_geometry_groups':{k:v for k,v in geometric.items() if len(v)>1},
        'shared_raw_groups':{k:v for k,v in raw_groups.items() if len(v)>1}})
    write(stage/'COMBINED_INDEX.json',{'schema':SCHEMA,'version':'v0.4.0','record_count':len(records),
        'no_scientific_promotion':True,'records':records})
    summary={'schema':'PKLSA-COMBINED-VALIDATION-1','version':'v0.4.0','record_count':len(records),
        'historical_carriers':4497,'historical_topologies':2227,'nominal':3630,'perturbed':3630,
        'ruban_component_files':xyz_count,'ruban_manifest_entries':10169,'history_files':len(contract['history']),
        'raw_source_paths':len(contract['raw_sources']),'historical_pass_topologies':len(campaign['passed']),
        'historical_fail_topologies':len(campaign['failed']),'unmapped_nominal':sum(s.get('topology_id') is None for s in family['seeds']),
        'pending_scenarios':54450,'new_independent_analytic_source_groups':len({s['source_independence_group'] for s in family['seeds']}),
        'new_independent_empirical_providers':0,'exact_geometry_duplicate_groups':sum(len(v)>1 for v in geometric.values()),
        'distinct_ordered_geometries':len(geometric),'shared_raw_groups':sum(len(v)>1 for v in raw_groups.values()),
        'source_contract_sha256':sha(VERSION_ROOT/'configs/SOURCE_INTAKE.json'),
        'drive_manifest_sha256':sha(VERSION_ROOT/'configs/DRIVE_MANIFEST_SHA256.txt'),
        'environment':{'python':sys.version,'numpy':np.__version__,'platform':platform.platform()},
        'gates':{'integrity':'PASS','execution':'PASS_BOUNDED_INGESTION_ONLY',
                 'geometry':'PASS_STRUCTURE_AND_HASH_NOT_PHYSICAL_QUALIFICATION','scientific':'NOT_RUN'},
        'historical_qualifications':'BYTE_PRESERVED','full_campaign_executed':False,
        'open_claims':['No new physical dynamics, equilibrium or stability evidence',
                       'No new polygonal isotopy or finite-core certificate',
                       'Unmapped topology IDs remain null; labels do not prove topology',
                       'Research samples do not increase independent provider count']}
    write(stage/'VALIDATION.json',summary)
    write(stage/'family_registry_overlay.json',{'schema':'E010-RESEARCH-FAMILY-REGISTRY-OVERLAY-1',
        'release':'v0.4.0','source_release':'v0.3.6','index_reference_from_output_folder':'research/v036/FAMILY_INDEX.json',
        'admission_mode':'RESEARCH_ONLY_NOT_AUTO_ADMITTED','active_v034_modified':False})
    for package in ['pklsa_builder','sst_pklsa']:
        for src in (VERSION_ROOT/package).glob('*.py'):
            checked_copy(src,stage/package/src.name,sha(src))
    for name in ['verify_atlas.py','README.md','requirements.txt']:
        checked_copy(VERSION_ROOT/name,stage/name,sha(VERSION_ROOT/name))
    write(stage/'FILE_MANIFEST.json',{'schema':'PKLSA-PORTABLE-FILE-MANIFEST-1',
        'files':{p.relative_to(stage).as_posix():sha(p) for p in sorted(stage.rglob('*')) if p.is_file()}})
    verify_file_manifest(stage)
    return summary


def verify_payload(root, *, all_geometries=False):
    count=verify_file_manifest(root)
    atlas=CombinedSeedAtlas(root)
    need(len(atlas.list_ids(include_research=True))==11757,'All record count')
    need(len(atlas.list_ids())==4497,'Research leaked into default selection')
    summary=read(Path(root)/'VALIDATION.json')
    ids=atlas.list_ids(include_research=True) if all_geometries else representative_ids(atlas)
    for identity in ids:
        atlas.load(identity, allow_research=True)
    return {'status':'PASS','manifest_files':count,'loaded_geometries':len(ids),'record_count':11757,
            'index_sha256':sha(Path(root)/'COMBINED_INDEX.json'),'scientific':'NOT_RUN'}


def representative_ids(atlas):
    selected={}
    for identity in atlas.list_ids(include_research=True):
        r=atlas.describe(identity)
        key=(r['collection'],r.get('variant'),r['component_count'],r.get('carrier',{}).get('representation'))
        selected.setdefault(key,identity)
    return sorted(selected.values())
