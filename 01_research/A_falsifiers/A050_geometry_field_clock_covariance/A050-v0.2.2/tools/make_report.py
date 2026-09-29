import json,sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
out=Path(sys.argv[1]); r=json.loads((out/'blind_results.json').read_text())
mg=r['temporal_memory_gate']; pg=r['modal_persistence_gate']
lines=['# BLIND RUN REPORT — v0.2.2','',f"Verdict: `{r['verdict']}`",'', '## Gate summary','',
 f"- Spatial covariance: {'PASS' if r['spatial_gate']['pass'] else 'FAIL'} ({r['spatial_gate']['qualified_family_count']}/{r['spatial_gate']['family_count']})",
 f"- Temporal memory reproduced: {'YES' if mg['present'] else 'NO'} ({mg['present_family_count']}/{mg['family_count']})",
 f"- Temporal memory converged: {'YES' if mg['converged'] else 'NO'} ({mg['converged_family_count']}/{mg['family_count']})",
 f"- Modal persistence reproduced: {'YES' if pg['reproduced'] else 'NO'} ({pg['confirmed_group_count']}/{pg['group_count']} groups)",
 f"- Modal numerical convergence: {'YES' if pg['numerically_converged'] else 'NO'} ({pg['qualified_confirmed_group_count']} qualified groups)",
 f"- Floquet policy: inactive; prior status `{r['floquet_policy']['prior_status']}`",
 f"- Divergence qualification: {'PASS' if r['divergence_gate'] else 'FAIL'}",
 f"- Spatial resolution qualification: {'PASS' if r['resolution_gate'] else 'FAIL'}",'',
 '## Anonymous holdout groups','']
for g in r['holdout_groups']:
    lines.append(f"- {g['group_id']}: `{g['status']}`, branch={g['branch_mode']}, support={g['supporting_replicates']}/{g['replicate_count']}.")
lines += ['', '## Interpretation boundary','', 'This report is blind. Anonymous holdout groups are not assigned geometry identities here. A confirmed transverse branch is a numerical persistence result under the frozen protocol, not an absolute physical wave-speed claim. Floquet/RPO inference is outside v0.2.2.','']
(out/'BLIND_RUN_REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
# memory convergence plot
plt.figure(figsize=(7,4.5))
for f in r['families']:
    w=f['memory_convergence']['windows']; x=[z['window_steps'] for z in w]; y=[z['ips_memory_steps'] for z in w]
    plt.plot(x,y,marker='o',label=f['family'])
plt.xlabel('evolution horizon [steps]'); plt.ylabel('IPS memory [sample steps]'); plt.title('Blind temporal-memory convergence'); plt.legend(); plt.tight_layout(); plt.savefig(out/'blind_temporal_memory_convergence.png',dpi=160); plt.close()
# group support
plt.figure(figsize=(7,4.5)); gs=r['holdout_groups']; x=np.arange(len(gs)); y=[g['supporting_replicates'] for g in gs]
plt.bar(x,y); plt.xticks(x,[g['group_id'] for g in gs]); plt.ylim(0,5.5); plt.ylabel('persistent same-branch replicates / 5'); plt.title('Blind modal persistence replication'); plt.tight_layout(); plt.savefig(out/'blind_modal_persistence_groups.png',dpi=160); plt.close()
print(out/'BLIND_RUN_REPORT.md')
