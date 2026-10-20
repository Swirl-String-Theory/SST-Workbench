"""Create an explicitly non-certified technical report using local diagnostic JSON."""
from pathlib import Path
import json,hashlib
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
root=Path(__file__).resolve().parent
out=root/'A069_v0.6.1_DEVELOPMENT_REPORT.pdf'
ss=getSampleStyleSheet();ss.add(ParagraphStyle(name='MainTitle',parent=ss['Title'],fontName='Helvetica-Bold',fontSize=19,leading=23,textColor=colors.HexColor('#17324d'),spaceAfter=12));ss.add(ParagraphStyle(name='Sub',parent=ss['Normal'],fontSize=9,leading=13,textColor=colors.HexColor('#555e65'),spaceAfter=16));ss.add(ParagraphStyle(name='SectionX',parent=ss['Heading2'],fontSize=12,leading=16,textColor=colors.HexColor('#17324d'),spaceBefore=10,spaceAfter=6));ss.add(ParagraphStyle(name='BodyX',parent=ss['BodyText'],fontSize=9,leading=14,spaceAfter=7));ss.add(ParagraphStyle(name='SmallX',parent=ss['Normal'],fontSize=7.8,leading=10.8));
S=[]
def p(t):S.append(Paragraph(t,ss['BodyX']))
def h(t):S.append(Paragraph(t,ss['SectionX']))
def table(rows,widths=None):
    v=Table([[Paragraph(str(c),ss['SmallX']) for c in row] for row in rows],colWidths=widths,hAlign='LEFT',repeatRows=1)
    v.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#edf2f5')),('LINEBELOW',(0,0),(-1,0),.7,colors.HexColor('#cad3dc')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f7f9fb')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));S.append(v);S.append(Spacer(1,9))
S.append(Paragraph('A069 v0.6.1',ss['MainTitle']))
S.append(Paragraph('Core separation &amp; subgrid vortex-line tracking repair | 19 October 2026 | DEVELOPMENT - NOT FROZEN, NOT CERTIFIED',ss['Sub']))
h('Abstract')
p('A069 v0.6.1 repairs two distinct weaknesses in v0.5.0/v0.6.0: the use of lattice-face centers as vortex-line positions and the absence of a strict core-separation plus mesh-resolution admission gate. We introduce bilinear complex-field zeros for each wound plaquette, oriented dual-graph polylines and subcell Fourier-grid offsets. The previous GP evolution code remains byte-pinned and unmodified. These are numerical diagnosis improvements, not validation of a stable particle knot or Swirl Clock.')
h('Scientific and model scope')
p('The simulated medium solves the dimensionless, compressible Gross-Pitaevskii equation. It is neither a resolved incompressible Euler trefoil nor a physical atomic clock. The historical Fourier A and Torus B curves are geometry inputs. No golden-ratio, Compton, Lorentz, particle-mass or desired clock-frequency calibration is used.')
h('Method and fail-closed readiness')
p('The scanner evaluates nearby, nonadjacent line-segment pairs while excluding 7% of the periodic parameterized arclength neighborhood. Its distance is a numerical nonlocal screening diagnostic - not mathematically certified reach or physical core thickness. We reject readiness if the GP core has fewer than four grid cells per xi, if xi / screened nonlocal gap exceeds 0.30, or if xi times maximum discrete centerline curvature exceeds 0.30. Thresholds are preregistration proposals for a future production campaign, not universal laws.')
p('A face carrying integer circulation is localized by solving both Re(Psi)=0 and Im(Psi)=0 in the bilinear interpolated plaquette. Zeros on shared face edges are marked boundary-degenerate rather than falsely connected into unique lines. The face crossing points are connected through a dual graph only when each node has one incoming and one outgoing link. This is a geometry diagnostic and not a knot invariant or ambient-isotopy certificate.')
h('Local numerical results (executed)')
rows=[['GP case','Gap d','xi/d','xi kmax','xi/dx','Pre / post graph','G32']]
for name in ['A_N32_v061.json','B_N32_v061.json','B_N48_v061.json']:
    q=json.loads((root/'results'/name).read_text());r=q['readiness'];d=q['geometry']['approx_min_nonlocal_segment_distance'];g=q['initial'];f=q['final'];rows.append([name.replace('_v061.json',''),f'{d:.3f}' if d else 'n/a',f"{r['xi_to_nonlocal_gap']:.3f}" if r['xi_to_nonlocal_gap'] is not None else 'n/a',f"{r['xi_times_kmax']:.3f}",f"{r['cells_per_xi']:.2f}",f"{g['components_count']} / {f['components_count']}",'FAIL'])
table(rows,[89,54,52,63,60,92,48])
p('All three quick preflights use xi=0.42, box=10, dt=0.006 and only eight time steps. They deliberately fail the core/grid qualification conditions. Initial/final component counts are not reconnection events.')
h('Decisive aliasing negative control')
q=json.loads((root/'results'/'B_N48_v061.json').read_text())
p('For B on 48^3, the SAME INITIAL GP FIELD, before physical time evolution, yields different dual-graph component counts under two subcell Fourier translations: ' + ', '.join(f"offset {t['shift_cells']} -> {t['components']} components" for t in q['initial_subcell_grid_offsets']) + '. As there is zero elapsed GP time, the disagreement is incontrovertibly an extraction/grid-alignment effect rather than a dynamical reconnection. This specifically invalidates topology promotion from component count alone.')
h('Results and epistemic gates')
table([['Gate','Executed result','Permitted statement'],['G32 core/readiness','FAIL (all 3 preflights)','No dynamics qualification'],['G33 subgrid zeros','Mixed geometric diagnostics','Software localization implemented'],['G34 knot class and topology transport','UNRESOLVED','No reconnection determination'],['G35 independent intrinsic eigenmode','UNRESOLVED','No Swirl Clock frequency']],[106,150,200])
p('There are 23 passing local regression tests (9 inherited v0.6.0 and 14 new). Neither an official v1.0.9 FREEZE/BASIC nor any native Arc A770 backends or source-independent physics holdout has been executed for v0.6.1.')
h('Next production qualification')
p('A useful candidate is B with xi=0.28 and box=10, requiring at least approximately N=143 for >=4 cells/xi, before additional domain, dx, dt, core and phase-alignment sweeps. This candidate is NOT already validated. Fourier A at the measured 0.284 nonlocal gap would require xi no greater than approximately 0.085 under the same ratio rule, implying N roughly 470 at box=10. Memory pressure and physical core overlap must therefore be handled explicitly. If a knot reconnects in fully converged GP, record that negative result; never repair it by post-hoc parameter selection.')
h('Provenance and limitations')
p('Pinned upstream public v0.5.0 ZIP SHA-256: bb8e1d392e3e72c0c2caee22df406469f9f3de5504296da45cedc6fda8d04b6e. All outputs remain DEVELOPMENT; source hashes and executable diagnostics are included in the accompanying ZIP. Old KnotPlot-relaxed geometry is excluded. The two historical trefoils and mirrors are not independent physical providers.')
def footer(canv,doc):
    canv.setFont('Helvetica',7.5);canv.setFillColor(colors.grey)
    canv.drawString(40,28,'A069 v0.6.1 - DEVELOPMENT ONLY | SST-Workbench')
    canv.drawRightString(A4[0]-40,28,str(doc.page))
doc=SimpleDocTemplate(str(out),pagesize=A4,rightMargin=40,leftMargin=40,topMargin=40,bottomMargin=45,title='A069 v0.6.1 Development Report',author='A069 numerical development')
doc.build(S,onFirstPage=footer,onLaterPages=footer)
print(out)
