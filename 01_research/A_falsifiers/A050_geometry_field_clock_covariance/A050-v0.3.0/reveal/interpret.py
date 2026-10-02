from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]
out=Path(sys.argv[1] if len(sys.argv)>1 else 'SST_Geometry_Field_Clock_Covariance_Blind_Falsifier_v0.3.0-outputs')
r=json.loads((out/'blind_results.json').read_text()); panel=json.loads((ROOT/'reveal/SOURCE_PANEL_v0.3.0.json').read_text()); mp={e['anonymous_base_id']:e for e in panel['entries']}
rows=[]
for b in r['primary_bases']:
 e=mp[b['group_id']]; rows.append({'anonymous_id':b['group_id'],'carrier_id':e['carrier_id'],'catalog_id':e['catalog_id'],'source_family':e['source_family'],'provider_group':e['provider_group'],'robust':b['robust'],'baseline_mode':b['baseline']['persistent_mode'],'same_branch_holdouts':b['same_branch_holdout_count'],'memory_present':b['field_memory']['memory_convergence'].get('present_final_two'),'memory_converged':b['field_memory']['memory_convergence'].get('converged')})
rev={'version':'v0.3.0','blind_verdict_unchanged':r['verdict'],'rows':rows,'source_snapshot':panel['source_snapshot'],'interpretation_guard':'Reveal attaches source identity only. It does not alter the frozen blind verdict or promote a numerical transverse mode to a theory-specific physical identification.'}
(out/'REVEALED_INTERPRETATION.json').write_text(json.dumps(rev,indent=2,sort_keys=True),encoding='utf-8'); print(json.dumps(rev,indent=2))
