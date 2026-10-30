"""B007 v0.2.3: provenance-pinned, reduced-filament paired T(2,3) experiments.

Reads real 2048/4096 analytic E010 perturbed data from PKLSA ConsumerDataset
folders or their ZIPs.  Reconstructs nominal analytical partners from frozen
source. No physical stability / full 3-D Euler conclusions are granted.
"""
from __future__ import annotations
import argparse, csv, datetime as dt, hashlib, io, json, math, os, platform, re, sys, zipfile
from pathlib import Path, PurePosixPath
import numpy as np
from .geometry import ROOT, CONFIG, GENER, fingerprint, get_config, generate
from .filaments import velocity, fit, vertex_arclength_weights
from .pipeline import save_json, save_csv, manifest, pack_run

PREFIX='Gate2_Ruban_Familywise_Coupled_Falsifier'
VERSION='v0.2.3'
OUTBASE=ROOT/(PREFIX+'_'+VERSION+'-outputs')
PINNED_INDEX='70af49e67406e26187607eef5c624a88989e8fd5938d0c6f42ba3b2d23b75341'
PINNED_GENERATOR='2c73d35fd58c9f4bcb4ddbb336021883d0bdff44051105750a68fa0fc6a0c609'
PINNED_CONFIG='c7b29996e665296a99c376be044c66eb0ebefe31ecd516a3e53e9b908679890d'
IDPAT=re.compile(r'^RUBAN_v036_T_2_3_B(\d{4})_N1024_perturbed$')

def sha(data):return hashlib.sha256(data).hexdigest()

def path_safe(s):
    """Require flat relative paths with no dot segments; prohibit archive traversal."""
    p=PurePosixPath(s)
    if (not s or '\\' in s or p.is_absolute() or '..' in p.parts or
        '.' in p.parts or str(p)!=s or ':' in s or s.startswith('/')):
        raise ValueError('Unsafe relative dataset path '+repr(s))
    return s

class SourceDataset:
    def __init__(self,path,n):
        self.path=Path(path).resolve();self.n=n
        if not self.path.exists():raise FileNotFoundError(f'Dataset N{n} not found: {path}')
        self.z=None
        if self.path.is_file():
            self.z=zipfile.ZipFile(self.path)
            matches=[x for x in self.z.namelist() if x.endswith('/DATASET_MANIFEST.json') or x=='DATASET_MANIFEST.json']
            if len(matches)!=1:raise ValueError('Expected exactly one dataset manifest in '+str(path))
            self.prefix=matches[0].removesuffix('DATASET_MANIFEST.json')
            # Reject ambiguous or traversal archive names even if not selected.
            names=self.z.namelist()
            if len(names)!=len(set(names)):raise ValueError('Duplicate ZIP entries')
            for x in names:path_safe(x.rstrip('/'))
        else:
            self.prefix=''
            root=self.path
            if not (root/'DATASET_MANIFEST.json').exists():
                matches=list(root.glob('*/DATASET_MANIFEST.json'))
                if len(matches)!=1:raise ValueError('No single DATASET_MANIFEST.json in '+str(path))
                self.path=matches[0].parent
        raw=self.read('DATASET_MANIFEST.json',max_bytes=12_000_000)
        check=self.read('DATASET_MANIFEST.json.sha256',max_bytes=1000).decode().split()
        if len(check)!=2 or check[0]!=sha(raw) or check[1]!='DATASET_MANIFEST.json':
            raise ValueError('Dataset manifest checksum mismatch')
        self.manifest_sha=sha(raw);self.manifest=json.loads(raw)
        d=self.manifest
        if d.get('schema')!='SST-ATLAS-CONSUMER-DATASET-1':raise ValueError('Unknown dataset schema')
        if d['atlas']['index_sha256']!=PINNED_INDEX:raise ValueError('Different upstream E010 atlas')
        gen=d['generation']
        if (gen.get('kind')!='SOURCE_FAITHFUL_ANALYTIC_REGENERATION' or
            gen.get('source_generator_sha256')!=PINNED_GENERATOR or
            gen.get('source_config_sha256')!=PINNED_CONFIG or
            gen.get('export_point_count')!=n):
            raise ValueError('Unreviewed generator/configuration or wrong point resolution')
        if d['coordinate_policy']['automatic_SI_conversion'] is not False:raise ValueError('Unknown physical scaling')
        if len(d['records'])!=121 or len(d['files_sha256'])!=121:raise ValueError('Expected full 121-record research dataset')
        self.records={}
        for rec in d['records']:
            a=rec['atlas_record'];sid=a['id'];mt=IDPAT.fullmatch(sid)
            if not mt or a['parametric_embedding']!='T_2_3' or a['variant']!='perturbed' or a['collection']!='ruban_v036':
                raise ValueError('Unexpected atlas record '+sid)
            b=int(mt.group(1))/10000
            if abs(b-float(a['B0']))>1e-10:raise ValueError('Record B0/ID mismatch')
            if a['component_count']!=1 or len(rec['exported_components'])!=1:raise ValueError('Expected one loop')
            comp=rec['exported_components'][0]
            if comp['exported_point_count']!=n:raise ValueError('Component point count mismatch')
            path_safe(comp['relative_path'])
            if d['files_sha256'].get(comp['relative_path'])!=comp['sha256']:raise ValueError('Manifest hash disagreement')
            if sid in self.records:raise ValueError('Duplicate record')
            self.records[sid]=rec
        if sorted(int(k.split('_B')[1][:4]) for k in self.records)!=[200+25*i for i in range(121)]:
            raise ValueError('Unexpected B0 sampling grid')
    def read(self,relative,max_bytes=2_000_000):
        path_safe(relative)
        if self.z:
            info=self.z.getinfo(self.prefix+relative)
            if info.file_size>max_bytes:raise ValueError('Unexpected large file: '+relative)
            return self.z.read(info)
        root=self.path.resolve();file=(root/relative).resolve()
        if not file.is_relative_to(root):raise ValueError('Dataset path escapes root')
        if file.stat().st_size>max_bytes:raise ValueError('Unexpected large file')
        return file.read_bytes()
    def load(self,sid):
        rec=self.records[sid];entry=rec['exported_components'][0]
        raw=self.read(entry['relative_path'],max_bytes=1_000_000 if self.n==2048 else 2_000_000)
        if sha(raw)!=entry['sha256']:raise ValueError('Geometry hash mismatch: '+sid)
        data=np.loadtxt(io.BytesIO(raw),dtype=np.float64)
        if data.shape!=(self.n,3) or not np.isfinite(data).all():raise ValueError('Invalid geometry: '+sid)
        if np.linalg.norm(data-np.roll(data,1,axis=0),axis=1).min()<=0:raise ValueError('Degenerate geometry: '+sid)
        return data
    def close(self):
        if self.z:self.z.close()
    def __enter__(self):return self
    def __exit__(self,*_):self.close()


def compare_analytic_source(record_id: str, source_n: int, loaded: np.ndarray,
                            regenerated: np.ndarray) -> dict:
    """Fail-closed cross-platform analytic parity check, not a topology gate.

    The dataset SHA-256 remains exact.  Independent evaluation of NumPy/libm
    trigonometry on Windows/Linux can differ by a few float64 ulps even when
    it represents the identical analytic E010 formula.  Bitwise identity of
    coordinates computed on different machines is not a scientific invariant.

    Bound BOTH the worst coordinate and global RMS error to small multiples of
    IEEE-754 machine epsilon and the absolute geometric coordinate scale.  Do
    not use np.allclose's generous default rtol=1e-5 or replace the hash gate.
    """
    loaded=np.asarray(loaded,dtype=np.float64)
    regenerated=np.asarray(regenerated,dtype=np.float64)
    if loaded.shape != regenerated.shape or loaded.shape != (source_n,3):
        raise ValueError(f'Analytic source shape mismatch: {record_id}, N={source_n}: '
                         f'file={loaded.shape}, calculated={regenerated.shape}')
    if not (np.isfinite(loaded).all() and np.isfinite(regenerated).all()):
        raise ValueError(f'Nonfinite analytic source coordinates: {record_id}, N={source_n}')
    diff=np.abs(loaded-regenerated)
    max_error=float(diff.max())
    rms_error=float(np.sqrt(np.mean(diff*diff)))
    scale=max(1.,float(np.max(np.abs(loaded))),float(np.max(np.abs(regenerated))))
    eps=float(np.finfo(np.float64).eps)
    max_limit=128*eps*scale
    rms_limit=32*eps*scale
    exact=(max_error==0.)
    checked=(max_error<=max_limit and rms_error<=rms_limit)
    status='EXACT' if exact else ('BOUNDED_FLOAT64_ROUNDOFF' if checked else 'MISMATCH_REJECTED')
    audit={'record_id':record_id,'source_N':source_n,'status':status,
           'max_abs_error':max_error,'rms_abs_error':rms_error,
           'max_allowed_abs_error':max_limit,'rms_allowed_abs_error':rms_limit,
           'coordinate_scale':scale,'bitwise_equal':exact,
           'provenance_validation':'SOURCE_FILE_SHA256_STILL_REQUIRED'}
    if not checked:
        where=np.unravel_index(np.argmax(diff),diff.shape)
        raise ValueError('Analytic source mismatch: '
                         f'{record_id}, N={source_n}; max_abs_error={max_error:.17g} '
                         f'(allowed {max_limit:.17g}); rms={rms_error:.17g} '
                         f'(allowed {rms_limit:.17g}); worst_index={where}. '
                         'Source SHA-256 was verified, but coordinates differ by more '
                         'than strictly bounded float64 roundoff. Stop and investigate '
                         'generator/config/platform before running dynamics.')
    return audit


def match_sources(a,b):
    if set(a.records)!=set(b.records):raise ValueError('2048/4096 record IDs differ')
    for sid in a.records:
        x=a.records[sid]['atlas_record'];y=b.records[sid]['atlas_record']
        for k in ('geometry_sha256','parent_id','source_independence_group','B0','topology_id'):
            if x.get(k)!=y.get(k):raise ValueError(f'Inconsistent {k} across resolutions: {sid}')
    if a.manifest['generation']['perturbation']!=b.manifest['generation']['perturbation']:
        raise ValueError('Inconsistent perturbation policies')


def select_ids(data,args):
    if args.all and (args.b0 or args.b_min is not None or args.limit):
        raise ValueError('--all cannot be combined with --b0/--b-min/--limit')
    ids=sorted(data.records,key=lambda k:float(data.records[k]['atlas_record']['B0']))
    if args.b0:
        bs=[float(s) for s in args.b0.split(',')]
        if len(bs)!=len(set(bs)):raise ValueError('Duplicate --b0')
        ids=[sid for sid in ids if any(abs(data.records[sid]['atlas_record']['B0']-b)<1e-9 for b in bs)]
        if len(ids)!=len(bs):raise ValueError('Some requested B0 values are absent')
    elif args.b_min is not None or args.b_max is not None:
        if args.b_min is None or args.b_max is None:raise ValueError('Give both --b-min and --b-max')
        ids=[sid for sid in ids if args.b_min-1e-10<=data.records[sid]['atlas_record']['B0']<=args.b_max+1e-10]
    elif not args.all and not args.limit:
        raise ValueError('Choose --b0, --b-min/--b-max, --limit, or explicit --all')
    if args.limit:ids=ids[:args.limit]
    if not ids:raise ValueError('No selected records')
    return ids


def decimate(points,n):
    """Exact parameter-index subsampling, never pretend a fine source was simulated."""
    if len(points)==n:return points.copy()
    if n>len(points) or len(points)%n:raise ValueError('Dynamic points must divide source count exactly')
    return points[::len(points)//n].copy()


def kabsch_distance(p,q):
    """Rigid SE(3) shape quotient, same material labels and fixed curve orientation."""
    p=np.asarray(p);q=np.asarray(q)
    pc=p.mean(axis=0);qc=q.mean(axis=0);pp=p-pc;qq=q-qc
    U,s,Vt=np.linalg.svd(pp.T@qq)
    det=np.linalg.det(U@Vt)
    Q=U@np.diag([1,1,1 if det>=0 else -1])@Vt
    rms=float(np.sqrt(np.mean(np.sum((pp@Q-qq)**2,axis=1))))
    scale=float(np.sqrt(np.mean(np.sum(pp*pp,axis=1))))
    return rms/max(scale,1e-30)


def length(p):return float(np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1).sum())


def evolve(nom,pert,lam,steps,T,snapshots):
    """Same two-stage Heun discretization of regularized Biot-Savart filament ODE.

    Does NOT prove Euler PDE stability. Source arrays are never changed in place.
    The same fixed Gamma=1 and sigma=exp(-Lambda) apply to both trajectories.
    """
    a=nom.copy();b=pert.copy();sigma=math.exp(-lam);h=T/steps
    d0=kabsch_distance(a,b);la0=length(a);lb0=length(b)
    if d0<=1e-12:raise ValueError('Perturbation too small to resolve reliably')
    shape_a0=a.copy();shape_b0=b.copy()
    trace=[]
    def measure(k):
        d=kabsch_distance(a,b)
        return {'step':k,'t_star':k*h,'separation':d,'amplification':d/d0,
                'shape_drift_nominal':kabsch_distance(shape_a0,a),
                'shape_drift_perturbed':kabsch_distance(shape_b0,b),
                'length_drift_nominal':length(a)/la0-1.,'length_drift_perturbed':length(b)/lb0-1.}
    trace.append(measure(0))
    for k in range(1,steps+1):
        # Physics: independent full circulation Gamma=1 in each run, not
        # simultaneous two interacting curves; nominal and perturbed are alternatives.
        va=velocity([a],sigma,component_gamma=[1.])[0]
        vb=velocity([b],sigma,component_gamma=[1.])[0]
        pa=a+h*va;pb=b+h*vb
        wa=velocity([pa],sigma,component_gamma=[1.])[0]
        wb=velocity([pb],sigma,component_gamma=[1.])[0]
        a=a+.5*h*(va+wa);b=b+.5*h*(vb+wb)
        if not (np.isfinite(a).all() and np.isfinite(b).all()):raise FloatingPointError('Nonfinite trajectory')
        if k==steps or k%snapshots==0:trace.append(measure(k))
    final=trace[-1];amps=np.array([x['amplification'] for x in trace])
    return {'initial_separation':d0,'final_separation':final['separation'],
            'amplification_final':final['amplification'],
            'amplification_max_observed':float(amps.max()),
            'amplification_min_after_initial':float(amps[1:].min()),
            'finite_time_log_amplification_rate':math.log(max(final['amplification'],1e-300))/T,
            'return_below_initial_observed':bool(np.any(amps[1:]<1)),
            'shape_drift_nominal':final['shape_drift_nominal'],
            'shape_drift_perturbed':final['shape_drift_perturbed'],
            'relative_length_drift_nominal':final['length_drift_nominal'],
            'relative_length_drift_perturbed':final['length_drift_perturbed'],
            'final_time_star':T,'steps':steps,'dt_star':h,'sigma_over_R0':sigma,
            'time_samples':trace}


def gate_compare(coarse,fine,abs_tolerance,amp_tolerance):
    keys=['amplification_final','shape_drift_nominal','shape_drift_perturbed',
          'relative_length_drift_nominal','relative_length_drift_perturbed']
    changes={k:abs(fine[k]-coarse[k]) for k in keys}
    denom=max(abs(fine['amplification_final']),1e-12)
    good=changes['amplification_final']/denom<=amp_tolerance and all(
        changes[k]<=abs_tolerance for k in keys[1:])
    return {'status':'TWO_LEVEL_DIAGNOSTIC_CONSISTENCY' if good else 'UNRESOLVED_DISCRETIZATION_CHANGE',
            'tolerance_amplification_relative':amp_tolerance,'tolerance_other_absolute':abs_tolerance,
            'absolute_changes':changes,'relative_amplification_change':changes['amplification_final']/denom}


def write_pdf(path, args, plan, cases, rank, provenance):
    """Two-page-ready compact scientific record, not a stability certificate."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
    from reportlab.lib.units import mm
    style=getSampleStyleSheet()
    style.add(ParagraphStyle(name='SubtleText',parent=style['Normal'],fontSize=8.5,leading=12,textColor=colors.HexColor('#41536B')))
    style.add(ParagraphStyle(name='AtlasTitle',parent=style['Title'],fontSize=16,leading=21,textColor=colors.HexColor('#183457')))
    style.add(ParagraphStyle(name='AtlasSmall',parent=style['Normal'],fontSize=8.2,leading=11))
    doc=SimpleDocTemplate(str(path),pagesize=A4,leftMargin=18*mm,rightMargin=18*mm,topMargin=17*mm,bottomMargin=17*mm)
    blocks=[Paragraph('B007 v0.2.3 - Atlas Perturbation Dynamics',style['AtlasTitle']),
            Paragraph('Development-only / no Euler equilibrium or chaos certification',style['SubtleText']),Spacer(1,12)]
    blocks.append(Paragraph('Executed protocol',style['Heading2']))
    for v in [f'{len(cases)} paired B0/Lambda cases, source resolutions N=2048 and 4096',
              f'Dynamical points: {plan["dynamics_points"]}; base steps {args.steps}, temporal holdout {args.steps*2}',
              f'Fixed dimensionless final time T*= {args.final_time}; Lambda = {plan["lambda_values"]}',
              'Separate independent nominal and perturbed regularized Biot-Savart filament trajectories (Gamma=1).',
              'At every sampled time, differences are quotient by proper rigid rotation and translation (SE(3)).',
              'The data provide finite-time growth diagnostics, not asymptotic Lyapunov exponents.']:
        blocks.append(Paragraph('&bull; '+v,style['AtlasSmall']))
    blocks.append(Spacer(1,12));blocks.append(Paragraph('Numerical qualification',style['Heading2']))
    good=sum(x['numerical_assessment']=='PROVISIONAL_TWO_LEVEL_CONSISTENCY_NOT_STABILITY' for x in cases)
    for q in [f'Native two-level spatial comparison: {plan["native_spatial_comparison"]}',
              f'Numerically consistent (two-level heuristic): {good} / {len(cases)}',
              'Spatial: N_low vs N_high at fixed T* and the same refined time-step count.',
              'Temporal: nstep vs 2*nstep at fixed T* for each spatial resolution.',
              'Two levels are not sufficient to establish continuum convergence.']:
        blocks.append(Paragraph('&bull; '+q,style['AtlasSmall']))
    blocks.append(Spacer(1,12));blocks.append(Paragraph('Leading numerical candidates (not physical ranks)',style['Heading2']))
    rows=[['B0','Lambda','Max observed gain','Spatial diagnostic']]
    for r in rank[:8]:
        rows.append([f'{r["B0"]:.4f}',f'{r["Lambda"]:.3f}',f'{r["max_sampled_amplification_higher"]:.6g}',r['spatial_gate'].replace('TWO_LEVEL_','')])
    if len(rows)==1:rows.append(['-','-','No candidates qualified','-'])
    tab=Table(rows,colWidths=[33*mm,32*mm,42*mm,63*mm],repeatRows=1,hAlign='LEFT')
    tab.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#203A60')),
       ('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
       ('FONTSIZE',(0,0),(-1,-1),8),('VALIGN',(0,0),(-1,-1),'TOP'),
       ('BOTTOMPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),
       ('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#CDD8E5'))]))
    blocks.append(tab);blocks.append(Spacer(1,13))
    blocks.append(Paragraph('Provenance and exclusions',style['Heading2']))
    for q in ['All records correspond to one Ruban analytic source group, not independent experiments.',
              'Original dataset manifests and source-geometry hashes preserved in RUN_CONFIG.json.',
              'The source coordinate unit is dimensionless R0=1; sigma=exp(-Lambda).',
              'Full 3D incompressible finite-core Euler, reach, knot topology under dynamics, and asymptotic chaos remain NOT RUN/UNRESOLVED.',
              'Do not infer a physical Swirl Clock or stable vortex knot from this screen.']:
        blocks.append(Paragraph('&bull; '+q,style['AtlasSmall']))
    def footer(c,doc):
        c.saveState();c.setFont('Helvetica',8);c.setFillColor(colors.HexColor('#65758B'))
        c.drawString(18*mm,10*mm,'B007 v0.2.3 - DEVELOPMENT / NO SCIENTIFIC PROMOTION')
        c.drawRightString(192*mm,10*mm,str(doc.page));c.restoreState()
    doc.build(blocks,onFirstPage=footer,onLaterPages=footer)


def parser():
    p=argparse.ArgumentParser(description='B007 v0.2.3: paired E010 T(2,3) perturbation dynamics; no stability certification.')
    p.add_argument('--dataset-2048',required=True,help='Extracted N2048 directory or E010 dataset ZIP')
    p.add_argument('--dataset-4096',required=True,help='Extracted N4096 directory or E010 dataset ZIP')
    s=p.add_mutually_exclusive_group();s.add_argument('--b0');s.add_argument('--all',action='store_true');s.add_argument('--limit',type=int)
    p.add_argument('--b-min',type=float);p.add_argument('--b-max',type=float)
    p.add_argument('--lambda-values',default='3.4,4.0')
    p.add_argument('--dynamics-points',default='2048,4096',help='e.g. 128,256 for diagnostic pilot; 2048,4096 native two-level study')
    p.add_argument('--steps',type=int,default=16,help='base temporal resolution; each case also runs 2x steps')
    p.add_argument('--final-time',type=float,default=.003)
    p.add_argument('--trace-every',type=int,default=1,help='write diagnostics at every N integration steps')
    p.add_argument('--amplification-tolerance',type=float,default=.05)
    p.add_argument('--shape-tolerance',type=float,default=.005)
    p.add_argument('--max-edge-over-core',type=float,default=2.0,help='Heuristic: longest polygon edge / sigma bound')
    p.add_argument('--max-dt-over-core2',type=float,default=1.0,help='Heuristic: base dt / sigma^2 bound; not a CFL proof')
    p.add_argument('--run-id',help='new immutable run directory')
    p.add_argument('--dry-run',action='store_true')
    p.add_argument('--confirm-full',action='store_true',help='required for all 121 x native full simulation')
    p.add_argument('--verify-all-inputs',action='store_true',help='verify SHA-256 of all 242 XYZ source files')
    return p


def main(argv=None):
    args=parser().parse_args(argv)
    if fingerprint(GENER)!=PINNED_GENERATOR or fingerprint(CONFIG)!=PINNED_CONFIG:
        raise ValueError('B007 E010 generator/config no longer match reviewed dataset')
    if args.steps<1 or args.final_time<=0 or args.trace_every<1 or args.limit is not None and args.limit<1 or args.max_edge_over_core<=0 or args.max_dt_over_core2<=0:
        raise ValueError('Invalid simulation settings')
    ll=[float(k) for k in args.lambda_values.split(',')]
    if not ll or len(set(ll))!=len(ll) or any(not math.isfinite(x) or x<=0 for x in ll):
        raise ValueError('Invalid Lambda list')
    ns=[int(k) for k in args.dynamics_points.split(',')]
    if len(ns)!=2 or sorted(set(ns))!=ns or ns[0]<64 or ns[1]>4096 or 2048%ns[0] or 4096%ns[1]:
        raise ValueError('Two strictly ascending resolutions dividing native N2048/N4096 required')
    if args.b0 and (args.b_min is not None or args.b_max is not None):raise ValueError('Select --b0 or --b-min/--b-max')
    with SourceDataset(args.dataset_2048,2048) as ds2, SourceDataset(args.dataset_4096,4096) as ds4:
        match_sources(ds2,ds4)
        ids=select_ids(ds2,args)
        nat=ns==[2048,4096]
        if args.all and nat and not args.confirm_full and not args.dry_run:
            raise ValueError('Full 121 x native 2048/4096 campaign requires --confirm-full')
        # O(N^2), 2 trajectories, 2 Heun stages, both time step levels, both spatial levels.
        operations=len(ids)*len(ll)*sum((n*n)*2*2*(args.steps+2*args.steps) for n in ns)
        plan={'schema':'B007-ATLAS-PAIR-PLAN-1','version':VERSION,'selected_B0_count':len(ids),
              'lambda_values':ll,'case_count':len(ids)*len(ll),'filament_model':'REDUCED_REGULARIZED_MIDPOINT_BIOT_SAVART_HEUN',
              'source_points':[2048,4096],'dynamics_points':ns,'native_spatial_comparison':nat,
              'base_steps':args.steps,'temporal_refinement_steps':2*args.steps,
              'final_time_star':args.final_time,'estimated_kernel_interactions':operations,
              'science':'NOT_RUN/NO_STABILITY_CERTIFICATION'}
        print(json.dumps(plan,indent=2),flush=True)
        if args.dry_run:return 0
        if args.verify_all_inputs:
            for dataset in (ds2,ds4):
                for sid in dataset.records:dataset.load(sid)
            print('Input hash verification: 242/242 file SHA-256 validated.',flush=True)
        now=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        run_id=args.run_id or ('T23_PAIR_'+now+'_'+sha(json.dumps(vars(args),sort_keys=True).encode())[:8])
        if not re.fullmatch('[A-Za-z0-9_-]{1,90}',run_id):raise ValueError('Unsafe --run-id')
        output=OUTBASE/'runs'/run_id
        if output.exists():raise FileExistsError('Create-only run exists: '+str(output))
        output.mkdir(parents=True)
        (output/'INCOMPLETE_DO_NOT_PROMOTE.txt').write_text('Run incomplete; no scientific promotion.\n')
        provenance={'version':VERSION,'run_id':run_id,'arguments':vars(args),'source_data':[
                {'path':str(d.path),'manifest_sha256':d.manifest_sha,'atlas_index_sha256':d.manifest['atlas']['index_sha256'],
                 'generation_sha256':d.manifest['generation']['source_generator_sha256'],
                 'source_config_sha256':d.manifest['generation']['source_config_sha256'],
                 'native_points':d.n,'count':len(d.records)} for d in (ds2,ds4)],
            'source_code_hashes':{str(p.relative_to(ROOT)).replace('\\','/'):fingerprint(p) for p in sorted((ROOT/'src').rglob('*.py'))},
            'numpy':np.__version__,'python':sys.version.split()[0],'platform':platform.platform(),
            'plan':plan,'scientific_status':'NOT_QUALIFIED'}
        save_json(output/'RUN_CONFIG.json',provenance)
        records=[];time_rows=[];cross=[];rank=[];analytic_checks=[]
        try:
            for sid in ids:
                b=float(ds2.records[sid]['atlas_record']['B0'])
                loaded={2048:ds2.load(sid),4096:ds4.load(sid)}
                # A SHA-verified file is additionally checked against the same analytic
                # deformation used to reconstruct the nominal source at its OWN resolution.
                cfg=get_config()
                for source_n,arr in loaded.items():
                    regenerated=generate(2,3,b,source_n,True,cfg)[0]
                    check=compare_analytic_source(sid,source_n,arr,regenerated)
                    analytic_checks.append(check)
                    save_json(output/'G1_ANALYTIC_SOURCE_PARITY.json',{
                        'schema':'B007-ANALYTIC-PARITY-FLOAT64-1',
                        'contract':'Exact SHA256 file integrity + bounded platform roundoff only',
                        'checks':analytic_checks,
                        'scientific':'SOURCE_PARITY_ONLY_NOT_STABILITY'})
                    if check['status']!='EXACT':
                        print(f'SOURCE PARITY N={source_n} {check["status"]}: '
                              f'max_abs_error={check["max_abs_error"]:.3g}, '
                              f'limit={check["max_allowed_abs_error"]:.3g}',flush=True)
                for lam in ll:
                    tests={}
                    for source_n,n in zip((2048,4096),ns):
                        pert=decimate(loaded[source_n],n)
                        nominal=decimate(generate(2,3,b,source_n,False,cfg)[0],n)
                        if n!=len(pert):raise AssertionError('Unexpected dynamic point count')
                        sigma=math.exp(-lam)
                        max_edge=max(float(np.linalg.norm(np.roll(part,-1,axis=0)-part,axis=1).max()) for part in (nominal,pert))
                        edge_over_core=max_edge/sigma
                        base_dt_over_core2=(args.final_time/args.steps)/(sigma*sigma)
                        preflight=(edge_over_core<=args.max_edge_over_core and base_dt_over_core2<=args.max_dt_over_core2)
                        first=evolve(nominal,pert,lam,args.steps,args.final_time,args.trace_every)
                        second=evolve(nominal,pert,lam,args.steps*2,args.final_time,args.trace_every)
                        tgate=gate_compare(first,second,args.shape_tolerance,args.amplification_tolerance)
                        tests[n]=(first,second,tgate,preflight,edge_over_core,base_dt_over_core2)
                        time_rows.extend([{'id':sid,'B0':b,'Lambda':lam,'source_N':source_n,'dynamic_N':n,'steps':st,
                                           **r} for st,run in ((args.steps,first),(2*args.steps,second)) for r in run['time_samples']])
                        records.append({'id':sid,'B0':b,'Lambda':lam,'source_N':source_n,'dynamic_N':n,
                           'run_source_sha256':ds2.records[sid]['atlas_record']['geometry_sha256'],
                           'steps':args.steps,'refined_steps':args.steps*2,'initial_separation':second['initial_separation'],
                           'amplification_final':second['amplification_final'],'amplification_max_observed':second['amplification_max_observed'],
                           'finite_time_log_amplification_rate':second['finite_time_log_amplification_rate'],
                           'return_below_initial_observed':second['return_below_initial_observed'],
                           'shape_drift_nominal':second['shape_drift_nominal'],
                           'shape_drift_perturbed':second['shape_drift_perturbed'],
                           'length_drift_nominal':second['relative_length_drift_nominal'],
                           'length_drift_perturbed':second['relative_length_drift_perturbed'],
                           'temporal_gate':tgate['status'],
                           'screen_preflight':'HEURISTIC_PASS_NOT_PHYSICAL_QUALIFICATION' if preflight else 'HEURISTIC_UNDERRESOLVED',
                           'max_segment_over_core':edge_over_core,'base_dt_over_core2':base_dt_over_core2,
                           'temporal_amplification_relative_difference':tgate['relative_amplification_change'],
                           'native_resolution':n==source_n,'physical_status':'UNRESOLVED_REDUCED_FILAMENT_ONLY'})
                    spatial=gate_compare(tests[ns[0]][1],tests[ns[1]][1],args.shape_tolerance,args.amplification_tolerance)
                    good=all(tests[n][2]['status']=='TWO_LEVEL_DIAGNOSTIC_CONSISTENCY' for n in ns) and spatial['status']=='TWO_LEVEL_DIAGNOSTIC_CONSISTENCY'
                    preflight_all=all(tests[n][3] for n in ns)
                    upper=tests[ns[-1]][1]
                    verdict=('HEURISTIC_UNDERRESOLVED' if not preflight_all else
                             'PROVISIONAL_TWO_LEVEL_CONSISTENCY_NOT_STABILITY' if good and nat else
                             'REDUCED_RESOLUTION_DIAGNOSTIC_ONLY' if not nat else 'NUMERICAL_CONVERGENCE_UNRESOLVED')
                    cross.append({'id':sid,'B0':b,'Lambda':lam,'lower_N':ns[0],'higher_N':ns[1],
                                  'spatial_gate':spatial['status'],'spatial_amplification_relative_difference':spatial['relative_amplification_change'],
                                  'temporal_gate_lower':tests[ns[0]][2]['status'],
                                  'temporal_gate_higher':tests[ns[1]][2]['status'],
                                  'amplification_higher':upper['amplification_final'],
                                  'max_sampled_amplification_higher':upper['amplification_max_observed'],
                                  'log_amplification_rate_higher':upper['finite_time_log_amplification_rate'],
                                  'return_below_initial_higher':upper['return_below_initial_observed'],
                                  'shape_drift_higher_nominal':upper['shape_drift_nominal'],
                                  'shape_drift_higher_perturbed':upper['shape_drift_perturbed'],
                                  'numerical_assessment':verdict,'dynamic_stability':'NOT_ESTABLISHED',
                                  'both_preflights_pass_heuristic':preflight_all,
                                  'max_segment_over_core_by_N':{str(n):tests[n][4] for n in ns},
                                  'base_dt_over_core2':tests[ns[-1]][5],
                                  'spatial_comparison_details':spatial,'temporal_comparison_details':{str(n):tests[n][2] for n in ns}})
                    print(f'PAIR {sid} Lambda={lam:g} N={ns} amp={upper["amplification_final"]:.6g} -> {verdict}',flush=True)
                    # Progressive checkpoint to survive interruptions; not a completed release.
                    save_csv(output/'G2_PAIRED_DYNAMICS.csv',records)
                    save_csv(output/'G2_TIME_SERIES.csv',time_rows)
                    save_csv(output/'G3_CONVERGENCE.csv',[{k:v for k,v in r.items() if not isinstance(v,dict)} for r in cross])
            ranked=sorted([r for r in cross if r['numerical_assessment']=='PROVISIONAL_TWO_LEVEL_CONSISTENCY_NOT_STABILITY'],
                          key=lambda x:(x['max_sampled_amplification_higher'],
                                        max(x['shape_drift_higher_nominal'],x['shape_drift_higher_perturbed']),x['B0'],x['Lambda']))
            rank=[{**{k:v for k,v in r.items() if not isinstance(v,dict)},'rank_provisional':i} for i,r in enumerate(ranked,1)]
            save_csv(output/'G3_PROVISIONAL_RANKING.csv',rank)
            save_json(output/'G3_INDEPENDENT_GATES.json',{'spatial_gate':'TWO_RESOLUTION_COMPARISON_ONLY',
                'temporal_gate':'TWO_TIMESTEP_COMPARISON_ONLY',
                'valid_native_spatial_comparisons':nat,'cases':cross,
                'selection_rule':'Only native two-level numerically consistent cases; rank by observed maximum amplification, then shape drift. Not chaos/stability classification.',
                'scientific':'NOT_GRANTED'})
            save_json(output/'G0_G4_ASSESSMENT.json',{'schema':'B007-ATLAS-PERTURBATION-GATES-1',
                'G0':'PASS_PINNED_SOURCE_AND_MANIFEST_CHECKS','G1':'PASS_ANALYTIC_RECONSTRUCTION_ONLY',
                'G2':'EXECUTED_REDUCED_FILAMENT_PAIRS_NOT_EULER',
                'G3':'TWO_LEVEL_NUMERICAL_CONSISTENCY_ONLY_NOT_FORMAL_CONVERGENCE',
                'G4':'NOT_RUN_FULL_FIELD_EULER',
                'selected_cases':len(cross),'provisional_numeric_candidates':len(ranked),
                'scientific':'UNRESOLVED_NO_NONLINEAR_STABILITY_OR_CHAOS_CERTIFICATION'})
            report='\n'.join(['# B007 v0.2.3 — Atlas Perturbation Dynamics','',
                f'- Cases: {len(cross)}; input perturbed records: {len(ids)}; Lambda values: {ll}',
                f'- Input source points: 2048,4096; dynamical points: {ns}; base/refined steps: {args.steps}/{args.steps*2}; T*={args.final_time}',
                f'- Native two-level comparisons: {nat}; provisional consistent cases: {len(ranked)}',
                '- Filament model: regularized midpoint Biot-Savart plus explicit Heun, one knot at a time with circulation Gamma=1.',
                '- Nominal and perturbed evolve independently from the same analytic source and identical solver settings.',
                '- Rigid separation uses proper Kabsch SE(3) alignment at each sampled time. Material indexing retained; no cyclic reparametrization.',
                '- Finite-time log growth and observed return are *diagnostics*, not Lyapunov exponent, attractor, proof of chaos or stability.',
                '- Spatial and temporal gates compare only two levels. True asymptotic convergence requires additional independent levels.',
                '- Edge/core and timestep/core^2 preflight heuristics can block promotion; neither proves stability.',
                '- Shape/length errors, core clearance, finite-core Euler and cross-model agreement remain UNRESOLVED.',
                '- Source coordinates are dimensionless R0=1; no SI calibration.',
                '- G4 is NOT RUN. No physical clock or Euler equilibrium claim.',
                '\n## Selected provisional numerical candidates',
                *[f'- B0={x["B0"]:.4f}, Lambda={x["Lambda"]:.3f}, max observed amplification={x["max_sampled_amplification_higher"]:.8g}' for x in rank[:12]],
                '\n## Dataset integrity',
                *[f'- N{x.n}: manifest SHA256 {x.manifest_sha}' for x in (ds2,ds4)],''])
            (output/'FALSIFIER_REPORT.md').write_text(report,encoding='utf-8')
            write_pdf(output/'FALSIFIER_REPORT.pdf',args,plan,cross,rank,provenance)
            (output/'INCOMPLETE_DO_NOT_PROMOTE.txt').unlink()
            manifest(output)
            arc=pack_run(output)
            print(json.dumps({'status':'COMPLETED_REDUCED_FILAMENT_DIAGNOSTIC_ONLY','cases':len(cross),
                              'provisional_numerical_candidates':len(rank),'output':str(output),'archive':str(arc)},indent=2),flush=True)
        except BaseException as exc:
            save_json(output/'FAILURE.json',{'error':repr(exc),'completed_cases':len(cross),
                                           'status':'INCOMPLETE_NOT_SCIENTIFICALLY_ADMITTED'})
            raise
    return 0

if __name__=='__main__':sys.exit(main())
