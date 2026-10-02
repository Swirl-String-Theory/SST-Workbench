from __future__ import annotations
import json
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from .blind import read_private_manifest

def plots(df,run_dir):
    pdir=run_dir/'plots';pdir.mkdir(exist_ok=True);made=[]
    if len(df):
        x=np.arange(len(df))
        plt.figure();plt.axhline(1.0,linestyle='--');plt.plot(x,df['tail_v2_exponent'].astype(float).to_numpy(),'o');plt.xlabel('blind knot index');plt.ylabel(r'tail exponent $n$ in $v^2\propto r^{-n}$');plt.tight_layout();p=pdir/'tail_v2_exponent.png';plt.savefig(p,dpi=180);plt.close();made.append(p.name)
        plt.figure();plt.axhline(1.0,linestyle='--');vals=np.abs(df['tail_poisson_to_amp_ratio'].astype(float).to_numpy());plt.semilogy(x,np.maximum(vals,1e-300),'o');plt.xlabel('blind knot index');plt.ylabel(r'$|\mu_Q/\mu_{v^2}|$');plt.tight_layout();p=pdir/'poisson_to_monopole_ratio.png';plt.savefig(p,dpi=180);plt.close();made.append(p.name)
    return made

def write_report(run_dir,df,rdf,overall):
    mani=read_private_manifest(run_dir/'blind_manifest_private.json')['mapping'];joined=rdf.copy()
    if len(joined): joined['source_name']=[mani.get(b,{}).get('name','?') for b in joined['blind_id']]
    md=df.merge(joined,on='blind_id',how='left') if len(df) else df
    lines=['# Einstein–SST Emergent Metric and Poisson Closure Gates','',f'**Campaign verdict:** `{overall}`','',
    'This package tests the *direct* closure chain on relaxed knot centerlines after a preregistered regularized Biot–Savart reconstruction. A FAIL falsifies this direct mapping for that reconstruction; it does not falsify all possible SST long-range closures.','',
    '## Headline hypotheses','',
    r'1. $\Phi_{\rm SST}=-v^2/2$ plus a Newtonian monopole requires $v^2\propto 1/r$ (equivalently $v\propto r^{-1/2}$).',
    r'2. If $p/\rho_f\simeq\Phi_{\rm SST}$, then $\int_V[\tfrac12|\omega|^2-S\!:\!S]dV$ must approach $4\pi GM\neq0$ and agree with the monopole inferred from $v^2$.','',
    '## Per-knot revealed gates','']
    if len(md):
        cols=[c for c in ['blind_id','source_name','ropelength_estimate','tail_v2_exponent','tail_mu_poisson_log_slope','tail_poisson_to_amp_ratio','monopole_1_over_r','pressure_poisson_monopole','pressure_phi_closure','overall'] if c in md.columns]
        lines.append(md[cols].to_markdown(index=False))
    else:lines.append('No usable knot centerlines were found.')
    lines += ['','## Interpretation rules','',
    '- `monopole_1_over_r=FAIL`: the reconstructed closed-knot velocity tail does not produce the required $1/r$ potential through $\\Phi=-v^2/2$.',
    '- `pressure_poisson_monopole=FAIL`: the pressure-Poisson source integral does not approach the same non-zero monopole strength.',
    '- `pressure_phi_closure=FAIL`: the Bernoulli/Beltrami identification $p/\\rho_f\\simeq-v^2/2$ is not supported in the far-field integral sense.',
    '- Metric determinant and clock columns are algebraic/consistency diagnostics, not independent evidence.','',
    '## Blinding','',
    'Measurement is written under salted blind IDs. Source names are joined only during reveal. Thresholds are copied to `preregistered_config.json` before measurement.','']
    (run_dir/'REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
    if len(md):md.to_csv(run_dir/'revealed_results.csv',index=False)
    return joined
