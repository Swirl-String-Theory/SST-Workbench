"""A075-v0.2.11: fully assembled finite-N normal Jacobian, no false stability gates.

A007 and A075-v0.2.9 are pinned read-only by prior-version source verifier.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,sys,zipfile,datetime
from pathlib import Path
import numpy as np
from .runner import verify,load_a007_at_uniform_theta
from .high_order import fit,residual,make_shape,refine_check,field
from .full_spectrum import jacobian,evaluate_spectrum,compare_matrices,match_eigenvalues
from .core import B_REFERENCE,DELTA,LAMBDA,GAMMA,LOCAL_COEFFICIENT

ROOT=Path(__file__).resolve().parents[1]
VERSION='v0.2.11'
PREFIX='A075_Hydrodynamische_Resonante_Invanging'


def save_json(p,data):
    p.write_text(json.dumps(data,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf8')

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def png_plot(rows,out):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:return False
    fig,ax=plt.subplots(figsize=(6.6,3.6))
    ax.plot([a['N'] for a in rows],[a['epsilon'] for a in rows],marker='o')
    ax.set_xlabel('Filamentpunten N');ax.set_ylabel('Dimensieloos evenwichtsresidu')
    ax.set_title('Ruban T(2,3) - vervormde seed, geen certificatie')
    ax.grid(alpha=.25);fig.tight_layout();fig.savefig(out,dpi=150);plt.close(fig)
    return True

def pdf_report(out,config,rows,assess):
    try:
        from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,KeepTogether
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
    except ImportError:return False
    styles=getSampleStyleSheet();story=[]
    def paragraph(value,style='BodyText'):
        story.append(Paragraph(value,styles[style]));story.append(Spacer(1,7))
    paragraph('A075 v0.2.11 - Ruban Equilibrium &amp; Discrete Linear Spectrum','Title')
    paragraph('Research-only add-on | No Framework gate promotion | 29 October 2026')
    paragraph('Scientific question','Heading2')
    paragraph('Can the A007 paper-parameter trefoil be relaxed to a converged moving relative equilibrium? Can its full finite-dimensional normal Jacobian be formed and its eigenvalues checked for finite-difference sensitivity?')
    paragraph('Model and provenance','Heading2')
    paragraph('A007 T(2,3), B0=77/500; R0=1; Gamma=2 pi; delta=0.05; Lambda=1.4 + log(200)/2. The pinned A075 v0.2.9 midpoint code is retained as evidence and not mutated. This new operator uses two distinct quadratures and Fourier derivatives. Units are nondimensional.')
    paragraph('Methods','Heading2')
    paragraph('Least-squares radial/vertical harmonics (multiples of q=3) reduce the normal velocity after fitting axial translation and rotation. For each N we report both the optimized residual and cross-evaluation at higher N. The 2N-by-2N centered finite-difference normal Jacobian holds axial speeds and tangential gauge frozen at the base state and is computed at both h and h/2. All 2N discrete eigenvalues are written to JSON.')
    paragraph('Results','Heading2')
    table=[['N','Basis H','epsilon','eps cross-grid','quadrature difference','Eigenvalues']]
    for r in rows:
        table.append([str(r['N']),str(r['harmonics']),f"{r['epsilon']:.7g}",f"{r['cross_grid_epsilon']:.7g}",f"{r['cross_scheme_absolute_epsilon']:.3g}",str(r.get('n_eigenvalues') or '-')])
    tb=Table(table,repeatRows=1,colWidths=[34,44,70,98,130,58]);tb.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DFE8EF')),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#C4CED7')),('FONTSIZE',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),5)]));story.append(tb)
    story.append(Spacer(1,14))
    paragraph('Gate assessment','Heading2')
    for k in ('geometric_source_verified','finite_N_matrix_complete','relative_equilibrium','continuum_spectral_convergence','physical_stability'):
        paragraph(f'{k}: {assess[k]}')
    paragraph('Scientific limits','Heading2')
    paragraph('A finite-N complete matrix is not the continuum linear operator. Any spectral interpretation is blocked until the base-state relative equilibrium, core resolution, quadrature agreement and spatial spectral convergence close. A self-consistent finite-N spectrum at a nonstationary seed cannot establish physical stability. No 3D Euler, finite-core material or topological certification has run.')
    paragraph('Source','Heading2')
    paragraph('V. P. Ruban, Long-lived quantum vortex knots, JETP Letters 107 (2018), DOI 10.1134/S0021364018050120. A007 analytic reconstruction and A075 v0.2.9 source hashes in RUN_CONFIG.json.')
    SimpleDocTemplate(str(out/'A075-v0.2.11_FALSIFIER_REPORT.pdf'),pagesize=(595,842),leftMargin=36,rightMargin=36,topMargin=36,bottomMargin=36).build(story)
    return True

def do_run(args):
    provenance=verify()
    levels=[int(z) for z in args.n_levels.split(',')]
    if levels!=sorted(set(levels)) or len(levels)>4 or len(levels)<1 or any(n<32 or n%2 for n in levels):
        raise ValueError('1..4 unique increasing even Ns >= 32 required')
    if len(levels)>2 and not args.allow_expensive:raise ValueError('More than two levels requires --allow-expensive')
    if max(levels)>128 and not args.allow_expensive:raise ValueError('N>128 requires --allow-expensive')
    if args.command in ('SPECTRUM','QUALIFY') and max(levels)>256:
        raise ValueError('Dense full spectrum limited to N<=256; use EQUILIBRIUM at higher N')
    if args.harmonics<0 or args.harmonics>10 or args.max_nfev<1:raise ValueError('Invalid fit limits')
    if args.fd_step<=0 or args.fd_step>=1e-2:raise ValueError('Invalid FD step')
    b=args.b0
    if not .02<=b<=.32:raise ValueError('B0 out of allowed range')
    run_id=args.run_id or f'{args.command}_{datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")}'
    if not run_id or not all(s.isalnum() or s in '_-' for s in run_id):raise ValueError('Unsafe run id')
    base=ROOT/f'{PREFIX}_{VERSION}-outputs';out=base/run_id
    if out.exists() or (ROOT.parent/f'{PREFIX}_{VERSION}_{run_id}_outputs.zip').exists():
        raise FileExistsError('Output already exists: REFUSE overwrite')
    out.mkdir(parents=True,exist_ok=False)
    cfg={'version':VERSION,'run_id':run_id,'kind':args.command,'N_levels':levels,'B0':b,
         'B0_original_exact':'77/500','harmonics':args.harmonics,'max_nfev':args.max_nfev,
         'delta':DELTA,'Gamma':GAMMA,'Lambda':LAMBDA,'local_induction_coefficient':LOCAL_COEFFICIENT,
         'fd_step':args.fd_step,'source_verification':provenance,
         'operator':'independent periodic trapezoid or midpoint plus spectral curvature',
         'framework_invoked':False,'A075_v029_modified':False,'original_author_perturbation_known':False,
         'input_at_B0_0p154':'A007 hash-verified original XYZ reconstructed on periodic theta mesh',
         'scientific_status':'DEVELOPMENT_ONLY'}
    save_json(out/'RUN_CONFIG.json',cfg)
    results=[];prev_eigs=None
    for n in levels:
        print(f'Fitting B0={b:.6f} N={n} H={args.harmonics} ...',flush=True)
        # Exact A007 seed is verified even when analytic torus sampling is used by constrained fit.
        # Record interpolation mismatch to source on uniform-theta mesh before performing fit.
        source=load_a007_at_uniform_theta(n) if abs(b-B_REFERENCE)<1e-12 else None
        analytic=make_shape(b,n,[])
        input_difference=float(np.max(np.abs(source-analytic))) if source is not None else None
        ff=fit(b,n,args.harmonics,scheme='trapezoid',max_nfev=args.max_nfev,reference_points=source)
        x=ff['x'];rt=ff['final'];cross=refine_check(b,ff['coeff'],2*n,'trapezoid',reference_points=(load_a007_at_uniform_theta(2*n) if source is not None else None))
        mid=residual(x,'midpoint')
        edges=np.linalg.norm(np.roll(x,-1,axis=0)-x,axis=1)
        np.savez_compressed(out/f'T23_B{b:.6f}_N{n}_relaxed.npz',points=x,coefficients=ff['coeff'])
        item={'N':n,'harmonics':args.harmonics,'B0':b,'epsilon_initial':ff['initial']['epsilon'],
              'epsilon':rt['epsilon'],'cross_grid_epsilon':cross['epsilon'],
              'cross_grid_relative_change':abs(cross['epsilon']-rt['epsilon'])/max(rt['epsilon'],1e-16),
              'cross_scheme_absolute_epsilon':abs(rt['epsilon']-mid['epsilon']),
              'midpoint_epsilon':mid['epsilon'],'U':rt['U'],'Omega':rt['Omega'],
              'max_segment_over_delta':float(edges.max()/DELTA),
              'optimizer_success':ff['optimizer_success'],'nfev':ff['nfev'],
              'optimizer_message':ff['optimizer_message'],
              'coefficients':ff['coeff'].tolist(),'a007_resampled_minus_analytic_max':input_difference,
              'n_eigenvalues':None}
        if args.command in ('SPECTRUM','QUALIFY'):
            print(f' Assembling complete finite-N normal Jacobian: {2*n} x {2*n} ...',flush=True)
            J,meta=jacobian(x,step=args.fd_step)
            J2,_=jacobian(x,step=args.fd_step/2)
            relative=compare_matrices(J,J2)
            ev=evaluate_spectrum(J)
            eig=np.array([complex(*z) for z in ev['eigenvalues']])
            matinfo={**meta,'FD_step':args.fd_step,'FD_step_relative_matrix_change':relative,
                     'spectrum':ev,'equilibrium_criterion_required':'epsilon<=1e-5 and cross-grid/core convergence',
                     'low_mode_comparison_to_previous_N':None if prev_eigs is None else match_eigenvalues(prev_eigs,eig),
                     'scientific_status':'FINITE_N_JACOBIAN_ASSEMBLED_NOT_CONTINUUM_SPECTRAL_CERTIFICATION'}
            save_json(out/f'FULL_DISCRETE_SPECTRUM_N{n}.json',matinfo)
            np.savez_compressed(out/f'FULL_DISCRETE_JACOBIAN_N{n}.npz',jacobian=J,fd_step=args.fd_step)
            item['n_eigenvalues']=ev['n_eigenvalues'];item['matrix_fd_step_relative_error']=relative
            item['max_real_eigenvalue']=ev['max_real']
            prev_eigs=eig
        results.append(item)
        print(f' N={n}: eps {ff["initial"]["epsilon"]:.8g} -> {rt["epsilon"]:.8g}; crossgrid={cross["epsilon"]:.8g}; segment/delta={item["max_segment_over_delta"]:.3f}',flush=True)
    with (out/'EQUILIBRIUM_CONVERGENCE.csv').open('w',newline='',encoding='utf8') as f:
        keys=['N','harmonics','B0','epsilon_initial','epsilon','cross_grid_epsilon','cross_grid_relative_change','midpoint_epsilon','cross_scheme_absolute_epsilon','max_segment_over_delta','optimizer_success','nfev','U','Omega','n_eigenvalues','max_real_eigenvalue','matrix_fd_step_relative_error']
        writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader();writer.writerows([{k:x.get(k) for k in keys} for x in results])
    # strict gates, do NOT assert true convergence from 2 levels or finite N
    strict_resid=all(z['epsilon']<=1e-5 for z in results)
    spatial= len(levels)>=3 and all(z['cross_grid_relative_change']<1e-3 for z in results) and all(z['max_segment_over_delta']<.25 for z in results)
    independent=all(z['cross_scheme_absolute_epsilon']<1e-5 for z in results)
    # exact equilibrium cannot be certified by finite residual, even when thresholds pass
    assess={'geometric_source_verified':True,'finite_N_matrix_complete':all(z['n_eigenvalues']==2*z['N'] for z in results) if args.command in ('SPECTRUM','QUALIFY') else False,
            'relative_equilibrium':'UNRESOLVED', 'continuum_spectral_convergence':'UNRESOLVED',
            'physical_stability':'UNRESOLVED','full_continuum_spectrum_computed':False,
            'all_residual_below_candidate_tolerance':strict_resid,'spatial_resolution_screen':spatial,
            'quadrature_agreement_screen':independent,'physical_equilibrium_proven':False,
            'source_and_seed_verified':True,'A075_framework_v1_1_0_gates_invoked':False,
            'euler_finite_core_qualified':False,'notes':('A finite-N normal matrix is numerically complete but cannot be interpreted as the true linear stability spectrum until a relative equilibrium, geometric gauge, finite-core resolution and low-mode spectral convergence have passed.')}
    save_json(out/'SCIENTIFIC_ASSESSMENT.json',assess)
    save_json(out/'FULL_RESULTS.json',{'rows':results})
    report=['# A075-v0.2.11 - Relative equilibrium and discrete spectrum','','**Status: DEVELOPMENT_ONLY / PHYSICAL_STABILITY_UNRESOLVED.**','',
           'The A007 source and original A075-v0.2.9 Eq.9 solver are SHA256-pinned and are not modified.',
           '', 'Hypothesis: a nontrivially deformed T(2,3) at B0=77/500 may be a relative equilibrium whose perturbation spectrum has narrow neutral/stable windows.',
           '', 'Method: independent periodic quadrature plus spectral curvature; constrained cylindrical Fourier shape correction; full 2N-by-2N normal Jacobian (two normal directions per collocation point).',
           '', '| N | epsilon | N->2N epsilon | |trapezoid-midpoint| | Max segment/delta | Eigenvalue count |',
           '|---:|---:|---:|---:|---:|---:|']
    for z in results:report.append(f'| {z["N"]} | {z["epsilon"]:.8g} | {z["cross_grid_epsilon"]:.8g} | {z["cross_scheme_absolute_epsilon"]:.3g} | {z["max_segment_over_delta"]:.2f} | {z["n_eigenvalues"] or "not run"} |')
    report+=['','## Scientific boundary','','2N finite-grid eigenvalues are not the continuum spectrum, and a matrix linearized around a non-equilibrium shape is not a physical stability operator. No stability status is promoted. The Ruban perturbation is unreported. A075 Framework and 3D Euler gates are not run.',
              '', '## Minimal follow-up','','Continue with core resolution (>4 points per delta), independent quadrature, N/time refinement, symmetry/gauge checks and continuation of a genuinely converged shape. Only then interpret the eigenvalues.',
              '', '## Source','','V. P. Ruban, *Long-lived quantum vortex knots*, JETP Letters 107 (2018), DOI 10.1134/S0021364018050120.']
    (out/'FALSIFIER_REPORT.md').write_text('\n'.join(report)+'\n',encoding='utf8')
    pdf_report(out,cfg,results,assess)
    png_plot(results,out/'RESIDUAL_CONVERGENCE.png')
    hashes={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
    save_json(out/'MANIFEST_SHA256.json',{'files':hashes})
    target=ROOT.parent/f'{PREFIX}_{VERSION}_{run_id}_outputs.zip'
    with zipfile.ZipFile(target,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(out.rglob('*')):
            if p.is_file():z.write(p,arcname=f'{run_id}/{p.relative_to(out)}')
    target.with_suffix('.zip.sha256').write_text(f'{sha(target)}  {target.name}\n',encoding='ascii')
    print('ARCHIVE',target,'\nASSESSMENT',json.dumps(assess,indent=2));return 0

def main():
    pa=argparse.ArgumentParser(description=__doc__)
    pa.add_argument('command',choices=['VERIFY','EQUILIBRIUM','SPECTRUM','QUALIFY'])
    pa.add_argument('--n-levels',default='48,64')
    pa.add_argument('--b0',type=float,default=B_REFERENCE)
    pa.add_argument('--harmonics',type=int,default=2)
    pa.add_argument('--max-nfev',type=int,default=40)
    pa.add_argument('--fd-step',type=float,default=2e-5)
    pa.add_argument('--run-id',default='')
    pa.add_argument('--allow-expensive',action='store_true')
    a=pa.parse_args()
    if a.command=='VERIFY':print(json.dumps(verify(),indent=2));return 0
    return do_run(a)

if __name__=='__main__':sys.exit(main())
