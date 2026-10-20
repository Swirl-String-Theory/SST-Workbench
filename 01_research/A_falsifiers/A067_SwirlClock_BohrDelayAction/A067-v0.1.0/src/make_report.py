"""Standalone (NOT frozen framework) PDF report and scientific figures."""
from __future__ import annotations
import json,math
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak,KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle,getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT=Path(__file__).resolve().parents[1]
O=ROOT/'outputs'
S=json.loads((O/'GATE_RESULTS.json').read_text())
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
if Path(FONT).exists():
    pdfmetrics.registerFont(TTFont('DV',FONT))
    pdfmetrics.registerFont(TTFont('DV-Bold',BOLD))
    FN='DV';FB='DV-Bold'
else: FN='Helvetica';FB='Helvetica-Bold'

plt.figure(figsize=(8.7,3.5))
for c in S['cases']:
    th=np.array(c['branch_theta'])
    ids=np.arange(len(th))
    plt.plot(ids,th/(2*math.pi),marker='o',label=c['case'])
plt.xlabel('Index of selected positive stable branch')
plt.ylabel('Locked frequency / (2pi / delay)')
plt.title('Exact delayed-phase roots: discrete but finite-feedback shifted')
plt.grid(alpha=.25)
plt.legend()
plt.tight_layout()
plt.savefig(O/'branch_roots.png',dpi=165)
plt.close()
plt.figure(figsize=(8.7,3.7))
for c in S['cases']:
    a=np.array(c['harmonic_actions_Js'])
    v=a/a[0]
    plt.plot(range(len(a)),v,marker='o',label=c['case'])
plt.xlabel('Index of selected positive stable branch')
plt.ylabel('Harmonic action divided by first action')
plt.title('Same locked frequencies, different continuous amplitude laws')
plt.grid(alpha=.25)
plt.legend()
plt.tight_layout()
plt.savefig(O/'amplitude_counterexample.png',dpi=165)
plt.close()

styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='DocTitle2',fontName=FB,fontSize=17,leading=22,spaceAfter=13,textColor=colors.HexColor('#172432')))
styles.add(ParagraphStyle(name='Sec2',fontName=FB,fontSize=11.3,leading=15,spaceBefore=11,spaceAfter=6,textColor=colors.HexColor('#172432')))
styles.add(ParagraphStyle(name='Body2',fontName=FN,fontSize=9.0,leading=14,spaceAfter=8))
styles.add(ParagraphStyle(name='Tiny2',fontName=FN,fontSize=7.5,leading=11,spaceAfter=5))
styles.add(ParagraphStyle(name='Eq2',fontName=FN,fontSize=9,leading=16,leftIndent=8,spaceAfter=7))
styles.add(ParagraphStyle(name='Note2',fontName=FN,fontSize=8.5,leading=13,spaceAfter=7,textColor=colors.HexColor('#2F3740')))
P=lambda txt,style='Body2':Paragraph(txt,styles[style])

def page(canvas,doc):
    canvas.setStrokeColor(colors.HexColor('#B7BBC0'));canvas.setLineWidth(.5)
    canvas.line(20*mm,17*mm,190*mm,17*mm)
    canvas.setFont(FN,7);canvas.setFillColor(colors.HexColor('#44515e'))
    canvas.drawString(20*mm,12*mm,'SST Swirl Clock / Bohr-Delay Action - v0.1.0 (development control)')
    canvas.drawRightString(190*mm,12*mm,f'{doc.page}')

def tab(headers,rows,widths=None):
    cells=[[P(str(x),'Tiny2') for x in headers]]+[[P(str(x),'Tiny2') for x in row] for row in rows]
    t=Table(cells,colWidths=widths,hAlign='LEFT',repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#EFF1F3')),
       ('LINEBELOW',(0,0),(-1,0),.8,colors.HexColor('#6A7887')),
       ('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#D5DADD')),
       ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    return t

pdf=ROOT.parent/'SST_SwirlClock_BohrDelayAction_v0.1.0_FALSIFIER_REPORT.pdf'
doc=SimpleDocTemplate(str(pdf),pagesize=(210*mm,297*mm),leftMargin=20*mm,rightMargin=20*mm,topMargin=20*mm,bottomMargin=23*mm,metadata={'title':'SST Swirl Clock - Bohr Delay Action Falsifier v0.1.0'})
flow=[]
flow.append(P('Swirl Clock: Bohr-Delay Action Closure','DocTitle2'))
flow.append(P('<b>Research tranche v0.1.0 - 16 October 2026</b><br/>Standalone Python reference; targeted to frozen SST Falsifier Framework v1.0.7. NOT a framework FULL/CERTIFY run.'))
flow.append(P('Executive status','Sec2'))
flow.append(P('<b>Scientific verdict: UNRESOLVED.</b> Three anonymized SHA256-sealed control files were executed. 7/7 implementation-control gates passed, while 3/3 physical closure gates remain unresolved. All three datasets are SYNTHETIC CONTROLS, not independent PKLSA evidence.'))
flow.append(tab(['Gate group','Observed outcome','Scientific authority'],[
    ('G0-G2','Hashes, harmonic action, SST-60 roots: PASS_CONTROL','Implementation only'),
    ('G3-G6','Delay integration, amplitude null and Euler scaling: PASS_CONTROL','Implementation only'),
    ('G7-G9','3D phase/clock, 3D canonical action, universal action step: UNRESOLVED','No physical assertion')],[38*mm,78*mm,54*mm]))
flow.append(P('What the falsifier actually asks','Sec2'))
flow.append(P('Can an unforced incompressible Euler vortex support a reproducible operational phase clock relative to global evolution T, generate its feedback lag from resolved transport, select stable modes and produce a canonical action ladder without entering the desired action quantum as an input?'))
flow.append(P('Required separation of three claims','Sec2'))
flow.append(P('1. <b>Clock:</b> intrinsic carrier phase phi_K(T) and clock rate d(tau_clock,K)/dT. 2. <b>Frequency:</b> a physical delay/feedback reduction yielding stable frequency branches. 3. <b>Action:</b> a physical symplectic projection with J = closed integral of p dq, then blind comparison with the universal target. Phase/frequency agreement cannot replace action certification.'))
flow.append(P('Core equations and dimensional checks','Sec2'))
flow.append(P('d phi/dT = Omega0 + K sin[phi(T - delay) - phi(T)];  Omega = Omega0 - K sin(Omega delay).','Eq2'))
flow.append(P('lambda = A[exp(-lambda delay) - 1],  A = K cos(Omega delay).  Stable sufficient: A &gt; 0. Unstable sufficient: A * delay &lt; -1.','Eq2'))
flow.append(P('Rotor hypothesis: J = 2 pi I Omega. Harmonic generalized coordinate: J = pi M Omega a^2. Both have units J*s; neither is a derived 3D vortex canonical action.','Eq2'))
flow.append(P('Exact finite-feedback roots; long-delay mode selection','Sec2'))
flow.append(Image(str(O/'branch_roots.png'),width=163*mm,height=65.6*mm))
flow.append(P('Negative control: frequency selection is not action selection','DocTitle2'))
flow.append(P('All three controls use the <b>same</b> phase-locking parameters (beta = 40, theta0 = 6 pi) and identical rotor inertia. The anonymized files carry different harmonic amplitude sequences. Hence their frequency branches agree while the harmonic actions J = pi M Omega a^2 need not form the same regular ladder. This is a deliberate test of false-positive scientific interpretation.'))
flow.append(Image(str(O/'amplitude_counterexample.png'),width=163*mm,height=69.5*mm))
flow.append(P('Source-level metrics','Sec2'))
rows=[]
for c in S['cases']:
    rows.append((c['case'],str(c['stable_roots_total']),f"{c['rotor_gap_cv']:.5f}",f"{c['harmonic_gap_cv']:.5f}"))
flow.append(tab(['Anonymized control','Stable positive roots','Rotor gap CV','Harmonic gap CV'],rows,[46*mm,43*mm,41*mm,40*mm]))
flow.append(P('The three controls do NOT constitute statistically independent physical confirmations. Their purpose is to certify the analysis cannot infer action quantization from frequency discreteness alone. No Planck target enters these code paths.','Note2'))
flow.append(P('Euler continuous-scaling null','Sec2'))
flow.append(P('For constant density, ideal Euler admits u_sigma(x,T) = sigma*u(x,sigma*T), P_sigma(x,T) = sigma^2*P(x,sigma*T). For a fixed-mass same-path kinetic action, J_sigma = sigma*J. Thus unforced ideal Euler by itself does not exclude continuously variable action. The full SST model needs an independently derived additional mechanism.'))
flow.append(P('External 3D source considered','Sec2'))
flow.append(P('Grounded Drive source: A064 trefoil CANDIDATE_SURFACE.npz (2,056 vertices; 4,108 triangles), SHA256 9f745ebd...56d108. This is a geometric surface, not time-resolved phase and momentum data. The associated A064 Euler source audit records conditional evolution but lists spatial and temporal convergence as unresolved. It cannot support G7-G9.'))
flow.append(P('Preregistered physical closure gates','DocTitle2'))
flow.append(tab(['Gate','Required source evidence','Stop/qualification condition'],[
    ('G7','Qualified Euler flow trajectories at 3+ spatial and temporal resolutions; phase and delay from same flow','No time-resolved carrier signal => UNRESOLVED; no projection-only inference'),
    ('G8','Canonical symplectic reduction, gauge/reparametrization checks and actual action integral','No physical canonical momentum => UNRESOLVED; 3-resolution < 1% required'),
    ('G9','At least 3 adjacent modes in 2 independent source groups, blind target comparison','No calibrated h, electron mass, clock rate or hidden circular target in discovery'),
],[17*mm,80*mm,73*mm]))
flow.append(P('Next execution tranche','Sec2'))
flow.append(P('1. Obtain the full accepted 3D Euler flow time series for a real PKLSA trefoil or reconstruct a reproducible one from the qualified solver.<br/>2. Extract an intrinsic carrier phase from a preregistered material observable and measure return-time spectrum with separation of phase, projection and advection.<br/>3. Derive reduced symplectic 2-form and canonical momentum, then integrate action over true recurrent modes.<br/>4. Run the same analysis on a ring and a distinct independent knot provider, and reveal the action target only after signed preconditions are satisfied.'))
flow.append(P('References and provenance','Sec2'))
flow.append(P('A. Sommerfeld (1916), Annalen der Physik 356, 1-94, doi:10.1002/andp.19163561702.','Tiny2'))
flow.append(P('J. E. Marsden and A. Weinstein (1983), Physica D 7, 305-323, doi:10.1016/0167-2789(83)90134-3.','Tiny2'))
flow.append(P('O. Iskandarani (2026), SST-55, doi:10.5281/zenodo.20023016; SST-60, doi:10.5281/zenodo.18810431; SST-72.','Tiny2'))
flow.append(P('Canonical frozen framework v1.0.7: Drive folder 1IASDEqmcEQXHyTfppetIGgYnVUsvN5hE. Workbench A059 v0.2.0 and A064 3D source audits checked; no target registry ID reserved for this add-on.','Tiny2'))
flow.append(P('Audit statement','Sec2'))
flow.append(P('Self-contained Python implementation of synthetic controls; separate official framework integration required before production claims or native CPU/GPU certifications. No fabricated framework ledger or physical PASS issued.'))

doc.build(flow,onFirstPage=page,onLaterPages=page)
print(pdf)
