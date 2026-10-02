from pathlib import Path
import json,sys
p=Path(sys.argv[1]); r=json.loads((p/'blind_results.json').read_text())
lines=['# A050 v0.3.0 BLIND Run Report','',f'**Verdict:** `{r["verdict"]}`','',f'- Modal source-transfer: **{r["modal_transfer_gate"]["pass"]}**',f'- Modal numerical convergence: **{r["modal_transfer_gate"]["numerically_converged"]}**',f'- Temporal memory present: **{r["temporal_memory_transfer_gate"]["present"]}** ({r["temporal_memory_transfer_gate"]["present_base_count"]}/{r["temporal_memory_transfer_gate"]["base_count"]})',f'- Temporal memory converged: **{r["temporal_memory_transfer_gate"]["converged"]}** ({r["temporal_memory_transfer_gate"]["converged_base_count"]}/{r["temporal_memory_transfer_gate"]["base_count"]})',f'- Spatial gate: **{r["spatial_gate"]["pass"]}** ({r["spatial_gate"]["qualified_base_count"]}/{r["spatial_gate"]["base_count"]})',f'- Divergence gate: **{r["divergence_gate"]}**','','## Anonymous source groups']
for s in r['modal_transfer_gate']['source_groups']: lines.append(f'- {s["source_group_id"]}: {s["robust_base_count"]}/{s["base_count"]} robust (required {s["minimum_required"]}) -> {s["pass"]}')
lines+=['','Source identities remain reveal-only. This report is dimensionless and does not interpret a coherent transverse mode as an absolute physical wave speed.']
(p/'BLIND_RUN_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
