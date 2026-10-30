"""Human-readable, evidence-first scientific PDF for each independent run."""
from __future__ import annotations
from pathlib import Path
import html
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_LEFT


def create(path:Path,ledger:dict):
    path=Path(path)
    ss=getSampleStyleSheet()
    ss.add(ParagraphStyle(name='ReportBody',parent=ss['BodyText'],fontName='Helvetica',fontSize=8.75,leading=12,spaceAfter=5))
    ss.add(ParagraphStyle(name='ReportSmall',parent=ss['BodyText'],fontName='Helvetica',fontSize=7.8,leading=10.4,spaceAfter=4))
    ss.add(ParagraphStyle(name='ReportTiny',parent=ss['BodyText'],fontName='Helvetica',fontSize=7.2,leading=9.8,spaceAfter=4))
    pdf=SimpleDocTemplate(str(path),pagesize=A4,leftMargin=42,rightMargin=42,topMargin=37,bottomMargin=47)
    elements=[]
    def paragraph(v,kind='ReportBody'):
        elements.append(Paragraph(html.escape(str(v)),ss[kind]))
    def header(v):paragraph(v,'Heading2')
    def table(rows,rel=None):
        if rel is None: rel=[1/len(rows[0])]*len(rows[0])
        width=A4[0]-84
        data=[[Paragraph(html.escape(str(c)),ss['ReportTiny']) for c in row] for row in rows]
        t=Table(data,colWidths=[width*r for r in rel],repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DCE8F2')),
            ('GRID',(0,0),(-1,-1),.35,colors.HexColor('#AFC2D1')),
            ('VALIGN',(0,0),(-1,-1),'TOP'),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F7F9FA')]),
            ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
        elements.append(t)
    paragraph('Gate2 Ruban Familywise Coupled Falsifier v0.2.1','Title')
    paragraph('Reproducible four-gate research report | DEVELOPMENT | no certified Euler equilibrium','ReportSmall')
    header('Scientific question and hypotheses')
    paragraph('Can a closed finite-core torus knot or torus link, together with initially parallel and fully responsive background vortex tubes, approach a common relative equilibrium of the incompressible three-dimensional Euler equations? The null interpretation is that no such relative equilibrium has been demonstrated by the computed evidence.')
    header('Mathematical target versus computed diagnostics')
    paragraph('A genuine common relative equilibrium requires curl[(u_total - V) cross omega_alpha] = 0 for EACH material vorticity component alpha, a common rigid-motion generator V, an admissible finite-core field, and an independently converging nonzero continuum candidate. This pipeline currently computes a reduced filament screening and a periodic Fourier-Euler pilot, not the full-field nonlinear equilibrium root.')
    paragraph('Normalization: R* = L0^4 / GammaK^2 * RMS(Euler residual); D* = L0^3 / |GammaK| * max(abs(div omega)). The factors refer to the chosen dimensionless length/circulation scales; they are not physical tube diameters.')
    header('Run definition')
    table([['Input','Recorded value'],['Run ID',ledger['run_id']],['Families',', '.join(ledger['family'])],
      ['B0 range','n/a (imported curves)' if not ledger['B0_values'] else str(ledger['B0_values'])],['Lambda values',str(ledger['Lambda_values'])],
      ['G2 filament points',str(ledger['screen_points'])],['G3 promoted geometry points',str(ledger['promotion_points'])]], [.28,.72])
    header('Execution status')
    table([['Gate','Scientific status','Count']]+[[g,ledger['gates'][g]['status'],ledger['gates'][g].get('count','-')] for g in ('G1','G2','G3','G4')],[.1,.73,.17])
    header('G3 candidates — ranking only')
    cands=ledger.get('winners',[])
    table([['Family','B0','Lambda','Score','Spatial eligible?','Holdout rel. drift']]+[
        [w['family'],'n/a' if w['B0'] is None else f"{w['B0']:.4f}",f"{w['Lambda']:.2f}",f"{w['score']:.5f}",
         'yes' if w.get('selected_from_spatial_eligible_candidates') else 'NO',f"{w['holdout_relative_change']:.3g}"]
         for w in cands[:min(len(cands),8)]],[.19,.1,.1,.15,.2,.26])
    if len(cands)>8:paragraph('Further candidates: see G3_FAMILY_WINNERS.csv (machine-readable full ranking).','ReportSmall')
    elements.append(PageBreak())
    paragraph('Scientific interpretation, preflights and provenance','Title')
    header('G1 — Geometry')
    paragraph('Analytical E010 v0.3.6 torus curves are constructed directly. Non-coprime pairs are generated as separate closed components. The generator checks point/segment geometry but has no rigorously certified continuous reach or finite-core tube thickness. KnotPlot link labels are provenance metadata, NOT independent imported coordinates.')
    paragraph('BORRO_* custom link candidates are separately imported from the attached original XYZ/TXT data, with SHA-256 proof of source identity. Their pairwise linking numbers are approximations; Milnor mu123 and full Borromean isotopy remain UNRESOLVED. N>original is resampled polygon geometry, not recovered physical detail.','ReportBody')
    header('G2 — Finite-time reduced filament dynamics')
    g2=ledger['gates']['G2']
    paragraph(f"{g2.get('count',0)} nominal/perturbed filament runs. The score uses the maximum initial rigid-motion residual, finite-time shape drift, and a small perturbation-amplification penalty. The spatial screening heuristic finds {g2.get('spatial_preflight_eligible_pairs',0)} potentially adequately sampled B0/Lambda pairs out of {g2.get('paired_cases',0)}; this does not establish temporal or continuum convergence. High Lambda can make the regularization core far narrower than the line sampling.")
    header('G3 — Independent sampling and internal geometry promotion')
    paragraph('For torus families winners are selected jointly over B0 and Lambda; imported BORRO_* families have no B0 and only Lambda is scanned. Higher-resolution custom seeds use arclength interpolation of original polygons, rather than analytic regeneration.','ReportBody')
    paragraph('The filament score is recomputed at multiple point counts; discrepancies remain UNRESOLVED. Every promoted geometry is hashed; promoted N never certifies Euler convergence. Imported links are interpolated only.')
    header('G4 — Fully coupled Euler pilot')
    paragraph('All live vortex components feed one shared Biot-Savart field. The periodic Gaussian-mollified velocity/vorticity representation is evaluated on a training and a holdout spatial grid, reusing a frozen axial translation U. Continuous axial rotation Omega is not a domain symmetry of a cubic periodic box. The numerical solver currently lacks a full-field nonlinear equilibrium root search.')
    g4=ledger['gates']['G4']
    paragraph(f"G4 runs: {g4.get('count',0)}. Blocked geometrically or spectrally: {g4.get('blocked_count','n/a')}. Source Fourier high-wavenumber filtering above 10%, or small inter-tube clearance, prevents physical promotion. The holdout is a different grid using the same backend, not independent code parity.")
    header('Mandatory scientific stop criteria')
    for v in [
      'Frozen full-field candidate with residual tending to zero under independent spatial refinement: NOT ESTABLISHED.',
      'Spatial plus temporal convergence at a common final physical time: NOT ESTABLISHED.',
      'Material circulation, helicity and knot/link isotopy under 3D evolution: NOT CERTIFIED.',
      'Independent reconstruction/backend and box size/return-limb checks: NOT CERTIFIED.',
      'Nonlinear stability and intrinsic self-confinement: NOT TESTED.',
      'Observed selection on the boundary of B0 or Lambda range: mark a boundary minimum, not an optimum.'
    ]:paragraph('• '+v,'ReportSmall')
    header('Hashes and reproduction')
    paragraph('Analytic E010 v0.3.6 source generator SHA-256: '+ledger['source_generator_sha256'],'ReportSmall')
    paragraph('E010 family config SHA-256: '+ledger['source_config_sha256'],'ReportSmall')
    paragraph('All CLI arguments, dependency fingerprints, per-seed exports, control runs and machine-readable gate decisions accompany the run. See RUN_CONFIG.json, G3_PROMOTED_FILES.json, MANIFEST_SHA256.json and README.md.','ReportSmall')
    header('Final decision')
    paragraph('G2_UNRESOLVED_NO_CERTIFIED_EQUILIBRIUM. A provisional seed is a research starting point, not a demonstrated physically stable configuration.','ReportBody')
    def footer(canvas,doc):
        canvas.saveState();canvas.setFillColor(colors.grey);canvas.setFont('Helvetica',8)
        canvas.drawString(42,28,'Gate2 v0.2.1 | Development only | evidence-first')
        canvas.drawRightString(A4[0]-42,28,'Page '+str(doc.page))
        canvas.restoreState()
    pdf.build(elements,onFirstPage=footer,onLaterPages=footer)
