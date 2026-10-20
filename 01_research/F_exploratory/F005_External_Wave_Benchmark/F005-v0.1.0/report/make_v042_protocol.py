from pathlib import Path
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,KeepTogether,PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.units import mm

OUT=Path(__file__).parent/'F005_v0.4.1_Review_and_v0.4.2_Qualification_Protocol.pdf'
NAVY=colors.HexColor('#102940');TEAL=colors.HexColor('#14788a');GRAY=colors.HexColor('#596574')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='FTitle',parent=styles['Title'],fontSize=18,leading=24,alignment=TA_LEFT,textColor=NAVY,spaceAfter=10))
styles.add(ParagraphStyle(name='FSub',parent=styles['Heading2'],fontSize=11.5,leading=15,textColor=TEAL,spaceBefore=14,spaceAfter=7))
styles.add(ParagraphStyle(name='FBody',parent=styles['Normal'],fontSize=9.1,leading=13.1,spaceAfter=8,textColor=NAVY))
styles.add(ParagraphStyle(name='FSmall',parent=styles['Normal'],fontSize=8.1,leading=11,textColor=GRAY,spaceAfter=8))
doc=SimpleDocTemplate(str(OUT),pagesize=(210*mm,297*mm),rightMargin=17*mm,leftMargin=17*mm,topMargin=17*mm,bottomMargin=18*mm,title='F005 0.4.2 Qualification Protocol')
story=[]
def h(text):story.append(Paragraph(text,styles['FSub']))
def p(text):story.append(Paragraph(text,styles['FBody']))
def tbl(rows,widths):
    t=Table([[Paragraph(str(v),styles['FSmall']) for v in row] for row in rows],colWidths=widths,hAlign='LEFT',repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#EDF3F6')),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#D7E0E6')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
    story.append(t)

story.append(Paragraph('F005 | External wave-data benchmark',styles['FTitle']))
p('<b>v0.4.2 qualification protocol</b>  -  20 October 2026  -  DEVELOPMENT / NON-BLIND')
p('Purpose: qualify conditional multistep predictive performance and audit waveform-family overlap, while preserving the existing candidate split, prior releases, source archives, and TEST/OOD elevation secrecy.')
h('1. Locked factual starting point: v0.4.1')
tbl([['Measure','v0.4.1 recorded result'],['Validation trajectories','750'],['Anchors','0.004, 1.5, 2.8 s'],['Horizons','0.1, 0.5, 1.0, 2.0, 3.0 s'],['ARX, 1.5 s anchor, 3 s endpoint','0.778 mm RMSE'],['Persistence, same endpoint','3.625 mm RMSE'],['Generated input-shape pairs / scored','75,181 / 15,000'],['Near-shape cross-partition pairs in scored subset','4,800'],['Certification','NOT BLIND; PKLSA/Euler NOT RUN']],[69*mm,105*mm])
p('<b>Scope warning:</b> the v0.4.1 RMSE figures are errors at selected forecast endpoints, not the average across the entire predicted path. The earlier endpoint win does not establish a full-path win against a zero-equilibrium baseline.')
h('2. Exact v0.4.2 implementation commitments')
tbl([['Gate','Qualification action / limit'],
     ['P5c','Score all generated input-fingerprint candidate pairs with same normalized cross-correlation criteria, without 15,000 cap. Not an exhaustive all-pairs or source-family audit.'],
     ['P6d','Report endpoint and full-path RMSE at all anchors/horizons; no water-height teacher forcing within horizon.'],
     ['P6e','Benchmark ARX against persistence, linear extrapolation, zero equilibrium and unforced damped oscillator. Oscillator parameters derive from TRAIN-only ARX.'],
     ['P6f','Descriptive phase/amplitude at locked ARX frequency, with minimum-amplitude threshold.'],
     ['P6g','Report candidate-linked VAL-TRAIN overlap and screen-negative validation sensitivity; original split unchanged.']],[24*mm,150*mm])
story.append(PageBreak())
story.append(Paragraph('Reproducibility, controls and next gate',styles['FTitle']))
h('3. Dimensional contract and prediction recurrence')
p('The experiment reports acceleration in m/s<super>2</super> and elevation in mm. Prediction calculations convert elevation to m. With dt = 0.004 s:')
p('<font face="Courier">eta[n+1] = A*eta[n] + B*eta[n-1] + C*dt^2*a[n]</font>')
p('Locked TRAIN-only model: A=1.985666104, B=-0.990869642, C=-1.118156918. Two measured heights are used only at each predeclared origin; the future acceleration remains known as exogenous input.')
p('<b>Path error:</b> RMSE computed over every trajectory and every intermediate timestep up to the horizon. <b>Endpoint error:</b> RMSE computed only at the horizon endpoint. Both are reported in mm.')
h('4. Separation of data and interpretation')
tbl([['Allowed','Forbidden'],
     ['Read all acceleration trajectories (input-only screening).','Read TEST/OOD water-height trajectories or compute their metrics.'],
     ['Read VALIDATION heights for fixed predeclared metrics.','Retrain or tune the frozen ARX on validation labels.'],
     ['Score all proposed input-shape pairs.','Claim complete all-pairs coverage or publisher-family independence.'],
     ['Fit nothing new; use locked TRAIN-derived oscillator controls.','Promote an oscillator/control to independent Euler or PKLSA validation.']],[85*mm,89*mm])
h('5. Expected local outputs')
p('Within <font face="Courier">outputs/f005_qualification_v0.4.2/</font>: JSON provenance report, summary Markdown, horizon-metrics CSV, matched-family edges, full input-shape component assignment CSV, input-screen-negative validation sensitivity CSV, phase/amplitude CSV, sample trajectories, and a generated PDF.')
h('6. Qualification decision')
p('<b>P5c:</b> REVIEW until source-defined family IDs or independently justified complete family mapping is available. <b>P6d/e:</b> descriptive/conditional development validation only, even if path RMSE improves. <b>P6g:</b> group-disjoint certification BLOCKED; TEST/OOD remain sealed. <b>P7:</b> PKLSA NOT RUN. <b>P8:</b> SST physical claims UNRESOLVED.')
p('<b>References:</b> Giulietti et al. (2026), Robot-executed sloshing dataset, Zenodo DOI: 10.5281/zenodo.20039757. Ljung (1999), System Identification: Theory for the User, 2nd ed., Prentice Hall, ISBN 9780136566953.')

def draw_footer(canvas,doc):
    canvas.setStrokeColor(colors.HexColor('#D7E0E6'));canvas.line(17*mm,15*mm,193*mm,15*mm)
    canvas.setFont('Helvetica',7.5);canvas.setFillColor(GRAY)
    canvas.drawString(17*mm,11*mm,'F005 v0.4.2 - protocol; NO real v0.4.2 measurement results in this document')
    canvas.drawRightString(193*mm,11*mm,f'{doc.page}')

doc.build(story,onFirstPage=draw_footer,onLaterPages=draw_footer)
print(OUT)
