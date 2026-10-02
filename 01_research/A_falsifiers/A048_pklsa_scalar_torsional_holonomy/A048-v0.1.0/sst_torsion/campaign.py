from pathlib import Path
import csv, json, os
import numpy as np
from .fitting import classify_dispersion
from .geometry import circle, curvature_torsion, winding_number

def analyze_input(input_dir, out_dir, config):
    input_dir=Path(input_dir); out_dir=Path(out_dir); out_dir.mkdir(parents=True,exist_ok=True)
    rows=[]
    for f in sorted(input_dir.glob('case_*.csv')):
        data=np.loadtxt(f,delimiter=',',skiprows=1)
        k=data[:,0]; omega=data[:,1]
        r=classify_dispersion(k,omega,float(config['min_delta_aic']))
        r['anonymous_case_id']=f.stem.replace('case_','')
        rows.append(r)
    # orthogonal numerical controls
    p=circle(512,1.0)
    kap,tau,_,_=curvature_torsion(p)
    circle_err=abs(float(np.mean(kap))-1.0)
    circle_tau=float(np.max(np.abs(tau)))
    th=np.linspace(0,2*np.pi,1024,endpoint=False)
    chi=3*th
    w0=winding_number(chi); w1=winding_number(chi+1.23456789)
    controls={
       'circle_curvature_mean_abs_error':circle_err,
       'circle_torsion_max_abs':circle_tau,
       'winding_base':w0,'winding_shifted':w1,
       'winding_gauge_error':abs(w0-w1),
    }
    summary={
      'backend':os.environ.get('SST_BACKEND','python').lower(),
      'case_count':len(rows),
      'analysis_complete':len(rows)>0 and all(np.isfinite(r['power_exponent_p']) for r in rows),
      'controls':controls,
      'class_counts':{},
    }
    for r in rows: summary['class_counts'][r['classification']]=summary['class_counts'].get(r['classification'],0)+1
    (out_dir/'case_metrics.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    (out_dir/'blind_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    return summary,rows
