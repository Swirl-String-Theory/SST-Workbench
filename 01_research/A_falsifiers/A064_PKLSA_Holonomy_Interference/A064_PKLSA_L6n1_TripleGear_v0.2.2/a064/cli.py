"""A064 CLI: no silent upgrade of geometry into dynamical evidence."""
import argparse,json,hashlib,zipfile,sys
from pathlib import Path
import numpy as np
from .flow import SnapshotFlow,FilamentFlow,AnalyticFlow,file_hash
from .analysis import run

ROOT=Path(__file__).resolve().parents[1]
NAME='A064_PKLSA_Flow_Separatrix_Transport_v0.1.1'

def pack_report(runroot):
    from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,KeepTogether
    base=Path(runroot)
    results=sorted(base.glob('*/GATE_RESULTS.json'))
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CodeSmallA064',parent=styles['Normal'],fontName='Courier',fontSize=7,leading=10))
    pdf=base.parent / 'A064-v0.1.1_FALSIFIER_REPORT.pdf'
    doc=SimpleDocTemplate(str(pdf),pagesize=A4,rightMargin=42,leftMargin=42,topMargin=48,bottomMargin=45)
    s=[]
    def add(txt,sty='Normal'):s.append(Paragraph(txt,styles[sty]));s.append(Spacer(1,8))
    add('A064 - PKLSA Flow Separatrix Identification and Transport', 'Title')
    add('Prototype v0.1.1 | bundled NPZ builder | discovery-first | direct-snapshot authority required', 'Heading3')
    add('Scientific status: implementation-control study. The canonical SST Falsifier Framework v1.0.7 has NOT run its FREEZE/CERTIFY pipeline in this package. Do not infer physical SST validation.', 'Normal')
    add('Method and non-circular inference', 'Heading2')
    add('Stage I: compute the 3D velocity field and its curl. Extract a closed isosurface of |curl v| squared by a preregistered geometry-only ranking. Seal candidate parameters before any flow-transport observables are computed. This surface is a candidate feature, not a proven separatrix.')
    add('Stage II: compute normal relative level-set speed, tracer side exchanges and integration-step refinement. A surface moving with fluid particles is material by definition; therefore the decisive test is whether an independently re-detected flow feature remains aligned with that advected surface. A stable/unstable invariant manifold remains an independent, unsatisfied mathematical gate.')
    add('For F(x,t)=|curl v|^2-lambda, u_rel,n=(dF/dt+v.grad F)/|grad F|. For a material level set this vanishes. Dimensions: F [s^-2], |grad F| [m^-1 s^-2], u_rel,n [m s^-1]. The primary positive control is steady axisymmetric azimuthal flow; negative controls add transverse advection or remove vorticity.')
    add('Evidence limitations', 'Heading2')
    add('E010 v0.3.1 and E011 v0.3.0 qualify static geometry, not actual fluid velocity. This archive includes three independently hash-checked MODEL NPZs rebuilt from raw centerlines via BUILD_NPZ. Their repeated velocity frames are a frozen regularized midpoint Biot-Savart approximation, NOT an Euler-time integration. Only appropriately sourced independent dynamics can inform physical separatrix claims.')
    for f in results:
        d=json.loads(f.read_text(encoding='utf8'))
        rows=[['Field','Value'],['Evidence class',d['evidence_class']],['Candidate found',str(d['candidate_detected'])],['Dynamics',d['dynamical_feature_status']],['Manifold gate',d['true_separatrix_manifold_gate']],['Scientific gate',d['overall_scientific_gate']],['divergence p95 dx/U',f"{d['divergence_p95_dx_over_U']:.4g}"]]
        tr=d['transport']
        if tr.get('status')=='MEASURED':
            rows.extend([['p95 flux/U',f"{tr['flux_p95_over_U']:.5g}"],['Tracer crossings',f"{tr['tracer_cross_count']}/{tr['valid_tracers']}"],['Feature residual',f"{tr['advected_feature_residual_rel_p90']:.4g}"]])
        def shorten(x):return x if len(x)<=58 else x[:54]+'...'
        tbl=Table([[Paragraph(shorten(str(a)),styles['CodeSmallA064']),Paragraph(shorten(str(b)),styles['CodeSmallA064'])] for a,b in rows],colWidths=[162,315],repeatRows=1,hAlign='LEFT')
        tbl.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e4edf4')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f5f7f9')]),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#d5dde3')),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
        s.append(KeepTogether([Paragraph(f.parent.name,styles['Heading2']),Spacer(1,6),tbl,Spacer(1,14)]))
    add('Required next certification', 'Heading2')
    add('Run with actual 3D time snapshots from the same PKLSA carrier; verify incompressible Euler residuals, grid/time convergence, separatrix invariant-manifold extraction and E011 provider-envelope provenance. Rebuild under frozen Framework v1.0.7 and obtain genuine blind gate ledger and output manifest. Synthetic regression successes are never physical source replication.')
    add('Literature pointers (bibitems included in THEORY.tex)', 'Heading2')
    add('Helmholtz (1858); Batchelor (1967); Haller (2015); Shadden, Lekien &amp; Marsden (2005); Saffman (1992).')
    def footer(canvas,doc):
        canvas.saveState();canvas.setFont('Helvetica',8);canvas.setFillColor(colors.grey)
        canvas.drawRightString(565,27,f'A064 prototype | page {doc.page}');canvas.restoreState()
    doc.build(s,onFirstPage=footer,onLaterPages=footer)
    # Unsealed archive: deliberately not called v1.0.7 BLIND zip.
    zip_path=base.parent/(NAME+'-outputs_PROTOTYPE.zip')
    with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
        for f in sorted(base.rglob('*')):
            if f.is_file():z.write(f,f.relative_to(base.parent))
    return pdf,zip_path


def single(mode, flow, axes,t0,t1,out,source,skip_stagnation=False):
    res=run(flow,axes,t0,t1,out,mode,source,skip_stagnation=skip_stagnation)
    print(f"[{Path(out).name}] {res['dynamical_feature_status']} | overall={res['overall_scientific_gate']}")
    return res


def main(argv=None):
    ap=argparse.ArgumentParser(description='A064 discovery-first PKLSA flow separatrix falsifier prototype')
    ap.add_argument('mode',choices=['DEMO','SNAPSHOTS','PKLSA_GEOMETRY','SELFTEST','BUILD_NPZ','BUNDLED'])
    ap.add_argument('--source',type=Path,help='NPZ velocity snapshots or XYZ knot file')
    ap.add_argument('--output',type=Path,default=ROOT/(NAME+'-outputs'))
    ap.add_argument('--grid',type=int,default=31)
    ap.add_argument('--knot',choices=['all','3_1','5_2','6_1'],default='all')
    ap.add_argument('--output-npz',type=Path,help='single-source output file for BUILD_NPZ')
    ap.add_argument('--force',action='store_true',help='rebuild instead of accepting a valid existing NPZ')
    ap.add_argument('--time-frames',type=int,default=3)
    ap.add_argument('--scale-m-per-unit',type=float,help='MANDATORY for knot geometry! Native KnotPlot lengths have unspecified SI units')
    ap.add_argument('--core-m',type=float,help='regularization core radius [m]')
    ap.add_argument('--gamma-m2-s',type=float,help='circulation [m2/s]')
    ap.add_argument('--duration-s',type=float,default=.14)
    args=ap.parse_args(argv)
    if args.mode=='SELFTEST':
        import pytest
        return pytest.main([str(ROOT/'tests'),'-q'])
    if args.grid<21:ap.error('minimum grid resolution is 21, use >=31 for science runs')
    from .build_npz import build_all, preset_paths
    if args.mode=='BUILD_NPZ':
        results=build_all(ROOT,args)
        for r in results: print(json.dumps(r,sort_keys=True))
        return 0
    out=args.output;out.mkdir(exist_ok=True,parents=True)
    if args.mode=='BUNDLED':
        files=preset_paths(ROOT,args.knot)
        for name,path in files:
            if not path.exists() or not path.with_suffix('.source.json').exists():
                # Missing sources are built from the shipped original KnotPlot XYZ files.
                args.knot=name
                build_all(ROOT,args)
            model=SnapshotFlow(path)
            if not model.evidence_class.startswith('geometry_derived_'):
                raise RuntimeError('bundled source is not a verified model-derived NPZ')
            xyz=ROOT/'data'/'PKLSA_RAW_NATIVE_UNQUALIFIED'/f'knot_{name.replace("_",".")}.txt'
            if model.source_metadata.get('source_xyz_sha256')!=file_hash(xyz):
                raise RuntimeError('bundled NPZ no longer matches supplied raw centerline geometry')
            axes=model.axes
            single('SNAPSHOTS_MODEL_RECONSTRUCTION',model,axes,float(model.times[0]),float(model.times[-1]),
                   out/f'pklsa_{name}_npz',model.source_metadata,skip_stagnation=True)
        pdf,z=pack_report(out)
        print('PDF:',pdf,'\nOUTPUT ZIP:',z)
        return 0
    if args.mode=='DEMO':
        axes=tuple(np.linspace(-2.1,2.1,args.grid) for _ in range(3))
        for kind in ('material','leaky','translated','none','strain'):
            model=AnalyticFlow(kind,speed=.28,scale=1.)
            single('SYNTHETIC_CONTROL',model,axes,0.,.3,out/kind,'analytic_'+kind,skip_stagnation=(kind!='strain'))
        # Actual PKLSA-native raw centerline geometry, reconstructing three MODEL fields only.
        for knot in ('3.1','5.2','6.1'):
            source=ROOT/'data'/'PKLSA_RAW_NATIVE_UNQUALIFIED'/f'knot_{knot}.txt'
            points=np.loadtxt(source)
            field=FilamentFlow(points,core_m=.8,gamma_m2_s=10.)
            pad=3.5
            geo_axes=tuple(np.linspace(np.min(points[:,j])-pad,np.max(points[:,j])+pad,args.grid) for j in range(3))
            single('PKLSA_GEOMETRY_DEMO',field,geo_axes,0.,.14,out/f'pklsa_{knot.replace(".","_")}_model',
                   {'input_file':str(source.relative_to(ROOT)),'sha256':file_hash(source),
                    'scale_m_per_unit':1.,'calibration':'ARTIFICIAL_DEMO_NOT_PHYSICAL_SST'},skip_stagnation=True)
    elif args.mode=='SNAPSHOTS':
        if not args.source:ap.error('--source NPZ required')
        model=SnapshotFlow(args.source)
        axes=model.axes
        t0=float(model.times[0]);t1=float(model.times[-1]) if len(model.times)>1 else t0+args.duration_s
        single('SNAPSHOTS_MODEL_RECONSTRUCTION' if model.evidence_class.startswith('geometry_derived_') else 'SNAPSHOTS',model,axes,t0,t1,out/'direct_flow',model.source_metadata or {'file':str(args.source),'sha256':model.sha256})
    elif args.mode=='PKLSA_GEOMETRY':
        for k in ('source','scale_m_per_unit','core_m','gamma_m2_s'):
            if getattr(args,k) is None:ap.error(f'--{k.replace("_","-")} required to prevent invented physical units')
        points=np.loadtxt(args.source)*args.scale_m_per_unit
        model=FilamentFlow(points,core_m=args.core_m,gamma_m2_s=args.gamma_m2_s)
        pad=max(3.5*args.core_m,.15*np.ptp(points,axis=0).max())
        axes=tuple(np.linspace(points[:,j].min()-pad,points[:,j].max()+pad,args.grid) for j in range(3))
        single('PKLSA_GEOMETRY_RECONSTRUCTION',model,axes,0.,args.duration_s,out/'model_field',
               {'input_file':str(args.source),'sha256':file_hash(args.source),'scale_m_per_unit':args.scale_m_per_unit,
                'core_m':args.core_m,'gamma_m2_s':args.gamma_m2_s},skip_stagnation=True)
    pdf,z=pack_report(out)
    print('PDF:',pdf,'\nOUTPUT ZIP:',z)
    return 0

if __name__=='__main__':sys.exit(main())
