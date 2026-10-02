from __future__ import annotations
from pathlib import Path
import csv
import numpy as np

def make_reports(out_dir, final, results, mapping):
    out=Path(out_dir); plots=out/'plots';plots.mkdir(exist_ok=True)
    try:
        import matplotlib.pyplot as plt
    except Exception:
        plt=None
    rows=[]
    for bid,r in results.items():
        sc=final['blind_scores'][bid]; rows.append(dict(blind_id=bid,source=mapping[bid]['source'],status=sc['status'],**sc['metrics']))
    if rows:
        keys=[]
        for row in rows:
            for k in row:
                if k not in keys and not isinstance(row[k],(list,dict)):keys.append(k)
        with (out/'summary_metrics.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows([{k:r.get(k) for k in keys} for r in rows])
    md=['# SST Trefoil Lobe-Orientation Blind Falsifier','',f"**Overall verdict:** `{final['overall']}`",'', '## Unblinded datasets']
    for bid in sorted(results):
        src=mapping[bid]['source'];sc=final['blind_scores'][bid];md += ['',f"### {bid} → {src}",f"Status: **{sc['status']}**",'', '| Gate | Pass |','|---|---:|']+[f"| {k} | {v} |" for k,v in sc['gates'].items()]
    md += ['','## Circle null controls']
    for bid,z in sorted(final['circle_nulls'].items()): md += [f"- {bid}: radial mean `{z['radial_velocity_mean']:.6e}`, pass `{z['pass_null']}`"]
    md += ['', '## Interpretation','`PASS` means both independent trefoil representations passed the preregistered critical gates. `FAIL` means at least one critical mechanism gate failed with numerically converged data. `INCONCLUSIVE` is used when numerical/core-clearance prerequisites fail.','', 'No reconnection operator is present anywhere in this package; a near-core event is reported, not repaired or reconnected.']
    (out/'REPORT.md').write_text('\n'.join(md),encoding='utf-8')
    if plt is None:return
    for bid,r in results.items():
        x=np.asarray(r['geometry']); fig=plt.figure(figsize=(7,6));ax=fig.add_subplot(111,projection='3d');lab=np.asarray(r['labels']);
        for k in range(3):
            q=x[lab==k];ax.plot(q[:,0],q[:,1],q[:,2],lw=1.2,label=f'lobe {k+1}')
        ax.set_title(f'{bid}: resampled blind geometry');ax.legend();fig.tight_layout();fig.savefig(plots/f'{bid}_geometry.png',dpi=180);plt.close(fig)
        j=r['jacobians'][len(r['jacobians'])//2]['eigs']; fig,ax=plt.subplots(figsize=(6,5));
        for key,mark in [('total','o'),('without_cross','x'),('cross_lobe','s')]:
            ev=j[key]['eigenvalues'];ax.scatter([z['re'] for z in ev],[z['im'] for z in ev],marker=mark,label=key)
        ax.axvline(0,lw=.8);ax.axhline(0,lw=.8);ax.set_xlabel('Re λ');ax.set_ylabel('Im λ');ax.set_title(f'{bid}: reduced Jacobian spectrum');ax.legend();fig.tight_layout();fig.savefig(plots/f'{bid}_eigenvalues.png',dpi=180);plt.close(fig)
        rd=r.get('ringdown')
        if rd and rd.get('history'):
            h=rd['history'];fig,ax=plt.subplots(figsize=(7,4));ax.plot([z['t'] for z in h],[z['mode_amplitude'] for z in h]);ax.set_xlabel('dimensionless time');ax.set_ylabel(rd['mode']);ax.set_title(f'{bid}: nonlinear ringdown');fig.tight_layout();fig.savefig(plots/f'{bid}_ringdown.png',dpi=180);plt.close(fig)
