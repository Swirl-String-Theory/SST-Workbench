from pathlib import Path
import csv,json,numpy as np
from .solver import velocity_material,segment_lengths,rk4,backend_name
from .geometry import normal_component,best_cyclic_align,radius_gyration
from .manifold import build_neighbors,tangent_for,gram_projection,AXES


def _read_catalog(path):
    with open(path,newline='',encoding='utf-8') as f:
        rows=list(csv.DictReader(f))
    for r in rows:
        for a in AXES:
            r[a]=float(r[a])
    return rows


def _reference_indices(rows):
    groups={}
    for i,r in enumerate(rows):
        groups.setdefault((r['family_blind'],r.get('replicate','0')),[]).append(i)
    refs={}
    for key,idxs in groups.items():
        c=np.array([[rows[i][a] for a in AXES] for i in idxs],float)
        z=np.where(np.linalg.norm(c,axis=1)<=1e-14)[0]
        if len(z):
            refs[key]=idxs[int(z[0])]
        else:
            med=np.median(c,axis=0)
            refs[key]=idxs[int(np.argmin(np.sum((c-med)**2,axis=1)))]
    return refs


def _gram_metrics(tangents):
    active=[a for a,T in tangents.items() if T is not None]
    if not active:
        return np.nan,np.nan,''
    A=np.array([[np.sum(tangents[a]*tangents[b]) for b in active] for a in active],float)
    raw=float(np.linalg.cond(A)) if len(active)>1 else 1.0
    d=np.sqrt(np.maximum(np.diag(A),1e-300))
    C=A/np.outer(d,d)
    corr=float(np.linalg.cond(C)) if len(active)>1 else 1.0
    return raw,corr,','.join(active)


def _transport_reference_basis(reference_basis,x):
    out={}
    for a,T in reference_basis.items():
        if T is None:
            out[a]=None
            continue
        V=normal_component(T,x)
        if float(np.sum(V*V))<1e-16:
            out[a]=None
        else:
            out[a]=V
    return out


def run(prepared,outdir,cfg):
    prep=Path(prepared); out=Path(outdir); out.mkdir(parents=True,exist_ok=True)
    rows=_read_catalog(prep/'blind_catalog.csv')
    z=np.load(prep/'blind_geometries.npz')
    X=[np.asarray(z[r['candidate_id']],float) for r in rows]
    neigh=build_neighbors(rows)

    # v0.1.3: construct ONE local QHP coordinate basis per family/replicate at the
    # reference geometry, then transport that same basis to every candidate.
    # This keeps F_q/F_h/F_p comparable across the whole 1-D star or 3-D grid.
    refs=_reference_indices(rows)
    bases={}; basis_schemes={}; basis_ref_ids={}
    for key,i0 in refs.items():
        b={}; s={}
        for a in AXES:
            b[a],s[a]=tangent_for(i0,a,rows,X,neigh)
        bases[key]=b; basis_schemes[key]=s; basis_ref_ids[key]=rows[i0]['candidate_id']

    rec=[]
    gamma=float(cfg.get('gamma_dimensionless',1.0))
    core=float(cfg.get('core_fraction',0.045))
    exp=float(cfg.get('core_length_exponent',-0.5))
    req=bool(cfg.get('require_native',True))
    tshort=float(cfg.get('t_short',0.05))
    dt_factor=float(cfg.get('dt_factor',0.01))

    for i,(r,x) in enumerate(zip(rows,X)):
        key=(r['family_blind'],r.get('replicate','0'))
        tang=_transport_reference_basis(bases[key],x)
        raw_cond,corr_cond,active_axes=_gram_metrics(tang)
        ref=segment_lengths(x)
        u,cores=velocity_material(x,gamma,core,ref,exp,req)
        up=normal_component(u,x)
        F,frac=gram_projection(up,tang)

        # Short-time independent validation, with the same family reference basis.
        ds=float(ref.min())
        dt0=dt_factor*ds*ds/max(abs(gamma),1e-30)
        steps=max(2,int(np.ceil(tshort/max(dt0,1e-12))))
        dt=tshort/steps
        y=x.copy()
        for _ in range(steps):
            y=rk4(y,dt,gamma,core,ref,exp,req)
        ya,al=best_cyclic_align(y,x,False)
        disp=normal_component((ya-x)/tshort,x)
        Fs,frac_s=gram_projection(disp,tang)

        row={
            'candidate_id':r['candidate_id'],
            'family_blind':r['family_blind'],
            'q':r['q'],'h':r['h'],'p':r['p'],'replicate':r.get('replicate','0'),
            'projection_fraction':frac,
            'short_projection_fraction':frac_s,
            'basis_condition_number':raw_cond,
            'basis_correlation_condition_number':corr_cond,
            'basis_active_axes':active_axes,
            'basis_reference_candidate_id':basis_ref_ids[key],
            'rg_initial':radius_gyration(x),
            'rg_final_short':radius_gyration(ya),
            'short_align_mse':al['mse'],
            'backend':backend_name(),
        }
        for a in AXES:
            row[f'F_{a}']=F.get(a,np.nan)
            row[f'Fshort_{a}']=Fs.get(a,np.nan)
            row[f'tangent_{a}_scheme']='reference_'+basis_schemes[key][a]
            row[f'has_tangent_{a}']=tang[a] is not None
        rec.append(row)

    fields=sorted(set().union(*(r.keys() for r in rec)))
    with (out/'blind_qhp_field.csv').open('w',newline='',encoding='utf-8') as f:
        wr=csv.DictWriter(f,fieldnames=fields); wr.writeheader(); wr.writerows(rec)
    summary={
        'format':'SST-QHP-BLIND-1.3',
        'n_candidates':len(rec),
        'backend':backend_name(),
        'projection_basis_policy':'family-reference QHP basis transported to every candidate',
        'family_identity_read':False,
        'file_identity_read':False,
        'parameter_coordinates_visible':True,
        'note':'Worker sees anonymous family/candidate IDs plus QHP coordinates; physical filenames remain sealed until reveal.'
    }
    (out/'blind_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    return summary
