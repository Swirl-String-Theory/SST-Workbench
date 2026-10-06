from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]
out=Path(sys.argv[1] if len(sys.argv)>1 else 'SST_Geometry_Field_Clock_Covariance_Blind_Falsifier_v0.3.2-outputs')
r=json.loads((out/'blind_results.json').read_text()); panel=json.loads((ROOT/'reveal/SOURCE_PANEL_v0.3.0.json').read_text()); mp={e['anonymous_base_id']:e for e in panel['entries']}
rows=[]
for b in r['primary_groups']:
 e=mp[b['group_id']]; bp=b['baseline']['branch_phase']; p=bp['phase']
 rows.append({'anonymous_id':b['group_id'],'carrier_id':e['carrier_id'],'catalog_id':e['catalog_id'],'source_family':e['source_family'],'provider_group':e['provider_group'],'branch_mode':bp['branch_identity']['reference_mode'],'branch_stable':bp['branch_identity']['stable'],'retained_holdouts':b['retained_holdout_count'],'holdout_count':b['holdout_count'],'phase_class':p['classification'],'angular_rate_sign_reversals':p.get('angular_rate_sign_reversal_count')})
rev={'version':'v0.3.2','frozen_parent_verdict':r['parent_verdict_frozen'],'diagnostic_status_unchanged':r['diagnostic_status'],'rows':rows,'source_snapshot':panel['source_snapshot'],'interpretation_guard':'Reveal attaches source identity only. It does not alter the frozen v0.3.0 verdict, the v0.3.2 blind diagnostic status, or promote a numerical transverse branch to a theory-specific physical identification.'}
(out/'REVEALED_INTERPRETATION.json').write_text(json.dumps(rev,indent=2,sort_keys=True),encoding='utf-8'); print(json.dumps(rev,indent=2))
