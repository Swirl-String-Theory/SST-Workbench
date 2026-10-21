#!/usr/bin/env python3
"""A006 geometry and optional KnotPlot-native measurements. NOT Euler.

Does not change source XYZ, never imputes missing data, and labels global
KnotPlot data distinctly from component-level independent geometry metrics.
"""
from pathlib import Path
import argparse,csv,json,math,re
import numpy as np
from build_whole import load_xyz,edge_metrics,polygon_length,gauss
from strict_xyz import assert_strict_xyz


def curvature(p):
    a=p-np.roll(p,1,axis=0);b=np.roll(p,-1,axis=0)-p
    al=np.linalg.norm(a,axis=1);bl=np.linalg.norm(b,axis=1)
    den=al*bl*np.linalg.norm(a+b,axis=1)
    k=np.divide(2*np.linalg.norm(np.cross(a,b),axis=1),den,
                out=np.full(len(p),np.nan),where=den>1.e-15)
    return {'kappa_max':float(np.nanmax(k)), 'kappa_p95':float(np.nanpercentile(k,95)),
            'kappa_mean':float(np.nanmean(k)), 'nonfinite':int(np.sum(~np.isfinite(k)))}

def static_measure(path):
    counts=assert_strict_xyz(path)
    p=load_xyz(path)
    rows=[]
    for i,x in enumerate(p):
        r=dict(file=path.name,component=i,nbeads=len(x),**edge_metrics(x),**curvature(x))
        rows.append(r)
    pair=[]
    for i,j in ((0,1),(0,2),(1,2)):
        step_i=max(1,len(p[i])//512);step_j=max(1,len(p[j])//512)
        pair.append({'file':path.name,'pair':f'{i}-{j}',
                     'gauss_midpoint_approx':gauss(p[i][::step_i],p[j][::step_j])})
    return rows,pair

def read_native(path):
    # Format is fixed by metrics_native.py.  Reject stale or missing numeric data.
    out=[]
    with path.open(newline='',encoding='utf-8-sig') as fh:
        reader=csv.DictReader(fh)
        expected=['iteration','nbeads','length','rog','safe']
        if not reader.fieldnames or [x.strip() for x in reader.fieldnames]!=expected:
            raise ValueError(f'Unexpected KnotPlot CSV columns {reader.fieldnames}: {path.name}')
        for r in reader:
            try:
                q={k:float(v) for k,v in r.items()}; i=int(q['iteration'])
                if q['iteration']!=i or i<0 or not all(math.isfinite(v) for v in q.values()):
                    raise ValueError('Nonfinite/bad iteration')
            except (TypeError,ValueError) as e:raise ValueError(f'Bad KnotPlot metric row in {path.name}: {r}') from e
            q['iteration']=i;q['file']=path.name;out.append(q)
    if not out or any(b['iteration']<=a['iteration'] for a,b in zip(out,out[1:])):
        raise ValueError(f'No measurements or nonmonotonic iterations: {path.name}')
    return out

def save_csv(path,records):
    if not records:return
    keys=list(records[0])
    with path.open('w',newline='',encoding='utf-8') as h:
        w=csv.DictWriter(h,fieldnames=keys,extrasaction='ignore');w.writeheader();w.writerows(records)

def plot_native(outdir,rows):
    if not rows:return []
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    files=[]
    for field in ('length','rog','safe'):
        fig,ax=plt.subplots(figsize=(10,5.5))
        for name in sorted(set(r['file'] for r in rows)):
            q=[r for r in rows if r['file']==name]
            ax.plot([r['iteration'] for r in q],[r[field] for r in q],marker='.',label=name.replace('_v042d',''))
        ax.set(xlabel='KnotPlot iteration (ago)',ylabel=field,title='Native KnotPlot '+field+' — recorded, not Euler')
        ax.grid(alpha=.25)
        if len(set(r['file'] for r in rows))<=8:ax.legend(fontsize=6)
        fig.tight_layout();p=outdir/(field+'_vs_iteration.png');fig.savefig(p,dpi=150);plt.close(fig);files.append(str(p))
    return files

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);a=ap.parse_args()
    root=a.root.resolve();geom=root/'output'/'borromean';out=geom/'analysis_v042d';out.mkdir(exist_ok=True)
    paths=sorted(geom.glob('Borromean_*_v042d.xyz'))
    all_rows=[];pairs=[];errors=[]
    for f in paths:
        try:
            r,pp=static_measure(f);all_rows+=r;pairs+=pp
        except Exception as e:errors.append({'file':f.name,'error':str(e)})
    save_csv(out/'component_geometry.csv',all_rows);save_csv(out/'pairwise_gauss_approx.csv',pairs)
    native=[];missing=[]
    for f in sorted((geom/'metrics').glob('*.csv')) if (geom/'metrics').exists() else []:
        if not (f.stem.endswith('_ON') or f.stem.endswith('_OFF')):continue # optional /W,/F raw stream is unqualified
        try:native+=read_native(f)
        except Exception as e:errors.append({'file':f.name,'error':str(e)})
    save_csv(out/'native_knotplot_matrix.csv',native)
    images=plot_native(out,native)
    audit={'geometry_files_found':len(paths),'geometry_components_measured':len(all_rows),
           'native_csv_files_found':len(set(x['file'] for x in native)),
           'native_rows':len(native),'plots':images,'errors':errors,
           'status':'DATA_PRESENT' if native else 'NO_KNOTPLOT_RUNTIME_DATA',
           'scope':'Native records are global KnotPlot values; geometry metrics per component from exact numeric XYZ; no Milnor/Euler certification'}
    (out/'AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps(audit,indent=2));
    if errors:raise SystemExit(1)

if __name__=='__main__':main()
