"""A075 v0.2.12: free gauge-fixed Newton--Krylov relative-equilibrium research run.

Self-contained, additive research extension. Does not execute or modify A075
Framework v1.1.0 scientific gates or original A075-v0.2.9 source.
"""
from __future__ import annotations
import argparse, csv, datetime, hashlib, json, math, os, sys, zipfile
from pathlib import Path
import numpy as np
from .runner import verify, load_a007_at_uniform_theta
from .core import B_REFERENCE, GAMMA, DELTA, LAMBDA, LOCAL_COEFFICIENT
from .free_gauge_nk import GaugeSlice, axial_spin, eval_system, solve, prolongate, geometric_quality, fit_speeds
from .high_order import field as reference_field

ROOT=Path(__file__).resolve().parents[1]
VERSION='v0.2.12'
PREFIX='A075_Hydrodynamische_Resonante_Invanging'

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def dump(path, obj):Path(path).write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')

def get_velocity(backend):
    if backend not in ('auto','numba','numpy'):raise ValueError('Unknown backend')
    if backend!='numpy':
        try:
            from .fast_field import field as fast, _sum
            if _sum is not None:return fast,'NUMBA_ACCELERATED_INDEPENDENTLY_CHECKED'
        except ImportError:pass
        if backend=='numba':raise RuntimeError('Numba explicitly requested but not available')
    return reference_field,'NUMPY_REFERENCE'

def interpolation_diagnostic(gauge,y,n_new,vf):
    """Evaluate SAME physical shape at the next mesh; do NOT reoptimise."""
    ref=load_a007_at_uniform_theta(n_new)
    g2, y2=prolongate(gauge,y,ref)
    fn,meta=eval_system(g2,y2,velocity_function=vf)
    return {'N':n_new,'epsilon':meta['epsilon'],'gauge_norm':meta['gauge_norm'],
            'max_segment_over_delta':meta['geometry']['max_segment_over_delta'],
            'y_prolongated':y2,'gauge_new':g2}

def write_pdf(out,rows,assessment):
    try:
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
    except ImportError:return False
    s=getSampleStyleSheet(); story=[]
    def put(t,style='BodyText'):
        story.append(Paragraph(t,s[style]));story.append(Spacer(1,9))
    put('A075 v0.2.12 | Free Gauge-Fixed Newton-Krylov','Title')
    put('Research addon | Absolute source provenance | 30 October 2026')
    put('Scientific question','Heading2')
    put('Can the A007 Ruban T(2,3) seed at B0=77/500 be deformed in all nodal normal degrees of freedom to a relative equilibrium of the regularized filament equation, after explicit removal of parameter and axial group gauges?')
    put('Model and method','Heading2')
    put('R0=1; Gamma=2 pi; delta=0.05; Lambda=7/5+ln(200)/2; local coefficient (7/5-ln(2)/2)/2. The new source-free model has 2N shape coordinates, unknown axial translation U and rotation Omega, two independent group-phase conditions, and no Fourier shape restriction. Jacobian-vector actions use finite differences; GMRES gives inexact Newton directions with backtracking. Numerical quadrature is the previously specified periodic trapezoid scheme, checked against midpoint on identical shapes.')
    put('Numerical run results','Heading2')
    tab=[['N','Initial epsilon','Final epsilon','2N fixed-shape epsilon','midpoint epsilon']]
    for r in rows:
        tab.append([str(r['N']),f"{r['epsilon_initial']:.5g}",f"{r['epsilon_final']:.5g}",f"{r['fixed_shape_epsilon_2N']:.5g}",f"{r['midpoint_epsilon']:.5g}"])
    t=Table(tab,repeatRows=1,colWidths=[42,99,99,114,114]);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DDE8F0')),('GRID',(0,0),(-1,-1),.35,colors.HexColor('#B8C6CF')),('FONTSIZE',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),7)]));story.append(t);story.append(Spacer(1,14))
    put('Independent gates','Heading2')
    for k,v in assessment.items():
        if k in ('source_verified','finite_N_candidate_found','continuum_equilibrium','linear_stability','physical_stability','core_resolution_screen','quadrature_agreement_screen','topological_certification'):
            put(f'{k}: {v}')
    put('Critical interpretation','Heading2')
    put('A very small finite-N residual is neither a mathematical proof of an exact continuous equilibrium nor an eigenvalue stability certificate. A Newton solver can produce a numerical solution at one mesh while quadrature, core-length and interpolation errors remain. The spectra from v0.2.11 do not certify a stationary base state. No new complete gauge-correct stability spectrum is claimed. No three-dimensional incompressible Euler experiment or original author perturbation has been reproduced.')
    put('References','Heading2')
    put('V. P. Ruban (2018), Long-lived quantum vortex knots, JETP Letters 107, 307-311, DOI 10.1134/S0021364018050120. A007 exact analytic seed and immutable A075-v0.2.9 Eq.(9) solver are SHA-256 verified.')
    SimpleDocTemplate(str(out/'A075-v0.2.12_FALSIFIER_REPORT.pdf'),pagesize=(595,842),leftMargin=38,rightMargin=38,topMargin=36,bottomMargin=36).build(story)
    return True

def run(args):
    original=verify()
    levels=[int(s) for s in args.n_levels.split(',')]
    if len(levels)>5 or len(levels)<1 or sorted(set(levels))!=levels or any(n%2 or n<32 for n in levels):
        raise ValueError('Unique increasing even levels >= 32, up to 5')
    if args.n_levels and max(levels)>256 and not args.allow_expensive:
        raise ValueError('N>256 requires --allow-expensive')
    if max(levels)>2048:raise ValueError('N>2048 not supported without separate resource study')
    if args.max_newton<1 or args.max_newton>60:raise ValueError('max-newton 1..60')
    if args.fd_step<=0 or args.fd_step>=1e-2:raise ValueError('Invalid finite-difference step')
    rid=args.run_id or ('GAUGE_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    if not rid or any(not(c.isalnum() or c in '-_') for c in rid):raise ValueError('Unsafe run-id')
    base=ROOT/f'{PREFIX}_{VERSION}-outputs';out=base/rid
    archive=ROOT.parent/f'{PREFIX}_{VERSION}_{rid}_outputs.zip'
    if out.exists() or archive.exists() or archive.with_suffix('.zip.sha256').exists():
        raise FileExistsError('Fail closed: run-id already exists; no overwrites')
    vf, backend=get_velocity(args.backend)
    # Verify optional fast field against the independent, unaccelerated implementation
    ref=load_a007_at_uniform_theta(96)
    parity=float(np.max(np.abs(vf(ref)-reference_field(ref))))
    if parity>5e-12:raise RuntimeError(f'Quadrature acceleration parity error {parity}')
    out.mkdir(parents=True)
    cfg={'version':VERSION,'run_id':rid,'N_levels':levels,'model':'Ruban_2018_regularized_finite_filament',
         'R0':1.0,'Gamma':GAMMA,'delta':DELTA,'Lambda':LAMBDA,'local_coefficient':LOCAL_COEFFICIENT,
         'B0_exact':'77/500','B0':B_REFERENCE,'solver':'free_nodal_normal_graph_gauge_fixed_Newton_Krylov',
         'normal_nodal_dof': '2*N','additional_unknowns':['U','Omega'],
         'gauge_conditions':['axial_translation_phase','axial_rotation_phase'],
         'tangent_reparameterization':'normal_graph_plus_current_tangent_projection',
         'solver_backend':backend,'numerical_field_parity_max_abs':parity,
         'max_newton':args.max_newton,'krylov_restart':args.restart,'krylov_cycles':args.cycles,
         'krylov_rtol':args.krylov_rtol,'fd_step':args.fd_step,'objective_tolerance':args.tolerance,
         'source_verification':original,'existing_A075_Framework_gates_invoked':False,
         'parent_original_files_mutated':False,'paper_author_perturbation_available':False,
         'scientific_classification':'RESEARCH_NUMERICAL_DISCRETE_ONLY'}
    dump(out/'RUN_CONFIG.json',cfg)
    results=[]; previous=None
    for n in levels:
        xref=load_a007_at_uniform_theta(n)
        warm=None
        if previous is not None:
            _,warm=prolongate(previous['gauge'],previous['y'],xref)
        gv=GaugeSlice.from_reference(xref)
        f0,m0=eval_system(gv, gv.y0(*fit_speeds(gv,xref)) if warm is None else warm, velocity_function=vf)
        print(f'Newton--Krylov n={n}: starting epsilon {m0["epsilon"]:.8g}',flush=True)
        rr=solve(xref,initial=warm,max_newton=args.max_newton,gmres_restart=args.restart,
                 gmres_cycles=args.cycles,krylov_rtol=args.krylov_rtol,fd_step=args.fd_step,
                 objective_tolerance=args.tolerance,velocity_function=vf,verbose=args.verbose)
        x=rr['x'];summ=rr['summary']
        mid=lambda z:reference_field(z,scheme='midpoint')
        _,mid_status=eval_system(rr['gauge'],rr['y'],velocity_function=mid)
        cross=interpolation_diagnostic(rr['gauge'],rr['y'],2*n,vf)
        midpoint_fast=lambda a:vf(a,scheme='midpoint')
        _,mid_cross=eval_system(cross['gauge_new'],cross['y_prolongated'],velocity_function=midpoint_fast)
        # independent quadrature at exact same shape/weights: not an optimized midpoint root
        basefields=reference_field(x),vf(x)
        parity_same=float(np.max(np.abs(basefields[0]-basefields[1])))
        if parity_same>2e-11:raise RuntimeError('Fast/reference field mismatch at deformed geometry')
        row={'N':n,'epsilon_initial':m0['epsilon'],'epsilon_final':summ['epsilon'],
             'fixed_shape_epsilon_2N':cross['epsilon'],
             'midpoint_epsilon':mid_status['epsilon'],
             'midpoint_epsilon_2N':mid_cross['epsilon'],
             'quadrature_epsilon_difference':abs(summ['epsilon']-mid_status['epsilon']),
             'U':summ['U'],'Omega':summ['Omega'],
             'iteration_count':len(rr['history'])-1,'newton_stop':rr['status'],
             'final_merit':rr['final_merit'],'gauge_norm':summ['gauge_norm'],
             'max_segment_over_delta':summ['geometry']['max_segment_over_delta'],
             'max_displacement':float(np.max(np.linalg.norm(x-xref,axis=1))),
             'max_ref_fast_velocity_diff':parity_same}
        np.savez_compressed(out/f'RE_N{n}_GAUGE_FIXED.npz',points=x,
                            source_reference_points=xref,normal_displacements=rr['y'][:-2].reshape(n,2),
                            axial_velocity=np.array([summ['U'],summ['Omega']]))
        dump(out/f'NEWTON_HISTORY_N{n}.json',rr['history'])
        results.append(row)
        print(f' N={n} after={summ["epsilon"]:.9g}, frozen-shape 2N={cross["epsilon"]:.9g},'
              f' midpoint={mid_status["epsilon"]:.9g}, midpoint2N={mid_cross["epsilon"]:.9g}, seg/delta={row["max_segment_over_delta"]:.4f}; {rr["status"]}',flush=True)
        previous=rr
    with (out/'EQUILIBRIUM_CONVERGENCE.csv').open('w',newline='',encoding='utf8') as f:
        keys=list(results[0].keys());w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(results)
    # Research diagnostics only; never convert a finite-N solver tolerance to proof.
    core=bool(len(levels)>=3 and all(z['max_segment_over_delta']<.25 for z in results[-2:]))
    quad=bool(len(levels)>=3 and all(z['midpoint_epsilon']<args.tolerance for z in results[-2:]))
    assessment={'source_verified':True,'finite_N_candidate_found':any(z['epsilon_final']<args.tolerance for z in results),
                'continuum_equilibrium':'UNRESOLVED','linear_stability':'NOT_RUN',
                'physical_stability':'UNRESOLVED','core_resolution_screen':core,
                'quadrature_agreement_screen':quad,'topological_certification':'NOT_RUN',
                'spatial_convergence_proven':False,'exact_continuum_equilibrium_proven':False,
                'full_gauge_correct_spectrum_computed':False,'framework_v1_1_0_scientific_gates_invoked':False,
                'numerical_source_parity_pass':True,'qualified_stable_B0_interval':'NONE_ESTABLISHED',
                'residual_small_not_equilibrium_proof':True,
                'scientific_note':'Finite-N Newton residual measures consistency of discretized Eq.9 only. Independent quadrature/core convergence and exact stationary shape remain unresolved.'}
    dump(out/'SCIENTIFIC_ASSESSMENT.json',assessment)
    report=['# A075-v0.2.12 — Gauge-fixed free normal-graph Newton–Krylov','',
            '**Research status: `DEVELOPMENT_ONLY`; `CONTINUUM_EQUILIBRIUM_UNRESOLVED`; `LINEAR_STABILITY_NOT_RUN`.**','',
            '## Scientific question','',
            'Does the A007 T(2,3) with B0=77/500 admit a nearby, freely deformed, moving relative equilibrium of the regularized Ruban filament equation?',
            '', '## Method','',
            '2N independent normal graph coordinates; two unknown axial speeds U/Omega; two phase-gauge constraints; instantaneous tangential component removed. No finite Fourier family constraint. GMRES finite-difference Jacobian-vector products with Newton backtracking. Compare unmodified shape on 2N points and trapezoid versus midpoint quadrature.',
            '', '| N | initial epsilon | solved epsilon | unchanged shape 2N epsilon | midpoint epsilon | midpoint 2N epsilon | segment/delta | status |',
            '|---:|---:|---:|---:|---:|---:|---:|---|']
    for z in results:
        report.append(f'| {z["N"]} | {z["epsilon_initial"]:.8g} | {z["epsilon_final"]:.8g} | {z["fixed_shape_epsilon_2N"]:.8g} | {z["midpoint_epsilon"]:.8g} | {z["midpoint_epsilon_2N"]:.8g} | {z["max_segment_over_delta"]:.4f} | {z["newton_stop"]} |')
    report+=['','## Scientific boundaries','',
             'Numerical near-zero finite-N residual is NOT proof of an exact continuous equilibrium. A finite-N root is not a spectral stability result; compare independently discretized operators and run at least three well resolved core levels. Midpoint and trapezoid are different finite-N schemes; cross-scheme mismatch is expected when core underresolved.',
             'No Ruban-author random perturbation, physical lifetime, reconnection, or 3D Euler check reproduced. A007 source is hash verified, not author simulation vertices. Source A075-v0.2.9 and prior source releases remain immutable.',
             '', '## Sources','','Ruban, *Long-lived quantum vortex knots* (2018), DOI 10.1134/S0021364018050120. A007 primary SHA-256: '+original['A007_primary_sha256']+'.',
             'A075-v0.2.9 Eq9 SHA-256: '+original['A075_parent_solver_sha256']+'.']
    (out/'FALSIFIER_REPORT.md').write_text('\n'.join(report)+'\n',encoding='utf8')
    write_pdf(out,results,assessment)
    hashes={str(p.relative_to(out)):digest(p) for p in sorted(out.rglob('*')) if p.is_file()}
    dump(out/'MANIFEST_SHA256.json',{'algorithm':'SHA-256','files':hashes})
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(out.rglob('*')):
            if p.is_file():z.write(p,arcname=f'{rid}/{p.relative_to(out)}')
    archive.with_suffix('.zip.sha256').write_text(f'{digest(archive)}  {archive.name}\n',encoding='ascii')
    print(f'ARCHIVE {archive}');print('STATUS CONTINUUM_EQUILIBRIUM_UNRESOLVED');return 0


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['VERIFY','GAUGE_NEWTON','CONTINUE'])
    p.add_argument('--n-levels',default='64,128')
    p.add_argument('--max-newton',type=int,default=12)
    p.add_argument('--restart',type=int,default=40)
    p.add_argument('--cycles',type=int,default=3)
    p.add_argument('--krylov-rtol',type=float,default=.015)
    p.add_argument('--fd-step',type=float,default=2e-6)
    p.add_argument('--tolerance',type=float,default=1e-8)
    p.add_argument('--backend',choices=['auto','numba','numpy'],default='auto')
    p.add_argument('--run-id',default='')
    p.add_argument('--allow-expensive',action='store_true')
    p.add_argument('--verbose',action='store_true')
    args=p.parse_args()
    if args.command=='VERIFY':print(json.dumps(verify(),indent=2));return 0
    return run(args)

if __name__=='__main__':sys.exit(main())
