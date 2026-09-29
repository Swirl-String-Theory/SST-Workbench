import json, sys
from pathlib import Path
import matplotlib.pyplot as plt

def main():
    out=Path(sys.argv[1]); r=json.loads((out/'diagnostic_results.json').read_text())
    a=r['amplitude_summary']
    x=[z['epsilon'] for z in a]; y=[z['strict_target_fraction'] for z in a]
    lo=[z['strict_target_wilson_low'] for z in a]; hi=[z['strict_target_wilson_high'] for z in a]
    fig,ax=plt.subplots(figsize=(7,4.2)); ax.plot(x,y,marker='o'); ax.fill_between(x,lo,hi,alpha=0.2); ax.set_xlabel('nominal perturbation RMS'); ax.set_ylabel('strict m=3 support fraction'); ax.set_ylim(-0.03,1.03); ax.grid(True,alpha=0.25); fig.tight_layout(); fig.savefig(out/'basin_support_profile.png',dpi=160); plt.close(fig)
    fcv=[z['cross_direction_frequency_cv'] if z['cross_direction_frequency_cv'] is not None else float('nan') for z in a]
    fig,ax=plt.subplots(figsize=(7,4.2)); ax.plot(x,fcv,marker='o'); ax.axhline(0.20,ls='--'); ax.set_xlabel('nominal perturbation RMS'); ax.set_ylabel('cross-direction frequency CV'); ax.grid(True,alpha=0.25); fig.tight_layout(); fig.savefig(out/'basin_frequency_robustness.png',dpi=160); plt.close(fig)
    lines=['# A050 v0.2.3 DIAGNOSTIC RUN REPORT','',f"Verdict: `{r['verdict']}`",'',f"Parent verdict (locked): `{r['parent_verdict_locked']}`",'', '## Basin profile','']
    for z in a: lines.append(f"- epsilon={z['epsilon']:.5g}: strict m=3 {z['strict_target_support']}/{z['trajectory_count']}, fraction={z['strict_target_fraction']:.3f}, frequency CV={z['cross_direction_frequency_cv']}")
    lines += ['', '## Interpretation boundary','', 'v0.2.3 is post-confirmatory and outcome-guided. Its result characterizes the local sensitivity of the generated G0002 m=3 branch. It does not revise the v0.2.2 confirmatory verdict and is not a test on production PKLSA/Ridgerunner geometry.']
    (out/'DIAGNOSTIC_RUN_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
if __name__=='__main__': main()
