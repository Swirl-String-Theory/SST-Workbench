"""Command line: verify immutable A007/A075 sources; evaluate Ruban T(2,3).

Creates only new files and run ids. Does not invoke or alter Framework v1.1.0.
"""
from __future__ import annotations
import argparse,csv,datetime,hashlib,json,math,os,sys,zipfile
from pathlib import Path
import numpy as np
from .core import (B_REFERENCE,DELTA,GAMMA,LAMBDA,LOCAL_COEFFICIENT,
                   torus,field,fitted_residual,relax,numerical_spectral_proxy)
ROOT=Path(__file__).resolve().parents[1]
PRIMARY='RUBAN_T23_B0_0p154_N2048_EQUAL_ARCLENGTH.xyz'
SOURCE_HASH='27cad14f87262d496b1f3b3cb0d13b63fff0163e8face210d3463f053f860411'
SEED_HASH='127de915c8eaae59325b8bd2697a0ab50c71eb1c5cf0a91fc55ed44de70fcc89'
OUTPUT_PREFIX='A075_Hydrodynamische_Resonante_Invanging'
VERSION='v0.2.10'

def sha256(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(obj,p):p.write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')

def verify():
    p=ROOT/'inputs/a007'/PRIMARY
    source=ROOT/'source_evidence/A075_v029_ruban_filament.py'
    if sha256(p)!=SEED_HASH:raise RuntimeError('A007 exact seed SHA256 mismatches; stop')
    if sha256(source)!=SOURCE_HASH:raise RuntimeError('A075 original Eq9 source SHA256 mismatches; stop')
    pts=np.loadtxt(p,comments='#',usecols=(0,1,2))
    if pts.shape!=(2048,3) or not np.isfinite(pts).all():raise RuntimeError('A007 geometry invalid')
    R=np.linalg.norm(pts[:,:2],axis=1)
    resid=np.hypot(R-1,pts[:,2])-B_REFERENCE
    if np.max(np.abs(resid))>1e-12:raise RuntimeError('A007 torus radius check failed')
    config=json.loads((ROOT/'inputs/a007/RUBAN_FILAMENT_CONFIG.json').read_text())
    if config['formulae_exact']['B0']!='77/500' or abs(config['delta_regulator']-DELTA)>1e-14:
        raise RuntimeError('A007 model config mismatches')
    manifest=json.loads((ROOT/'inputs/a007/SEED_MANIFEST.json').read_text())
    entry=next(q for q in manifest['files'] if q['filename']==PRIMARY)
    if entry['sha256']!=SEED_HASH:raise RuntimeError('A007 manifest source mismatches')
    parent=json.loads((ROOT/'source_evidence/SOURCE_MANIFEST_v0.2.9.json').read_text())
    entry=next(q for q in parent['files'] if q['path']=='experiment/ruban_filament.py')
    if entry['sha256']!=SOURCE_HASH:raise RuntimeError('A075 manifest source mismatch')
    return {'A007_primary_sha256':SEED_HASH,'A075_parent_solver_sha256':SOURCE_HASH,
            'A007_primary_shape':[2048,3], 'A007_max_torus_residual':float(np.max(np.abs(resid))),
            'status':'PROVENANCE_VERIFIED_PARENT_SOLVER_NOT_REPLACED'}



def load_a007_at_uniform_theta(n):
    """RESAMPLE authentic A007 equal-arclength 2048 points to theta collocation.

    Periodic cubic interpolation (not regeneration from analytic torus), keeping
    the SHA-verified A007 vertices as the actual computational input.
    """
    from scipy.interpolate import CubicSpline
    p=np.loadtxt(ROOT/'inputs/a007'/PRIMARY,comments='#',usecols=(0,1,2))
    theta=np.unwrap(np.arctan2(p[:,1],p[:,0]))/2.0
    if abs(theta[0])>1e-12 or not np.all(np.diff(theta)>0):
        raise RuntimeError('Unexpected A007 toroidal parameter ordering')
    spline=CubicSpline(np.r_[theta,2*math.pi],np.vstack((p,p[0])),bc_type='periodic')
    return np.asarray(spline(np.arange(n)*2*math.pi/n),dtype=np.float64)

def make_pdf(out:Path,rows:list[dict],cfg:dict):
    try:
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.enums import TA_LEFT
        from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak
    except ImportError:
        return False
    styles=getSampleStyleSheet(); story=[]
    def p(t,style='BodyText'):
        story.append(Paragraph(t,styles[style]));story.append(Spacer(1,8))
    p('A075 v0.2.10 | Ruban T(2,3) Relative Equilibrium', 'Title')
    p('Research diagnostic | Development only | 29 October 2026')
    p('Scientific question','Heading2')
    p('Does the exact paper-parameter trefoil at B0 = 77/500 approach a relative equilibrium, and how does the measured instantaneously fitted normal residual depend on B0?')
    p('Evidence boundary','Heading2')
    p('The embedded A007 seed and A075 v0.2.9 filament source are SHA256 checked. This implementation is independent midpoint Biot-Savart quadrature with Fourier curvature. It does NOT reproduce the author perturbation, provide a complete linear stability spectrum, certify nonlinear longevity, or run the 3D Euler field.')
    p('Model and methods','Heading2')
    p('R0 = 1; Gamma = 2 pi; delta = 1/20; Lambda = 7/5 + ln(200)/2. Filament velocity follows Ruban Eq. (9): midpoint segment Biot-Savart plus curvature-binormal coefficient (7/5-ln(2)/2)/2. Least-squares fit removes axial translation, axial rotation, and tangent reparameterization. Constrained Fourier harmonics are optional geometry corrections. The Ritz matrix is a gauge-incomplete exploratory projection, NOT a certified stability operator.')
    p('Numerical results','Heading2')
    table=[['B0','N','initial residual','relaxed residual','Ritz max Re','classification']]
    for r in rows:table.append([f"{r['B0']:.4f}",str(r['n']),f"{r['epsilon_initial']:.8g}",f"{r['epsilon_final']:.8g}",('N/A' if r['ritz_max_real'] is None else f"{r['ritz_max_real']:.7g}"),'DIAGNOSTIC'])
    tb=Table(table,repeatRows=1,colWidths=[40,40,78,78,75,85]);tb.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e2e8f0')),('GRID',(0,0),(-1,-1),.25,colors.grey),('FONTSIZE',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),6)]));story.append(tb)
    story.append(Spacer(1,14));p('Interpretation and stop gates','Heading2')
    p('A lower relative-equilibrium residual is NOT a stability certificate. Positive Ritz eigenvalues are an exploratory warning, not a validated physical growth rate. No spectral or topological PASS is assigned. Need independent quadrature, full constrained linearization, spatial and time convergence, perturbation sensitivity, and separate Euler finite-core checks.')
    p('Sources','Heading2')
    p('V. P. Ruban (2018), Long-lived quantum vortex knots, JETP Letters 107, 307-311, doi:10.1134/S0021364018050120. A007 v0.1.0 archived reconstruction; A075 v0.2.9 preserved source manifest.')
    SimpleDocTemplate(str(out/'A075-v0.2.10_FALSIFIER_REPORT.pdf'),pagesize=(595,842),rightMargin=38,leftMargin=38,topMargin=38,bottomMargin=38).build(story)
    return True

def run(args):
    provenance=verify()
    if not args.b_values:
        bvalues=[0.152,0.154,0.156] if args.command=='PILOT' else [round(0.148+i*.0005,6) for i in range(25)]
    else:bvalues=[float(v) for v in args.b_values.split(',')]
    if len(bvalues)>40 and not args.allow_expensive:raise SystemExit('More than 40 cases require --allow-expensive')
    if not all(0.02<=b<=0.32 for b in bvalues):raise SystemExit('B0 must be 0.02..0.32')
    if args.n>512 and not args.allow_expensive:raise SystemExit('n>512 requires --allow-expensive')
    if args.n<32 or args.n%2:raise SystemExit('n must be even >=32')
    timestamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    run_id=args.run_id or f'{args.command}_{timestamp}'
    if not run_id or not all(c.isalnum() or c in '_-' for c in run_id):raise SystemExit('Unsafe run_id')
    outbase=ROOT/f'{OUTPUT_PREFIX}_{VERSION}-outputs'
    out=outbase/run_id
    out.mkdir(parents=True,exist_ok=False)
    cfg={'schema':'A075_RUBAN_RE_STUDY_v1', 'release':'A075-v0.2.10-addon',
         'mode':args.command,'n':args.n,'B0_values':bvalues, 'harmonics':args.harmonics,
         'modes':args.modes,'max_nfev':args.max_nfev,'delta':DELTA,
         'Gamma':GAMMA,'Lambda':LAMBDA,'local_coefficient':LOCAL_COEFFICIENT,
         'source_provenance':provenance,
         'reference_geometry_consumption':'A007 uniform theta reconstruction from SHA256-pinned equal-arclength XYZ',
         'author_perturbation_available':False,
         'framework_invoked':False, 'full_Euler_3D_invoked':False,
         'status':'DEVELOPMENT_ONLY_SPECTRAL_AND_STABILITY_UNRESOLVED'}
    dump(cfg,out/'RUN_CONFIG.json')
    rows=[]
    for b in bvalues:
        anchor=(load_a007_at_uniform_theta(args.n) if abs(b-B_REFERENCE)<1e-12 else None)
        rr=relax(b,args.n,args.harmonics,args.max_nfev,reference_points=anchor)
        proxy=(numerical_spectral_proxy(rr['x'],rr['U'],rr['Omega'],args.modes) if args.modes>0 else None)
        row={'B0':b,'n':args.n,'epsilon_initial':rr['initial_epsilon'],
            'epsilon_final':rr['final_epsilon'],'U':rr['U'],'Omega':rr['Omega'],
            'ritz_max_real':proxy['max_real_part'] if proxy else None,
            'optimizer_success':rr['converged_optimizer'],'nfev':rr['nfev'],
            'geometry_source':('A007_SHA256_PINNED_CUBIC_RESAMPLE' if anchor is not None else 'ANALYTIC_TORUS_SCANNED'),
            'correction':rr['coeff'].tolist()}
        rows.append(row)
        np.savez_compressed(out/f'T23_B{b:.4f}_N{args.n}_RELAXED.npz',points=rr['x'],correction=rr['coeff'])
        if proxy:dump(proxy,out/f'T23_B{b:.4f}_RITZ.json')
        print(f'B={b:.4f} n={args.n} eps={rr["initial_epsilon"]:.8f} -> {rr["final_epsilon"]:.8f} ritz={row["ritz_max_real"]}',flush=True)
    with (out/'RUBAN_EQUILIBRIUM_RESULTS.csv').open('w',newline='',encoding='utf8') as f:
        writer=csv.DictWriter(f,fieldnames=['B0','n','epsilon_initial','epsilon_final','U','Omega','ritz_max_real','optimizer_success','nfev','correction','geometry_source']);writer.writeheader();writer.writerows(rows)
    assessment={'classification':'DIAGNOSTIC_ONLY','relative_equilibrium_proven':False,
                'linear_stability_proven':False,'physical_stability':'UNRESOLVED',
                'Ritz_is_gauge_incomplete':True,'topology_certified':False,
                'source_and_seed_verified':True,'no_automatic_status_promotion':True,
                'n_cases':len(rows), 'best_sampled_residual_B0':min(rows,key=lambda a:a['epsilon_final'])['B0']}
    dump(assessment,out/'SCIENTIFIC_ASSESSMENT.json')
    lines=['# A075-v0.2.10 Ruban T(2,3) mathematical diagnostic','',
           '**Status: DEVELOPMENT_ONLY — PHYSICAL_STABILITY_UNRESOLVED.**','',
           'Source: A007 exact 77/500 trefoil and original A075-v0.2.9 equation-(9) reference (SHA256 checked).',
           '', 'Hypothesis: a relative equilibrium and a converged, gauge-correct spectrum can explain a quasi-stable interval near B0=0.154.',
           '', 'Method: fixed-R0 analytic torus, midpoint Biot-Savart, Fourier curvature, least-squares axial motion removal, small harmonic shape corrections.',
           '', '| B0 | n | epsilon before | epsilon after | exploratory max Ritz Re |', '|---:|---:|---:|---:|---:|']
    for a in rows:lines.append(f"| {a['B0']:.4f} | {a['n']} | {a['epsilon_initial']:.9f} | {a['epsilon_final']:.9f} | {a['ritz_max_real']} |")
    lines+=['','**Conclusions:** Optimizer convergence is not equilibrium proof. Ritz values do not certify a physical growth rate; they omit full gauge and spectrum. Dynamics, time convergence, topology, and Euler finite-core remain NOT_RUN.', '', 'Reference: V. P. Ruban (2018), *Long-lived quantum vortex knots*, JETP Letters 107, 307–311, doi:10.1134/S0021364018050120.']
    (out/'FALSIFIER_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    make_pdf(out,rows,cfg)
    hashes={str(p.relative_to(out)):sha256(p) for p in sorted(out.rglob('*')) if p.is_file()}
    dump({'sha256':hashes},out/'MANIFEST_SHA256.json')
    zipfileout=ROOT.parent/f'{OUTPUT_PREFIX}_{VERSION}_{run_id}_outputs.zip'
    if zipfileout.exists():raise RuntimeError('Refuse overwrite existing results archive')
    with zipfile.ZipFile(zipfileout,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(out.rglob('*')):
            if p.is_file():z.write(p,arcname=f'{out.name}/{p.relative_to(out)}')
    zipfileout.with_suffix(zipfileout.suffix+'.sha256').write_text(sha256(zipfileout)+'  '+zipfileout.name+'\n',encoding='ascii')
    print('OUTPUT',out,'\nARCHIVE',zipfileout,'\nSTATUS: DEVELOPMENT_ONLY')
    return 0

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['VERIFY','PILOT','SCAN'])
    parser.add_argument('--n',type=int,default=128)
    parser.add_argument('--b-values',default='')
    parser.add_argument('--harmonics',type=int,default=1)
    parser.add_argument('--modes',type=int,default=4)
    parser.add_argument('--max-nfev',type=int,default=30)
    parser.add_argument('--allow-expensive',action='store_true')
    parser.add_argument('--run-id',default='')
    a=parser.parse_args()
    if a.command=='VERIFY':print(json.dumps(verify(),indent=2));return 0
    return run(a)

if __name__=='__main__':sys.exit(main())
