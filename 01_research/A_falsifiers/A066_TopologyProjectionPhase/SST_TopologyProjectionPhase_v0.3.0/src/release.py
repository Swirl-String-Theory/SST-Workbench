"""Generate sourced, audit-bounded PDF and reproducible output/source releases."""
from __future__ import annotations
import hashlib,json,os,subprocess,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT.parent/(ROOT.name+'-outputs')

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def build_pdf(root=ROOT,outfile=None):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image,KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    if Path(font).exists():
        pdfmetrics.registerFont(TTFont('DV',font));fn='DV'
    else:fn='Helvetica'
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='PaperTitleX',fontName=fn,fontSize=17,leading=23,spaceAfter=12))
    styles.add(ParagraphStyle(name='PaperHeadingX',fontName=fn,fontSize=12,leading=17,spaceBefore=15,spaceAfter=7))
    styles.add(ParagraphStyle(name='PaperBodyX',fontName=fn,fontSize=9,leading=14,spaceAfter=8))
    styles.add(ParagraphStyle(name='PaperSmallX',fontName=fn,fontSize=7.5,leading=11,spaceAfter=7))
    styles.add(ParagraphStyle(name='PaperTableCellX',fontName=fn,fontSize=7.1,leading=9.5,wordWrap='LTR'))
    census=json.loads((root/'results/GEOMETRY_CENSUS_SUMMARY.json').read_text())
    assess=json.loads((root/'results/CONVERGENCE_ASSESSMENT.json').read_text())
    results=json.loads((root/'results/GEOMETRY_CENSUS.json').read_text())
    upstream=json.loads((root/'preregistration/UPSTREAM_SOURCES.json').read_text())
    if outfile is None:outfile=OUT/'FALSIFIER_REPORT.pdf'
    outfile=Path(outfile);outfile.parent.mkdir(parents=True,exist_ok=True)
    figdir=OUT/'figures';figdir.mkdir(exist_ok=True)
    fig,ax=plt.subplots(figsize=(9,3.5))
    names=list(assess['cases'])
    for name in names:
        row=assess['cases'][name]['same_time_marker_differences']
        ax.plot([28,36],[row[0]['rms_box_length'],row[1]['rms_box_length']],marker='o',label=name)
    ax.set_xticks([28,36],['24 to 32','32 to 40']);ax.set_ylabel('RMS material-marker difference (model length)')
    ax.set_title('Fixed time 2.4, fixed sigma 0.5: spatial refinement');ax.grid(alpha=.25);ax.legend(fontsize=7,loc='upper right')
    fig.tight_layout();fig.savefig(figdir/'spatial_convergence.png',dpi=170);plt.close(fig)
    def pg(s,sty='PaperBodyX'):return Paragraph(s,styles[sty])
    def heading(s):return pg(s,'PaperHeadingX')
    def tabla(arr,widths=None):
        wrapped=[[Paragraph(str(c).replace('&','&amp;'),styles['PaperTableCellX']) for c in row] for row in arr]
        t=Table(wrapped,colWidths=widths,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eaeef4')),
          ('TEXTCOLOR',(0,0),(-1,0),colors.HexColor('#152232')),
          ('LINEBELOW',(0,0),(-1,0),.5,colors.grey),
          ('LINEBELOW',(0,1),(-1,-1),.2,colors.HexColor('#dddddd')),
          ('VALIGN',(0,0),(-1,-1),'TOP'),('FONTSIZE',(0,0),(-1,-1),7.6),
          ('LEADING',(0,0),(-1,-1),11),('FONTNAME',(0,0),(-1,-1),fn),
          ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
          ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
        return t
    story=[]
    story += [pg('SST Topology - Projection - Phase Falsifier v0.3.0','PaperTitleX'),
      pg('Independent geometry-provider census and extended ideal-Euler numerical convergence', 'PaperBodyX'),
      pg('<b>Scientific status:</b> NUMERICAL SCREENING ONLY. No qualified SST mass, gravity, vortex stability or physical reconnection claim.', 'PaperBodyX'),
      heading('Executive result'),
      pg(f'{census["total"]} source configurations were analyzed, containing {census["n_components"]} closed geometric components. '+
       f'{census["status_counts"].get("SCREENING_COMPLETE",0)} passed the finite-resolution geometry screen and '+
       f'{census["status_counts"].get("UNRESOLVED_REFINEMENT",0)} require additional geometry resolution, provenance, or numerical handling. '+
       'A pass is not evidence of dynamically stable matter.'),
      pg('Five selected source geometries were evolved under dimensionless, 3D periodic incompressible Euler at N=24,32,40, to the same final time T=2.4 with a fixed Gaussian core width sigma=0.5. '+
        'All five retain the tested Alexander determinant / linking number over this interval. The corresponding material trajectories show decreasing differences under grid refinement.'),
      pg('For the genuine KnotPlot N300 geometry, halving the RK4 time step at N=32 changes the final traced geometry by 3.22e-7 model length; '+
         'the N32-N40 spatial difference is 2.22e-3. Changing core width to sigma=0.4 or 0.6 changes the final path by 7.87e-2 or 8.49e-2, respectively. '+
         'This model dependence prevents SST physical closure.'),
      heading('Source independence and provenance'),
      tabla([['Source family','Geometries','Interpretation'],
      ['KnotPlot/Ridgerunner N300','1','Actual original N300 centerline, independent geometric provider'],
      ['Fremlin Fourier coefficients','73','One provider; includes multiple model variants'],
      ['Fremlin .short polylines','76','Same provider as Fremlin coefficients; not independent'],
      ['Gilbert IdealLinks','130','Independent Fourier link database, some contacts unresolved']], [150,65,300]),
      Spacer(1,12), pg('Upstream archive SHA-256 values and source URLs are recorded in preregistration/UPSTREAM_SOURCES.json. Original bytes are retained unchanged. '+
      'One .fseries file is empty; short zero-coefficient lines are normalized with an explicit parse rule. Fremlin harmonic indices start at 1, validated on known knot determinants.'),
      PageBreak(), heading('Full geometry-screening census'),
      pg('Screening uses arclength-normalized 96-point curves and three projection directions per knot. Gaussian linking is numerically integrated at quadrature orders 3 and 5, with an independent curve-gap check. '+
         'Alexander determinant |Delta(-1)| is incomplete as a knot identifier (for example some nontrivial knots have determinant 1).'),
      tabla([['Provider','Count','Screen PASS','Needs review']]+[[k,c,sum(r['provider']==k and r['geometry_status']=='SCREENING_COMPLETE' for r in results),sum(r['provider']==k and r['geometry_status']!='SCREENING_COMPLETE' for r in results)] for k,c in census['provider_counts'].items()],[160,80,120,130]),
      Spacer(1,14),pg('Reasons for unresolved rows must be read individually in GEOMETRY_CENSUS.json: near-tangencies, sampling ambiguity, projection degeneracy and bad inputs cannot be collapsed into proof of a physical instability.'),
      heading('Representative topological identities'),
      tabla([['Source','Initial identity','Final identity at T=2.4'],
        ['KnotPlot N300 trefoil','|Delta(-1)| = 3','3'],
        ['Fremlin 3_1','|Delta(-1)| = 3','3'],
        ['Fremlin 4_1','|Delta(-1)| = 5','5'],
        ['Fremlin 7_1','|Delta(-1)| = 7','7'],
        ['IdealLinks L4a1','linking number +2','+2']], [160,160,170]),
      Spacer(1,15), pg('Boundary issue: IdealLinks L2a1 reaches numerical zero separation in the sampled source geometry, and is therefore NOT treated as a validated disjoint Hopf configuration. L4a1 is used as the finite-separation link pilot instead.'),
      PageBreak(),heading('Fixed-time spatial refinement'),
      pg('All comparable simulations use T = 2.4 and sigma = 0.5 in the same 2π-periodic box. RMS differences use the same material-marker indices and shortest periodic displacement.'),
      tabla([['Source','24 vs 32','32 vs 40','Topological screen']]+[
      [name,f'{row["same_time_marker_differences"][0]["rms_box_length"]:.6f}',f'{row["same_time_marker_differences"][1]["rms_box_length"]:.6f}',
         'unchanged' if row['topology_preserved_all_grids'] else 'UNRESOLVED'] for name,row in assess['cases'].items()], [170,100,100,120]),
      Spacer(1,15), Image(str(figdir/'spatial_convergence.png'),width=470,height=184),
      Spacer(1,7),pg('The decreasing pairwise differences support numerical refinement, but do not independently establish an asymptotic order without a fourth spatial resolution, robust field-norm convergence and geometric-remapping error control.', 'PaperSmallX'),
      PageBreak(),heading('N300 temporal refinement, model sensitivity and Kelvin diagnostic'),
      pg('Full KnotPlot N300 material labeling is preserved during Euler integration. The 96-point projection is used only for uniform topological diagnostics; it does not replace the N300 advected markers.'),
      tabla([['Observable','Measured dimensionless value'],
        ['N32 vs N40 path RMS, sigma=0.5','2.2226071e-3'],
        ['N32, dt versus dt/2 path RMS','3.2246705e-7'],
        ['sigma=0.4 versus sigma=0.5 path RMS','7.8685661e-2'],
        ['sigma=0.6 versus sigma=0.5 path RMS','8.4882626e-2'],
        ['Finest N40 material-contour circulation drift','8.2218637e-4']], [295,195]),
      Spacer(1,14),pg('Kelvin circulation is numerically estimated around a 32-marker, initially transverse material loop, evolved with the same trilinear advection as the filament markers. The contour is material, but the underlying interpolation is not independently certified. '+
        'For the KnotPlot N300 run, Kelvin drift decreases from 4.07e-3 (N24) to 1.83e-3 (N32) and 8.22e-4 (N40).'),
      pg('Vorticity/filament tangent agreement on the N300 curve at N32 (mean absolute cosine) is approximately 0.98 initially and 0.97 at T=2.4. '+
        'Strong local alignment supports the interpretation as a vorticity-carrying tube over this interval, but no ridge extraction or material-core stability certification has been performed.'),
      heading('Euler model'),
      pg('The solver evolves projected inviscid incompressible 3D Euler, du/dt = P(u x curl(u)), with 2/3 spectral de-aliasing and explicit RK4 time integration. '+
         'An initial smoothed tangent-vorticity deposit is projected to a solenoidal velocity field. The Gaussian sigma is a model choice, not the canonical SST core radius.'),
      pg('A Kelvin-conserving material line cannot reconnect under smooth ideal Euler flow. Thus topology retention is a positive numerical control, not a discovery of non-ideal reconnection. '+
       'Passive marker lines are not automatically vorticity-ridge centerlines; topology alone does not establish self-confined particles.'),
      PageBreak(),heading('Falsification gates and next release criteria'),
      tabla([['Gate','Observed status','Necessary independent evidence'],
        ['Source-provenance integrity','PASS (file hashes)','Distinct upstream raw geometries'],
        ['Fourier indexing','PASS regression','Known 3_1,4_1,7_1 determinants'],
        ['Cross-source geometric comparison','SCREENED','Independence contract per provider'],
        ['Topology preservation short-to-medium time','SCREENED','Reliable projection and knot/link invariants'],
        ['Same-time grid trajectory refinement','SCREENED','N=24,32,40; next N=48/64'],
        ['RK4 timestep refinement (N300)','SCREENED','N32, dt and dt/2'],
        ['Core-width physical calibration','UNRESOLVED','Core constitutive law independent of fitting'],
        ['Euler field/vorticity convergence','UNRESOLVED','Pointwise cross-grid norm and core-resolving refinement'],
        ['Long-time knotted vortex confinement','UNRESOLVED','Many core turnover times, ridge extraction and perturbations'],
        ['SST dimensional physical closure','UNRESOLVED','Calibrated units and independent measurements'],
        ['Native framework v1.0.7 certification','UNRESOLVED','Create pinned instance; native C++ FP64 and exact reveal gate']], [210,110,180]),
      Spacer(1,11),pg('No implicit PASS escalation is allowed. Source-library census results and five-source Euler tests are separate evidence classes. The optional full-geometry Euler queue is a low-resolution exploratory screen, not a substitute for matched final-time three-grid certification.'),
      heading('Reproducible commands'),
      pg('Windows: run_all.cmd SELFTEST; run_all.cmd CENSUS; run_all.cmd LONG; run_all.cmd ASSESS; run_all.cmd REPORT; run_all.cmd EULER_ALL_SCREEN --max-cases 5. '+
         'For large screening runs omit --max-cases; the queue resumes from JSONL state without duplicating completed runs.'),
      heading('References (copy-ready LaTeX entries)'),
      pg(r'\bibitem{Saffman1993} P. G. Saffman, Vortex Dynamics, Cambridge University Press (1993), doi:10.1017/CBO9780511624063.'),
      pg(r'\bibitem{BerryDennis2000} M. V. Berry and M. R. Dennis, Phase singularities in isotropic random waves, Proc. R. Soc. A 456, 2059-2079 (2000), doi:10.1098/rspa.2000.0602.'),
      pg(r'\bibitem{Bucher2026} T. Bucher et al., Superluminal correlations in ensembles of optical phase singularities, Nature 651, 920-926 (2026), doi:10.1038/s41586-026-10209-z.')]
    def footer(canvas,doc):
        canvas.saveState();canvas.setFont(fn,8)
        canvas.drawString(50,34,'SST Topology-Projection-Phase v0.3.0 | exploratory - no physical SST qualification')
        canvas.drawRightString(560,34,str(doc.page));canvas.restoreState()
    SimpleDocTemplate(str(outfile),pagesize=(595.28,841.89),leftMargin=50,rightMargin=45,topMargin=46,bottomMargin=55,
        title='SST Topology Projection Phase v0.3.0 - Euler convergence and source census').build(story,onFirstPage=footer,onLaterPages=footer)
    return outfile

def frozen_manifest(paths):return {str(p):sha(p) for p in paths}

def archive(path,items,base):
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=8) as z:
        for p in sorted(items):z.write(p,arcname=str(p.relative_to(base)))

def build(root=ROOT):
    out=OUT;out.mkdir(exist_ok=True)
    report=build_pdf(root,out/'FALSIFIER_REPORT.pdf')
    passed=subprocess.run([sys.executable,'-m','pytest','-q'],cwd=root,env={**os.environ,'PYTHONPATH':str(root)},capture_output=True,text=True)
    (out/'SELFTEST.log').write_text(passed.stdout+'\n'+passed.stderr)
    if passed.returncode:raise RuntimeError('Regression failure: '+passed.stdout[-4000:])
    # Include only science results that already ran; do not regenerate or rewrite hidden labels.
    data_files=sorted((root/'results').rglob('*'))
    science=[p for p in data_files if p.is_file() and not any(q in p.parts for q in ('.venv','__pycache__'))]
    ledger={'name':root.name,'status':'UNQUALIFIED_SCIENTIFIC_EULER_SCREEN',
      'upstream_blind_datasets':'unchanged from v0.2 source; no hidden labels revealed',
      'native_framework_v1_0_7':'NOT_RUN_NO_NATIVE_CERTIFICATION',
      'results_file_sha256':frozen_manifest(science),
      'report_pdf_sha256':sha(report),'selftests':passed.stdout.strip(),
      'hash_scope':'only generated report and current science results; no claim of external trusted timestamp or independent seal'}
    (out/'RUN_LEDGER.json').write_text(json.dumps(ledger,indent=2))
    shutilfiles=['GEOMETRY_CENSUS_SUMMARY.json','CONVERGENCE_ASSESSMENT.json','GEOMETRY_CENSUS.csv','GEOMETRY_CENSUS.json']
    import shutil
    for p in shutilfiles:shutil.copy2(root/'results'/p,out/p)
    # All source archive is real, including unchanged encrypted 0.2 truth input;
    # do not include Python bytecode or prior transient output folders.
    sources=[p for p in root.rglob('*') if p.is_file() and not any(x in p.parts for x in ('.venv','.pytest_cache','__pycache__')) and p.suffix!='.pyc']
    srczip=root.parent/(root.name+'_SOURCE_BLIND.zip')
    archive(srczip,sources,root.parent)
    outputzip=root.parent/(root.name+'-outputs_BLIND.zip')
    archive(outputzip,[p for p in out.rglob('*') if p.is_file()]+science,root.parent)
    return {'pdf':str(report),'source':str(srczip),'outputs':str(outputzip),'n_source_files':len(sources),'n_result_files':len(science),'test_output':passed.stdout.strip()}

if __name__=='__main__':print(json.dumps(build(),indent=2))
