from pathlib import Path
import csv,json,numpy as np
AXES=('q','h','p')

def _rows(path):
    with open(path,newline='',encoding='utf-8') as f: rr=list(csv.DictReader(f))
    for r in rr:
        for k in ['q','h','p','projection_fraction','short_projection_fraction']+[f'F_{a}' for a in AXES]+[f'Fshort_{a}' for a in AXES]:
            try:r[k]=float(r[k])
            except:r[k]=np.nan
    return rr

def _same_slice(a,b,axis,tol=1e-10): return a['family_blind']==b['family_blind'] and a.get('replicate','0')==b.get('replicate','0') and all(abs(a[k]-b[k])<=tol for k in AXES if k!=axis)
def line_crossings(rr,axis,cfg):
    out=[]; groups={}
    for r in rr: groups.setdefault((r['family_blind'],r.get('replicate','0'),tuple(round(r[k],12) for k in AXES if k!=axis)),[]).append(r)
    for key,vals in groups.items():
        vals=sorted(vals,key=lambda r:r[axis])
        for a,b in zip(vals[:-1],vals[1:]):
            fa,fb=a[f'F_{axis}'],b[f'F_{axis}'];
            if not np.isfinite(fa) or not np.isfinite(fb) or fa*fb>0: continue
            x0=a[axis] if abs(fb-fa)<1e-30 else a[axis]-fa*(b[axis]-a[axis])/(fb-fa); slope=(fb-fa)/(b[axis]-a[axis]); restoring=slope<0
            fs_a,fs_b=a[f'Fshort_{axis}'],b[f'Fshort_{axis}']; slope_s=(fs_b-fs_a)/(b[axis]-a[axis]) if np.isfinite(fs_a+fs_b) else np.nan
            out.append({'family_blind':key[0],'replicate':key[1],'axis':axis,'q_slice':np.mean([a['q'],b['q']]) if axis!='q' else x0,'h_slice':np.mean([a['h'],b['h']]) if axis!='h' else x0,'p_slice':np.mean([a['p'],b['p']]) if axis!='p' else x0,'root_coordinate':x0,'F_slope':slope,'Fshort_slope':slope_s,'restoring':bool(restoring),'short_restoring':bool(np.isfinite(slope_s) and slope_s<0),'bracket_low':a[axis],'bracket_high':b[axis]})
    return out

def local_jacobian(rr,i):
    r0=rr[i]; J=np.full((3,3),np.nan); usable=[]
    for j,axisx in enumerate(AXES):
        cand=[r for r in rr if _same_slice(r0,r,axisx) and r is not r0]
        lo=[r for r in cand if r[axisx]<r0[axisx]]; hi=[r for r in cand if r[axisx]>r0[axisx]]
        if not lo or not hi: continue
        a=max(lo,key=lambda r:r[axisx]); b=min(hi,key=lambda r:r[axisx]); dx=b[axisx]-a[axisx]
        if abs(dx)<1e-15: continue
        for k,axisf in enumerate(AXES): J[k,j]=(b[f'F_{axisf}']-a[f'F_{axisf}'])/dx
        usable.append(axisx)
    if len(usable)<3 or not np.isfinite(J).all(): return None
    return J

def analyze(blind_dir,outdir,cfg):
    out=Path(outdir); out.mkdir(parents=True,exist_ok=True); rr=_rows(Path(blind_dir)/'blind_qhp_field.csv'); crosses=[]
    for a in AXES: crosses.extend(line_crossings(rr,a,cfg))
    with (out/'blind_zero_crossings.csv').open('w',newline='',encoding='utf-8') as f:
        fields=['family_blind','replicate','axis','q_slice','h_slice','p_slice','root_coordinate','F_slope','Fshort_slope','restoring','short_restoring','bracket_low','bracket_high']; wr=csv.DictWriter(f,fieldnames=fields); wr.writeheader(); wr.writerows(crosses)
    pts=[]; norm_max=float(cfg.get('fixed_point_field_norm_max',0.05)); min_proj=float(cfg.get('min_projection_fraction',0.05))
    for i,r in enumerate(rr):
        F=np.array([r[f'F_{a}'] for a in AXES]);
        if not np.isfinite(F).all(): continue
        J=local_jacobian(rr,i); fn=float(np.linalg.norm(F))
        if J is None: continue
        ev=np.linalg.eigvals(J); maxre=float(np.max(ev.real)); stable=maxre<0
        pts.append({'candidate_id':r['candidate_id'],'family_blind':r['family_blind'],'q':r['q'],'h':r['h'],'p':r['p'],'field_norm':fn,'projection_fraction':r['projection_fraction'],'jacobian_max_real_eigenvalue':maxre,'jacobian_eigenvalues':';'.join(f'{z.real:.9g}{z.imag:+.9g}j' for z in ev),'stable_linear':stable,'fixed_point_candidate':bool(stable and fn<=norm_max and r['projection_fraction']>=min_proj)})
    if pts:
        fields=list(pts[0].keys());
        with (out/'blind_fixed_point_candidates.csv').open('w',newline='',encoding='utf-8') as f: wr=csv.DictWriter(f,fieldnames=fields); wr.writeheader(); wr.writerows(pts)
    else: (out/'blind_fixed_point_candidates.csv').write_text('candidate_id,family_blind,q,h,p,field_norm,projection_fraction,jacobian_max_real_eigenvalue,jacobian_eigenvalues,stable_linear,fixed_point_candidate\n',encoding='utf-8')
    # Local affine fixed-point solve: F(xi*) ~= 0 inside a complete central stencil.
    affine=[]
    for i,r in enumerate(rr):
        F0=np.array([r[f'F_{a}'] for a in AXES],float)
        if not np.isfinite(F0).all(): continue
        J=local_jacobian(rr,i)
        if J is None or abs(np.linalg.det(J))<1e-12: continue
        ev=np.linalg.eigvals(J); stable=bool(np.max(ev.real)<0)
        delta=-np.linalg.solve(J,F0); xi0=np.array([r[a] for a in AXES],float); star=xi0+delta
        inside=True
        for j,a in enumerate(AXES):
            cand=[z for z in rr if _same_slice(r,z,a) and z is not r]
            lo=[z[a] for z in cand if z[a]<r[a]]; hi=[z[a] for z in cand if z[a]>r[a]]
            if not lo or not hi: inside=False; break
            L=max(lo); H=min(hi); inside &= (star[j]>=L-1e-12 and star[j]<=H+1e-12)
        if not inside: continue
        short_diag=[]
        for j,a in enumerate(AXES):
            cand=[z for z in rr if _same_slice(r,z,a) and z is not r]; lo=[z for z in cand if z[a]<r[a]]; hi=[z for z in cand if z[a]>r[a]]
            A=max(lo,key=lambda z:z[a]); B=min(hi,key=lambda z:z[a]); short_diag.append((B[f'Fshort_{a}']-A[f'Fshort_{a}'])/(B[a]-A[a]))
        short_restoring=bool(all(np.isfinite(short_diag)) and all(v<0 for v in short_diag))
        affine.append({'family_blind':r['family_blind'],'replicate':r.get('replicate','0'),'anchor_candidate_id':r['candidate_id'],'q_star':float(star[0]),'h_star':float(star[1]),'p_star':float(star[2]),'anchor_field_norm':float(np.linalg.norm(F0)),'jacobian_max_real_eigenvalue':float(np.max(ev.real)),'jacobian_eigenvalues':';'.join(f'{z.real:.9g}{z.imag:+.9g}j' for z in ev),'stable_linear':stable,'short_diagonal_restoring':short_restoring,'confirmed_affine_fixed_point':bool(stable and short_restoring)})
    afields=['family_blind','replicate','anchor_candidate_id','q_star','h_star','p_star','anchor_field_norm','jacobian_max_real_eigenvalue','jacobian_eigenvalues','stable_linear','short_diagonal_restoring','confirmed_affine_fixed_point']
    with (out/'blind_affine_fixed_point_candidates.csv').open('w',newline='',encoding='utf-8') as f:
        wr=csv.DictWriter(f,fieldnames=afields); wr.writeheader(); wr.writerows(affine)
    nrest=sum(c['restoring'] and c['short_restoring'] for c in crosses); nfp=sum(p['fixed_point_candidate'] for p in pts); naff=sum(a['confirmed_affine_fixed_point'] for a in affine)
    verdict='PASS_CANDIDATE_RESTORING_STRUCTURE' if (nrest>=int(cfg.get('min_confirmed_restoring_crossings',1)) or nfp>0 or naff>0) else ('FAIL_NO_RESTORING_STRUCTURE' if crosses or pts else 'INDETERMINATE_INSUFFICIENT_GRID')
    summary={'format':'SST-QHP-ANALYZE-1','verdict':verdict,'n_zero_crossings':len(crosses),'n_confirmed_restoring_crossings':nrest,'n_fixed_point_candidates':nfp,'n_confirmed_affine_fixed_points':naff,'caution':'PASS means a numerical restoring candidate on the sampled QHP manifold, not proof of physical knot stability or SST ontology.'}
    (out/'blind_analysis_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8'); return summary
