"""Scientific short report: only describes calculated, not inferred, outcomes."""
import json
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,KeepTogether,PageBreak

def render(out:Path,external_pdf:Path|None=None):
    out=Path(out)
    cfg=json.loads((out/'config.json').read_text())
    result=json.loads((out/'results.json').read_text())
    gates=json.loads((out/'gates.json').read_text())
    src=json.loads((out/'source_manifest.json').read_text())
    path=out/'FALSIFIER_REPORT.pdf'
    doc=SimpleDocTemplate(str(path),pagesize=A4,rightMargin=43,leftMargin=43,
        topMargin=50,bottomMargin=48,title='Ruban T23 reproduction falsifier',author='SST research - automated report')
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='BodyCustom',parent=styles['Normal'],fontName='Helvetica',fontSize=9.3,leading=13,spaceAfter=7))
    styles.add(ParagraphStyle(name='SubtitleCustom',parent=styles['Normal'],fontName='Helvetica',fontSize=10.5,leading=15,textColor=colors.HexColor('#344257'),spaceAfter=12))
    styles.add(ParagraphStyle(name='SmallCustom',parent=styles['Normal'],fontName='Helvetica',fontSize=8,leading=10.4,spaceAfter=5))
    story=[Paragraph('Ruban T(2,3) Reproduction Falsifier',styles['Title']),
      Paragraph(f"Numerical pilot | {cfg['mode']} | v0.1.0 | {src['timestamp_utc']}",styles['SubtitleCustom']),
      Paragraph('SCIENTIFIC STATUS: DEVELOPMENT ONLY - PUBLICATION REPRODUCTION UNRESOLVED',styles['Heading3'])]
    def section(head,content):
        story.append(Paragraph(head,styles['Heading2']))
        story.append(Paragraph(content,styles['BodyCustom']))
    section('1. Claim and experiment',
      'Attempt to reproduce Ruban (2018), Long-lived quantum vortex knots, arXiv:1801.04822, equations (6)-(9), for a trefoil T(2,3). The paper presents a long-lived configuration at B0=0.154, Lambda=1.4+0.5 ln(200), and delta=0.05, with survival beyond t=300 and axial travel above 1200 R0. This package is a filament-only model and makes no full 3D Euler or physical stability claim.')
    section('2. Implemented operator',
      'Normalized R0=1, Gamma=2*pi. Velocity = 0.5 * integral [X_beta(source) cross (X(target)-X(source))] / [(distance)^2+delta^2]^(3/2) d(beta_source) + 0.5*lambda_tilde*kappa*binormal, with lambda_tilde=Lambda+ln(delta). Fourier spectral beta derivatives, periodic trapezoid rule, RK4 time integration. No external forcing, remeshing, smoothing or artificial damping. Delta is a numerical regularization and is distinct from physical core size xi.')
    tabledata=[['Parameter','Actual'],['B0 scan',', '.join(str(x) for x in cfg['b0'])],['Lambda',f"{cfg['Lambda']:.9f}"],
      ['delta/R0',f"{cfg['delta']:.4f}"],['N, dt',f"{cfg['n']}, {cfg['dt']}"],
      ['target t',str(cfg['final_time'])],['initial perturbation',str(cfg['perturb'])]]
    tbl=Table(tabledata,colWidths=[125,375],hAlign='LEFT')
    tbl.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7ecf1')),
      ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('VALIGN',(0,0),(-1,-1),'TOP'),
      ('FONTSIZE',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),6),
      ('LINEBELOW',(0,0),(-1,0),.5,colors.grey)]))
    story.extend([tbl,Spacer(1,10),Paragraph('3. Measured outputs',styles['Heading2'])])
    data=[['B0','t attained','Energy drift','Axial travel','Stop reason']]
    for r in result:
        data.append([f"{r['b0']:.3f}",f"{r['attained_time']:.3f}",f"{r['last']['energy_rel']:.2e}",
                     f"{r['net_z_travel']:.4f}",r['stop_reason']])
    t=Table(data,colWidths=[52,68,86,84,210],repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7ecf1')),
      ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),8),
      ('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),6),
      ('LINEBELOW',(0,0),(-1,0),.5,colors.grey)]))
    story.extend([t,Spacer(1,8),Paragraph('4. Gate ledger',styles['Heading2'])])
    for name,val in gates.items():
        story.append(Paragraph(f'<b>{name}:</b> {val}',styles['SmallCustom']))
    section('5. Interpretation and stop criteria',
      'A PASS for solver symmetry or short-time energy checks is not a PASS for Ruban replication. Only the canonical B0=0.154 case may satisfy the paper-specific lifetime gate. An operational deformation threshold of 0.25 R0, relative energy drift cap of 0.001, and segment-length ratio cap of 10 are new explicit numerical stop criteria, NOT calibrated to the author\'s unpublished lifetime algorithm. Publication-level validation requires independent spatial/time convergence and full-duration integration.')
    section('6. Scope exclusions',
      'No 3D finite-core Euler field, internal core twist, background parallel filaments, exact equilibrium/Floquet analysis, reconnection algorithm or physical clock mechanism is modeled. Filament topology is assumed for smooth evolution only while no collisions/singularities occur. Fixed-grid parameter-space window comparison remains unresolved.')
    section('7. Provenance and citation',
      'V. P. Ruban, Long-Lived Quantum Vortex Knots, JETP Letters 107 (2018), DOI: 10.1134/S0021364018050120; arXiv:1801.04822v2. Extended geometry: Ruban, Quasi-Stable Configurations of Torus Vortex Knots and Links, JETP 127 (2018), DOI: 10.1134/S106377611809008X. E010-v0.4.0 combined atlas used as geometry-only context, not a computed dynamics provider.')
    story.append(Paragraph(f"Config SHA-256: {src['configuration_sha256']}",styles['SmallCustom']))
    def footer(c,d):
        c.setFont('Helvetica',8);c.setFillColor(colors.grey)
        c.drawString(43,30,'Ruban T(2,3) | development-only | no promoted stability claim')
        c.drawRightString(A4[0]-43,30,f'Page {d.page}')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    if external_pdf is not None:
        external_pdf.write_bytes(path.read_bytes())
    return path
