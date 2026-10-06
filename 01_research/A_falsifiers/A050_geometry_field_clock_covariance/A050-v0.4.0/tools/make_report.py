from pathlib import Path
import json,sys
p=Path(sys.argv[1]); r=json.loads((p/'blind_results.json').read_text())
lines=['# A050 v0.4.0 BLIND Mechanism-Discrimination Report','',f'**Frozen v0.3.2 status:** `{r["parent_diagnostic_status_frozen"]}`','',f'**v0.4.0 mechanism status:** `{r["mechanism_status"]}`','', 'This campaign does not modify the v0.3.0 verdict or v0.3.2 diagnostic status.','', '## Fresh holdout branch replication',f'- Branch gate: **{r["fresh_holdout_replication"]["branch_gate_pass"]}**',f'- Retained primary bases: **{r["fresh_holdout_replication"]["retained_primary_base_count"]}/{r["fresh_holdout_replication"]["primary_base_count"]}**','', '## Mechanism replication']
for m in r['mechanism_summary']: lines.append(f'- {m["mechanism"]}: {m["replicated_primary_base_count"]}/{m["primary_base_count"]} replicated bases; source groups={m["source_groups_confirmed"]} -> **{m["pass"]}**')
lines+=['','## Passed mechanisms', '- '+(', '.join(r['passed_mechanisms']) if r['passed_mechanisms'] else 'none'),'', 'RPO candidate means recurrence evidence only. Floquet/monodromy remains inactive. Source identities remain reveal-only and no numerical mode is preregistered.']
(p/'BLIND_RUN_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
