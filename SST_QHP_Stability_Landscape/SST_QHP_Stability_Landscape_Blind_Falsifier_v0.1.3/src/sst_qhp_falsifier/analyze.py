from pathlib import Path
import csv,json,numpy as np
AXES=('q','h','p')


def _rows(path):
    with open(path,newline='',encoding='utf-8') as f:
        rr=list(csv.DictReader(f))
    numeric=(['q','h','p','projection_fraction','short_projection_fraction',
              'basis_condition_number','basis_correlation_condition_number']+
             [f'F_{a}' for a in AXES]+[f'Fshort_{a}' for a in AXES])
    for r in rr:
        for k in numeric:
            try:r[k]=float(r[k])
            except:r[k]=np.nan
    return rr


def _same_slice(a,b,axis,tol=1e-10):
    return (a['family_blind']==b['family_blind'] and
            a.get('replicate','0')==b.get('replicate','0') and
            all(abs(a[k]-b[k])<=tol for k in AXES if k!=axis))


def _crosses_zero(a,b,tol=0.0):
    if not np.isfinite(a) or not np.isfinite(b):
        return False
    return (a<=tol and b>=-tol) or (b<=tol and a>=-tol)


def _root(xa,fa,xb,fb):
    if abs(fb-fa)<1e-30:
        return 0.5*(xa+xb)
    return xa-fa*(xb-xa)/(fb-fa)


def line_crossings(rr,axis,cfg):
    out=[]; groups={}
    min_proj=float(cfg.get('min_projection_fraction',0.0))
    max_cond=float(cfg.get('max_basis_correlation_condition',25.0))
    max_root_frac=float(cfg.get('max_short_root_disagreement_fraction',0.5))

    for r in rr:
        groups.setdefault((r['family_blind'],r.get('replicate','0'),
                           tuple(round(r[k],12) for k in AXES if k!=axis)),[]).append(r)
    for key,vals in groups.items():
        vals=sorted(vals,key=lambda r:r[axis])
        for a,b in zip(vals[:-1],vals[1:]):
            fa,fb=a[f'F_{axis}'],b[f'F_{axis}']
            if not _crosses_zero(fa,fb):
                continue
            width=float(b[axis]-a[axis])
            if abs(width)<1e-15:
                continue
            x0=_root(a[axis],fa,b[axis],fb)
            slope=(fb-fa)/width
            restoring=bool(slope<0)

            fs_a,fs_b=a[f'Fshort_{axis}'],b[f'Fshort_{axis}']
            short_sign_crossing=_crosses_zero(fs_a,fs_b)
            slope_s=(fs_b-fs_a)/width if np.isfinite(fs_a) and np.isfinite(fs_b) else np.nan
            short_root=_root(a[axis],fs_a,b[axis],fs_b) if short_sign_crossing else np.nan
            short_restoring=bool(short_sign_crossing and np.isfinite(slope_s) and slope_s<0)
            root_disagreement=(abs(short_root-x0)/abs(width)) if np.isfinite(short_root) else np.nan
            root_agrees=bool(np.isfinite(root_disagreement) and root_disagreement<=max_root_frac)

            proj_vals=[a.get('projection_fraction',np.nan),b.get('projection_fraction',np.nan),
                       a.get('short_projection_fraction',np.nan),b.get('short_projection_fraction',np.nan)]
            projection_qualified=bool(all(np.isfinite(v) and v>=min_proj for v in proj_vals))
            cond_vals=[a.get('basis_correlation_condition_number',np.nan),b.get('basis_correlation_condition_number',np.nan)]
            basis_qualified=bool(all(np.isfinite(v) and v<=max_cond for v in cond_vals))
            confirmed=bool(restoring and short_restoring and root_agrees and projection_qualified and basis_qualified)

            out.append({
                'family_blind':key[0],'replicate':key[1],'axis':axis,
                'q_slice':np.mean([a['q'],b['q']]) if axis!='q' else x0,
                'h_slice':np.mean([a['h'],b['h']]) if axis!='h' else x0,
                'p_slice':np.mean([a['p'],b['p']]) if axis!='p' else x0,
                'root_coordinate':x0,'F_slope':slope,
                'short_sign_crossing':short_sign_crossing,
                'short_root_coordinate':short_root,
                'Fshort_slope':slope_s,
                'root_disagreement_fraction':root_disagreement,
                'restoring':restoring,'short_restoring':short_restoring,
                'projection_qualified':projection_qualified,
                'basis_qualified':basis_qualified,
                'confirmed_restoring':confirmed,
                'bracket_low':a[axis],'bracket_high':b[axis]
            })
    return out


def local_jacobian(rr,i,prefix='F_'):
    r0=rr[i]; J=np.full((3,3),np.nan); usable=[]
    for j,axisx in enumerate(AXES):
        cand=[r for r in rr if _same_slice(r0,r,axisx) and r is not r0]
        lo=[r for r in cand if r[axisx]<r0[axisx]]; hi=[r for r in cand if r[axisx]>r0[axisx]]
        if not lo or not hi:
            continue
        a=max(lo,key=lambda r:r[axisx]); b=min(hi,key=lambda r:r[axisx]); dx=b[axisx]-a[axisx]
        if abs(dx)<1e-15:
            continue
        for k,axisf in enumerate(AXES):
            J[k,j]=(b[f'{prefix}{axisf}']-a[f'{prefix}{axisf}'])/dx
        usable.append(axisx)
    if len(usable)<3 or not np.isfinite(J).all():
        return None
    return J


def _local_bounds(rr,r):
    bounds=[]
    for a in AXES:
        cand=[z for z in rr if _same_slice(r,z,a) and z is not r]
        lo=[z[a] for z in cand if z[a]<r[a]]; hi=[z[a] for z in cand if z[a]>r[a]]
        if not lo or not hi:
            return None
        bounds.append((max(lo),min(hi)))
    return bounds


def _inside(star,bounds,tol=1e-12):
    return bool(all(star[j]>=bounds[j][0]-tol and star[j]<=bounds[j][1]+tol for j in range(3)))


def _star_agrees(a,b,bounds,max_fraction):
    if not np.isfinite(a).all() or not np.isfinite(b).all():
        return False,np.nan
    fracs=[]
    for j,(L,H) in enumerate(bounds):
        width=max(abs(H-L),1e-30)
        fracs.append(abs(a[j]-b[j])/width)
    return bool(max(fracs)<=max_fraction),float(max(fracs))


def analyze(blind_dir,outdir,cfg):
    out=Path(outdir); out.mkdir(parents=True,exist_ok=True)
    rr=_rows(Path(blind_dir)/'blind_qhp_field.csv')
    crosses=[]
    for a in AXES:
        crosses.extend(line_crossings(rr,a,cfg))

    cross_fields=['family_blind','replicate','axis','q_slice','h_slice','p_slice','root_coordinate',
                  'F_slope','short_sign_crossing','short_root_coordinate','Fshort_slope',
                  'root_disagreement_fraction','restoring','short_restoring','projection_qualified',
                  'basis_qualified','confirmed_restoring','bracket_low','bracket_high']
    with (out/'blind_zero_crossings.csv').open('w',newline='',encoding='utf-8') as f:
        wr=csv.DictWriter(f,fieldnames=cross_fields); wr.writeheader(); wr.writerows(crosses)

    pts=[]
    norm_max=float(cfg.get('fixed_point_field_norm_max',0.05))
    min_proj=float(cfg.get('min_projection_fraction',0.05))
    max_cond=float(cfg.get('max_basis_correlation_condition',25.0))
    for i,r in enumerate(rr):
        F=np.array([r[f'F_{a}'] for a in AXES],float)
        Fs=np.array([r[f'Fshort_{a}'] for a in AXES],float)
        if not np.isfinite(F).all() or not np.isfinite(Fs).all():
            continue
        J=local_jacobian(rr,i,'F_'); Js=local_jacobian(rr,i,'Fshort_')
        if J is None or Js is None:
            continue
        fn=float(np.linalg.norm(F)); fsn=float(np.linalg.norm(Fs))
        ev=np.linalg.eigvals(J); evs=np.linalg.eigvals(Js)
        maxre=float(np.max(ev.real)); maxres=float(np.max(evs.real))
        stable=maxre<0; stable_short=maxres<0
        proj_ok=bool(np.isfinite(r['projection_fraction']) and r['projection_fraction']>=min_proj and
                     np.isfinite(r['short_projection_fraction']) and r['short_projection_fraction']>=min_proj)
        basis_ok=bool(np.isfinite(r['basis_correlation_condition_number']) and
                      r['basis_correlation_condition_number']<=max_cond)
        confirmed=bool(stable and stable_short and fn<=norm_max and fsn<=norm_max and proj_ok and basis_ok)
        pts.append({
            'candidate_id':r['candidate_id'],'family_blind':r['family_blind'],
            'q':r['q'],'h':r['h'],'p':r['p'],
            'field_norm':fn,'short_field_norm':fsn,
            'projection_fraction':r['projection_fraction'],'short_projection_fraction':r['short_projection_fraction'],
            'basis_correlation_condition_number':r['basis_correlation_condition_number'],
            'jacobian_max_real_eigenvalue':maxre,
            'jacobian_eigenvalues':';'.join(f'{z.real:.9g}{z.imag:+.9g}j' for z in ev),
            'short_jacobian_max_real_eigenvalue':maxres,
            'short_jacobian_eigenvalues':';'.join(f'{z.real:.9g}{z.imag:+.9g}j' for z in evs),
            'stable_linear':stable,'short_stable_linear':stable_short,
            'projection_qualified':proj_ok,'basis_qualified':basis_ok,
            'fixed_point_candidate':confirmed
        })

    pfields=['candidate_id','family_blind','q','h','p','field_norm','short_field_norm',
             'projection_fraction','short_projection_fraction','basis_correlation_condition_number',
             'jacobian_max_real_eigenvalue','jacobian_eigenvalues',
             'short_jacobian_max_real_eigenvalue','short_jacobian_eigenvalues',
             'stable_linear','short_stable_linear','projection_qualified','basis_qualified','fixed_point_candidate']
    with (out/'blind_fixed_point_candidates.csv').open('w',newline='',encoding='utf-8') as f:
        wr=csv.DictWriter(f,fieldnames=pfields); wr.writeheader(); wr.writerows(pts)

    # Local affine fixed-point solve using both instantaneous and short-time vector fields.
    affine=[]
    max_aff_frac=float(cfg.get('max_affine_root_disagreement_fraction',0.5))
    for i,r in enumerate(rr):
        F0=np.array([r[f'F_{a}'] for a in AXES],float)
        Fs0=np.array([r[f'Fshort_{a}'] for a in AXES],float)
        if not np.isfinite(F0).all() or not np.isfinite(Fs0).all():
            continue
        J=local_jacobian(rr,i,'F_'); Js=local_jacobian(rr,i,'Fshort_')
        if J is None or Js is None or abs(np.linalg.det(J))<1e-12 or abs(np.linalg.det(Js))<1e-12:
            continue
        bounds=_local_bounds(rr,r)
        if bounds is None:
            continue
        ev=np.linalg.eigvals(J); evs=np.linalg.eigvals(Js)
        stable=bool(np.max(ev.real)<0); stable_s=bool(np.max(evs.real)<0)
        xi0=np.array([r[a] for a in AXES],float)
        star=xi0-np.linalg.solve(J,F0)
        star_s=xi0-np.linalg.solve(Js,Fs0)
        inside=_inside(star,bounds); inside_s=_inside(star_s,bounds)
        root_agree,root_dis=max_aff_frac>=0 and _star_agrees(star,star_s,bounds,max_aff_frac) or (False,np.nan)
        proj_ok=bool(np.isfinite(r['projection_fraction']) and r['projection_fraction']>=min_proj and
                     np.isfinite(r['short_projection_fraction']) and r['short_projection_fraction']>=min_proj)
        basis_ok=bool(np.isfinite(r['basis_correlation_condition_number']) and
                      r['basis_correlation_condition_number']<=max_cond)
        confirmed=bool(stable and stable_s and inside and inside_s and root_agree and proj_ok and basis_ok)
        affine.append({
            'family_blind':r['family_blind'],'replicate':r.get('replicate','0'),
            'anchor_candidate_id':r['candidate_id'],
            'q_star':float(star[0]),'h_star':float(star[1]),'p_star':float(star[2]),
            'short_q_star':float(star_s[0]),'short_h_star':float(star_s[1]),'short_p_star':float(star_s[2]),
            'anchor_field_norm':float(np.linalg.norm(F0)),
            'anchor_short_field_norm':float(np.linalg.norm(Fs0)),
            'jacobian_max_real_eigenvalue':float(np.max(ev.real)),
            'jacobian_eigenvalues':';'.join(f'{z.real:.9g}{z.imag:+.9g}j' for z in ev),
            'short_jacobian_max_real_eigenvalue':float(np.max(evs.real)),
            'short_jacobian_eigenvalues':';'.join(f'{z.real:.9g}{z.imag:+.9g}j' for z in evs),
            'stable_linear':stable,'short_stable_linear':stable_s,
            'instant_root_inside_cell':inside,'short_root_inside_cell':inside_s,
            'affine_root_disagreement_fraction':root_dis,
            'affine_roots_agree':root_agree,
            'projection_qualified':proj_ok,'basis_qualified':basis_ok,
            'confirmed_affine_fixed_point':confirmed
        })

    afields=['family_blind','replicate','anchor_candidate_id','q_star','h_star','p_star',
             'short_q_star','short_h_star','short_p_star','anchor_field_norm','anchor_short_field_norm',
             'jacobian_max_real_eigenvalue','jacobian_eigenvalues',
             'short_jacobian_max_real_eigenvalue','short_jacobian_eigenvalues',
             'stable_linear','short_stable_linear','instant_root_inside_cell','short_root_inside_cell',
             'affine_root_disagreement_fraction','affine_roots_agree','projection_qualified','basis_qualified',
             'confirmed_affine_fixed_point']
    with (out/'blind_affine_fixed_point_candidates.csv').open('w',newline='',encoding='utf-8') as f:
        wr=csv.DictWriter(f,fieldnames=afields); wr.writeheader(); wr.writerows(affine)

    nrest=sum(bool(c['confirmed_restoring']) for c in crosses)
    nfp=sum(bool(p['fixed_point_candidate']) for p in pts)
    naff=sum(bool(a['confirmed_affine_fixed_point']) for a in affine)
    proj_vals=[r.get('projection_fraction',np.nan) for r in rr]+[r.get('short_projection_fraction',np.nan) for r in rr]
    finite_proj=[float(v) for v in proj_vals if np.isfinite(v)]
    max_proj=max(finite_proj) if finite_proj else None
    n_proj_rows=sum(bool(np.isfinite(r.get('projection_fraction',np.nan)) and r['projection_fraction']>=min_proj and
                         np.isfinite(r.get('short_projection_fraction',np.nan)) and r['short_projection_fraction']>=min_proj)
                    for r in rr)

    if nrest>=int(cfg.get('min_confirmed_restoring_crossings',1)) or nfp>0 or naff>0:
        verdict='PASS_CANDIDATE_RESTORING_STRUCTURE'
    elif finite_proj and max_proj<min_proj:
        verdict='INDETERMINATE_WEAK_QHP_MANIFOLD_COUPLING'
    elif crosses or pts or affine:
        verdict='FAIL_NO_RESTORING_STRUCTURE'
    else:
        verdict='INDETERMINATE_INSUFFICIENT_GRID'

    summary={
        'format':'SST-QHP-ANALYZE-1.3','verdict':verdict,
        'n_zero_crossings':len(crosses),
        'n_confirmed_restoring_crossings':nrest,
        'n_fixed_point_candidates':nfp,
        'n_confirmed_affine_fixed_points':naff,
        'n_projection_qualified_rows':n_proj_rows,
        'max_observed_projection_fraction':max_proj,
        'min_projection_fraction_gate':min_proj,
        'short_confirmation_policy':'actual short-time sign crossing/root agreement required; negative slope alone is insufficient',
        'caution':'PASS means a numerical restoring candidate on the sampled QHP manifold, not proof of physical knot stability or SST ontology.'
    }
    (out/'blind_analysis_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    return summary
