import json,csv,sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
out=Path(sys.argv[1])
r=json.loads((out/'blind_results.json').read_text())
lines=['# BLIND RUN REPORT — v0.2.1','',f"Verdict: `{r['verdict']}`",'', '## Gate summary','',
       f"- Spatial covariance: {'PASS' if r['spatial_gate']['pass'] else 'FAIL'} ({r['spatial_gate']['qualified_family_count']}/{r['spatial_gate']['family_count']})",
       f"- Temporal memory: {'PASS' if r['temporal_memory_gate']['pass'] else 'FAIL'} ({r['temporal_memory_gate']['qualified_family_count']}/{r['temporal_memory_gate']['family_count']})",
       f"- Transverse modal gate: {'PASS' if r['kelvin_gate']['pass'] else 'NOT RESOLVED'} ({r['kelvin_gate']['qualified_family_count']}/{r['kelvin_gate']['family_count']})",
       f"- Floquet gate: `{r['floquet_gate']['status']}`",
       f"- Divergence qualification: {'PASS' if r['divergence_gate'] else 'FAIL'}",
       f"- Resolution qualification: {'PASS' if r['resolution_gate'] else 'FAIL'} (exponent span={r['resolution_exponent_span']:.6f})",'',
       '## Family diagnostics','']
for f in r['families']:
    mg=f['memory_gate']; kg=f['kelvin_gate']
    lines.append(f"- {f['family']}: spatial exponent={f['pressure_fit']['exponent']:.6f}, null={f['null_fit']['exponent']:.6f}, temporal exponent={f['temporal_fit']['exponent']:.6f}, memory steps={mg['memory_steps']:.6f}, memory/null={mg['memory_ratio_to_null']:.6f}, modal mode={kg['selected_mode']}, modal fraction={kg['dominant_fraction']:.6f}, phase cycles={kg['phase_cycles']:.6f}.")
lines += ['', '## Interpretation boundary','', 'The blind verdict uses only dimensionless internal observables and decorrelated controls. The transverse-mode gate is reported from the preregistered family-count, modal-energy, phase-linearity and phase-advance criteria; individual families may still remain unresolved. The Floquet stage does not estimate multipliers unless a nontrivial return is first detected for the preregistered carrier. These are scientific outcomes, not runtime errors.','']
(out/'BLIND_RUN_REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
# memory ACF
plt.figure(figsize=(7,4.5))
for f in r['families']:
    a=np.asarray(f['memory_gate']['acf'],float); plt.plot(np.arange(len(a)),a,marker='o',label=f['family'])
plt.axhline(0,linewidth=0.8); plt.xlabel('lag [samples]'); plt.ylabel('mean autocorrelation'); plt.title('Blind temporal-memory diagnostic'); plt.legend(); plt.tight_layout(); plt.savefig(out/'blind_temporal_memory_acf.png',dpi=160); plt.close()
# modes
plt.figure(figsize=(7,4.5))
for f in r['families']:
    k=f['kelvin_gate']; plt.plot(k['mode_numbers'],k['mean_mode_energy'],marker='o',label=f['family'])
plt.yscale('log'); plt.xlabel('transverse mode number'); plt.ylabel('mean modal energy'); plt.title('Blind transverse-mode spectrum'); plt.legend(); plt.tight_layout(); plt.savefig(out/'blind_transverse_mode_spectrum.png',dpi=160); plt.close()
# return residual
fg=r['floquet_gate']; rr=np.asarray(fg.get('residual_series',[]),float)
if len(rr):
    plt.figure(figsize=(7,4.5)); plt.plot(np.arange(len(rr)),rr); plt.xlabel('evolution step'); plt.ylabel('shape return residual'); plt.title('Blind Floquet prerequisite: return search'); plt.tight_layout(); plt.savefig(out/'blind_floquet_return_search.png',dpi=160); plt.close()
print(out/'BLIND_RUN_REPORT.md')
