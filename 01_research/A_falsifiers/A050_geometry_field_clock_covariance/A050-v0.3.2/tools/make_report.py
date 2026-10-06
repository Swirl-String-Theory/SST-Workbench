from pathlib import Path
import json,sys
p=Path(sys.argv[1]); r=json.loads((p/'blind_results.json').read_text())
b=r['branch_retention_gate']; ph=r['phase_diagnostic']
lines=[
 '# A050 v0.3.2 BLIND Diagnostic Report','',
 f'**Frozen parent verdict:** `{r["parent_verdict_frozen"]}`','',
 f'**v0.3.2 diagnostic status:** `{r["diagnostic_status"]}`','',
 'This diagnostic does not modify the parent verdict.','',
 '## Branch identity retention',
 f'- Campaign retention gate: **{b["pass"]}**',
 f'- Retained primary bases: **{b["retained_primary_base_count"]}/{b["primary_base_count"]}**',
 f'- Anonymous source groups confirmed: **{b["source_groups_confirmed"]}**','',
 '## Phase classes',
 f'- Coherent primary baselines: **{ph["coherent_primary_base_count"]}/{b["primary_base_count"]}**',
 f'- Nonstationary-coherent primary baselines: **{ph["nonstationary_coherent_primary_base_count"]}/{b["primary_base_count"]}**',
 '- Angular rate is omega=d(phi)/dt in radians per dimensionless time; cycle rate is f=omega/(2*pi).','',
 '### Primary baseline class counts'
]
for k,v in ph['primary_baseline_class_counts'].items(): lines.append(f'- {k}: {v}')
lines+=['','### Holdout class counts']
for k,v in ph['holdout_class_counts'].items(): lines.append(f'- {k}: {v}')
lines+=['','## Anonymous source groups']
for s in b['source_group_rows']: lines.append(f'- {s["source_group_id"]}: {s["retention_base_count"]}/{s["base_count"]} retained bases (required {s["minimum_required"]}) -> {s["pass"]}')
lines+=['','Source identities remain reveal-only. No numerical mode number is a preregistered target. A recurrent numerical branch is not by itself a physical Kelvin-wave identification or SST validation.']
(p/'BLIND_RUN_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
