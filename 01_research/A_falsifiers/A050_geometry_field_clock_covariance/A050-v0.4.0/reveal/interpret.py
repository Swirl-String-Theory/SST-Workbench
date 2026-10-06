from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]; out=Path(sys.argv[1] if len(sys.argv)>1 else 'SST_Geometry_Field_Clock_Covariance_Blind_Falsifier_v0.4.0-outputs')
r=json.loads((out/'blind_results.json').read_text()); panel=json.loads((ROOT/'reveal/SOURCE_PANEL_v0.3.0.json').read_text()); mp={e['anonymous_base_id']:e for e in panel['entries']}
rows=[]
for b in r['primary_groups']:
    e=mp[b['group_id']]; rows.append({'anonymous_id':b['group_id'],'carrier_id':e['carrier_id'],'catalog_id':e['catalog_id'],'source_family':e['source_family'],'provider_group':e['provider_group'],'baseline_mechanism':b['baseline']['mechanism']['label'],'fresh_branch_retention_fraction':b['fresh_branch_retention_fraction'],'mechanism_replication':{k:v['replicated'] for k,v in b['mechanism_replication'].items()}})
rev={'version':'v0.4.0','blind_status_unchanged':r['mechanism_status'],'rows':rows,'interpretation_guard':'Reveal attaches source identity only. It does not alter v0.3.0/v0.3.2 outcomes or promote a numerical mechanism signature to an SST physical identification.'}
(out/'REVEALED_INTERPRETATION.json').write_text(json.dumps(rev,indent=2,sort_keys=True),encoding='utf-8'); print(json.dumps(rev,indent=2))
