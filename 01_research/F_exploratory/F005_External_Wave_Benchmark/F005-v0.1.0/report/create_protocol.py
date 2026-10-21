from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,KeepTogether
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.colors import HexColor
from pathlib import Path

path=Path(__file__).resolve().parent/'F005_v0.4.3_Qualification_Protocol.pdf'
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='Hero',parent=styles['Title'],fontName='Helvetica-Bold',fontSize=18,leading=22,textColor=HexColor('#182c43'),spaceAfter=11))
styles.add(ParagraphStyle(name='SectionA',parent=styles['Heading2'],fontSize=12,leading=15,textColor=HexColor('#182c43'),spaceBefore=13,spaceAfter=6))
styles.add(ParagraphStyle(name='SmallA',parent=styles['Normal'],fontSize=9.1,leading=13,spaceAfter=6))
styles.add(ParagraphStyle(name='TinyA',parent=styles['Normal'],fontSize=8,leading=11))
styles.add(ParagraphStyle(name='Sub',parent=styles['Normal'],fontSize=9,leading=12,textColor=HexColor('#5b6677'),spaceAfter=12))
doc=SimpleDocTemplate(str(path),pagesize=A4,rightMargin=44,leftMargin=44,topMargin=47,bottomMargin=44)
P=lambda s:Paragraph(s,styles['SmallA'])
H=lambda s:Paragraph(s,styles['SectionA'])
C=lambda s:Paragraph(s,styles['TinyA'])
story=[Paragraph('F005 v0.4.3 | Qualification Protocol',styles['Hero']),Paragraph('Family-disjoint development validation and independently trained oscillator | 20 October 2026',styles['Sub'])]
story += [H('Purpose and status'),P('Evaluate whether an independently <b>retrained</b> ARX model predicts sloshing responses on input-proxy-disjoint development groups, and compare it to a separately fitted, damped, driven oscillator. <b>No blind family-independence certification, Euler closure, PKLSA simulation, or physical SST claim is made.</b>')]
rows=[['Audit gate','Contract and outcome'],
      ['P5d','Rebuild a TRAIN / VALIDATION split on connected input-shape components; preserve original TEST/OOD response seals.'],
      ['P6h','Re-estimate ARX(2) from the new TRAIN-only responses; evaluate recursive free-run on new development VALIDATION.'],
      ['P6i','Identify oscillator frequency and damping from quiet TRAIN ringdown windows; calibrate force coupling from TRAIN.'],
      ['P7 / P8','Not run / unresolved. No Euler- or PKLSA-derived independent wave prediction.']]
t=Table([[C(str(x)) for x in row] for row in rows],colWidths=[78,427],repeatRows=1,hAlign='LEFT')
t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#e8eef4')),('GRID',(0,0),(-1,-1),.4,HexColor('#cbd5df')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),9)]))
story+=[t,H('Provenance and independence'),P('Robot-sloshing data: 9,822 x 1,500 observations; 250 Hz. Original STANDARD_TRAIN (3,500) and STANDARD_VALIDATION (750) are explicitly declared a <b>reused development cohort</b> because both have already been analyzed. The original TEST (750) and OPTIMIZED_OOD (4,822) response trajectories remain sealed.'),P('The split is a partition of the connected components of the v0.4.2 accepted input near-match graph. All 75,181 generated candidates were scored previously, producing 36,081 accepted edges, but candidate generation was non-exhaustive. A graph-disjoint partition is therefore <b>not proof of real waveform-family independence</b>.')]
story+=[H('Predeclared measurements'),P('At t0 = 0.004, 1.5, 2.8 seconds, initialize with two measured heights. Predict H = 0.1, 0.5, 1, 2, 3 seconds using recursive simulated heights and known future acceleration. Measure both entire-path RMSE and final-point RMSE, each in millimetres. Include persistence, zero response, linear extrapolation and separately trained driven oscillator. Bootstrap entire detected proxy groups, not individual trajectories.')]
story.append(PageBreak())
story +=[Paragraph('Qualification gates & technical safeguards',styles['Hero']),H('Distinct numerical estimators'),P('<b>ARX(2):</b> eta[n+1] = A eta[n] + B eta[n-1] + C a[n] dt^2. Fit via TRAIN-only regularized second-difference regression. The previous v0.3 parameters are deliberately not reused for fitting.'),P('<b>Independent oscillator:</b> d^2 eta/dt^2 + 2 gamma d eta/dt + omega0^2 eta = K a(t). Estimate gamma and omega0 using low-input TRAIN ringdown segments and estimate K separately on TRAIN. This tests an independently fitted <i>reduced model</i>, not an Euler PDE prediction.')]
story += [H('Fail-closed conditions'),P('Abort on changed input hash, inconsistent v0.4.2 candidate count, altered split identity, edge-score inconsistency, cross-component split overlap, nonfinite source inputs, or direct access to original TEST/OOD elevations. If TRAIN ARX poles are unstable, withhold forecast qualification. If oscillator ringdown samples are insufficient or parameters are nonphysical, publish BLOCKED for the oscillator rather than substituting former ARX poles.')]
story += [H('Output artifacts'),P('v043_report.json; V043_SUMMARY.md; proxy_family_development_split.csv; validation_full_path_metrics.csv; fixed_development_trace_sample.csv; and F005_v0.4.3_DEVELOPMENT_REPORT.pdf, all under outputs/f005_family_disjoint_v0.4.3/. The source ZIPs and v0.4.2 outputs are not changed.')]
story += [H('Scientific boundaries'),P('Positive validation scores indicate predictive utility within a previously observed, input-proxy-repartitioned development population. They do not establish independent-source reproducibility, true Euler dynamics, Kelvin waves, inertial waves, SST vortex-clock physics, or fundamental gravity claims.')]
story += [H('References'),P('Giulietti et al. (2026), <i>Robot-executed sloshing dataset</i>, Zenodo, DOI: 10.5281/zenodo.20039757.'),P('L. Ljung (1999), <i>System Identification: Theory for the User</i>, 2nd ed., Prentice Hall, ISBN 9780136566953.')]
def footer(canvas,doc):
    canvas.setFont('Helvetica',8);canvas.setFillColor(HexColor('#65758b'))
    canvas.drawString(44,28,'F005 v0.4.3 | DEVELOPMENT / NON-BLIND')
    canvas.drawRightString(A4[0]-44,28,f'Page {doc.page}')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(path)
