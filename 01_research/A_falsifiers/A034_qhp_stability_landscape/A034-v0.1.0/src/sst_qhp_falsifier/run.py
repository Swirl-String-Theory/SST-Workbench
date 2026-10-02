from pathlib import Path
import csv,json,numpy as np
from .solver import velocity_material,segment_lengths,rk4,backend_name
from .geometry import normal_component,best_cyclic_align,radius_gyration
from .manifold import build_neighbors,tangent_for,gram_projection,AXES

def _read_catalog(path):
    with open(path,newline='',encoding='utf-8') as f:
        rows=list(csv.DictReader(f))
    for r in rows:
        for a in AXES: r[a]=float(r[a])
    return rows

def run(prepared,outdir,cfg):
    prep=Path(prepared); out=Path(outdir); out.mkdir(parents=True,exist_ok=True); rows=_read_catalog(prep/'blind_catalog.csv'); z=np.load(prep/'blind_geometries.npz'); X=[np.asarray(z[r['candidate_id']],float) for r in rows]
    neigh=build_neighbors(rows); rec=[]
    gamma=float(cfg.get('gamma_dimensionless',1.)); core=float(cfg.get('core_fraction',.045)); exp=float(cfg.get('core_length_exponent',-.5)); req=bool(cfg.get('require_native',True)); tshort=float(cfg.get('t_short',.05)); dt_factor=float(cfg.get('dt_factor',.01))
    for i,(r,x) in enumerate(zip(rows,X)):
        tang={}; schemes={}
        for a in AXES: tang[a],schemes[a]=tangent_for(i,a,rows,X,neigh)
        ref=segment_lengths(x); u,cores=velocity_material(x,gamma,core,ref,exp,req); up=normal_component(u,x); F,frac=gram_projection(up,tang)
        # short-time independent validation, using fixed material reference lengths
        ds=float(ref.min()); dt0=dt_factor*ds*ds/max(abs(gamma),1e-30); steps=max(2,int(np.ceil(tshort/max(dt0,1e-12)))); dt=tshort/steps; y=x.copy()
        for _ in range(steps): y=rk4(y,dt,gamma,core,ref,exp,req)
        ya,al=best_cyclic_align(y,x,False); disp=normal_component((ya-x)/tshort,x); Fs,frac_s=gram_projection(disp,tang)
        row={'candidate_id':r['candidate_id'],'family_blind':r['family_blind'],'q':r['q'],'h':r['h'],'p':r['p'],'replicate':r.get('replicate','0'),'projection_fraction':frac,'short_projection_fraction':frac_s,'rg_initial':radius_gyration(x),'rg_final_short':radius_gyration(ya),'short_align_mse':al['mse'],'backend':backend_name()}
        for a in AXES:
            row[f'F_{a}']=F.get(a,np.nan); row[f'Fshort_{a}']=Fs.get(a,np.nan); row[f'tangent_{a}_scheme']=schemes[a]; row[f'has_tangent_{a}']=tang[a] is not None
        rec.append(row)
    fields=sorted(set().union(*(r.keys() for r in rec)))
    with (out/'blind_qhp_field.csv').open('w',newline='',encoding='utf-8') as f: wr=csv.DictWriter(f,fieldnames=fields); wr.writeheader(); wr.writerows(rec)
    summary={'format':'SST-QHP-BLIND-1','n_candidates':len(rec),'backend':backend_name(),'family_identity_read':False,'file_identity_read':False,'parameter_coordinates_visible':True,'note':'Worker sees anonymous family/candidate IDs plus QHP coordinates; physical filenames remain sealed until reveal.'}
    (out/'blind_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8'); return summary
