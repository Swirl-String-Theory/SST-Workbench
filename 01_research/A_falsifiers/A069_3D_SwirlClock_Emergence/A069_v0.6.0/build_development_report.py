from pathlib import Path
import json
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,KeepTogether,PageBreak
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.colors import HexColor,white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT=Path(__file__).parent
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONTB='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
pdfmetrics.registerFont(TTFont('DV',FONT));pdfmetrics.registerFont(TTFont('DVB',FONTB))
style=getSampleStyleSheet()
style.add(ParagraphStyle(name='HeaderDV',fontName='DVB',fontSize=15,leading=21,spaceAfter=10,textColor=HexColor('#123145')))
style.add(ParagraphStyle(name='SubDV',fontName='DVB',fontSize=10.5,leading=14,spaceBefore=11,spaceAfter=6,textColor=HexColor('#123145')))
style.add(ParagraphStyle(name='BodyDV',fontName='DV',fontSize=8.4,leading=12,spaceAfter=7))
style.add(ParagraphStyle(name='SmallDV',fontName='DV',fontSize=7.6,leading=10.3))
style.add(ParagraphStyle(name='TagDV',fontName='DVB',fontSize=8,leading=12,textColor=HexColor('#99531a')))
class HeaderDoc(SimpleDocTemplate):pass
out=ROOT/'A069_v0.6.0_DEVELOPMENT_REPORT.pdf'
doc=SimpleDocTemplate(str(out),pagesize=A4,leftMargin=49,rightMargin=49,topMargin=42,bottomMargin=48,title='A069 v0.6.0 - 3D vortex tracking development',author='SST-Workbench — development test')
story=[]
P=lambda text,typ='BodyDV':Paragraph(text,style[typ])
story.append(P('A069 v0.6.0 — 3D GP Vortex-Line Tracking','HeaderDV'))
story.append(P('DEVELOPMENT · NOT FROZEN · NOT CERTIFIED · 19 October 2026','TagDV'))
story.append(Spacer(1,10))
story.append(P('Purpose','SubDV'))
story.append(P('Extend A069 v0.5.0 with discrete, oriented vortex-line tracking from <b>actual three-dimensional Gross–Pitaevskii fields</b>. This is a conservative step toward continuous trefoil topology and internal-mode analysis. It is not a new official v1.0.9 framework run and does not change any v0.5.0 science evidence.'))
story.append(P('Numerical method','SubDV'))
story.append(P('For each oriented XY, YZ and ZX lattice plaquette, compute 2π phase winding from the complex field link phases. Construct the dual oriented graph and record per-vertex incoming/outgoing degree, graph components, simple cycles, and periodic homology. The algorithm rejects exact-zero grid vertices and multi-quantum plaquettes. Closed graph cycles are <b>not</b> proofs of trefoil isotopy; moving lattice edges are <b>not</b> proof of a physical reconnection.'))
story.append(P('New regression controls','SubDV'))
story.append(P('9/9 PASS: trivial field, four exact periodic straight vortex lines, two synthetic vortex rings, global U(1) phase invariance, circulation orientation reversal under complex conjugation, discrete translations, and fail-closed scientific interpretation.'))
story.append(P('Short genuine 3D GP knot runs','SubDV'))
results=['v060_GP_A_N24_preflight.json','v060_GP_A_N32_preflight.json','v060_GP_A_N48_preflight.json','v060_GP_B_N32_preflight.json']
rows=[['Seed','Grid','Initial components / defects','Final components / defects']]
for nm in results:
 j=json.loads((ROOT/'results'/nm).read_text());init=j['initial_graph'];fin=j['final_graph'];rows.append([j['kind'],str(j['n'])+'³',f"{init['component_count']} / {init['junction_or_orientation_defects']}",f"{fin['component_count']} / {fin['junction_or_orientation_defects']}"])
t=Table(rows,colWidths=[55,55,178,175],rowHeights=23)
t.setStyle(TableStyle([('FONTNAME',(0,0),(-1,0),'DVB'),('FONTNAME',(0,1),(-1,-1),'DV'),('FONTSIZE',(0,0),(-1,-1),8),('BACKGROUND',(0,0),(-1,0),HexColor('#e7edf2')),('LINEBELOW',(0,0),(-1,0),0.8,HexColor('#627e90')),('ROWBACKGROUNDS',(0,1),(-1,-1),[white,HexColor('#f8fafb')]),('LEFTPADDING',(0,0),(-1,-1),8),('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
story.append(t);story.append(Spacer(1,10))
story.append(P('All four runs use dimensionless GP model, dt=0.006, 8 time steps (T=0.048). The vortex-graph defects and even the number of components change with resolution for seed A. This <b>blocks physical topology certification</b>; it does not establish reconnection. Seed B passes a short graph consistency check only, not long-time knot preservation.'))
story.append(P('Science gate outcomes','SubDV'))
for t in [
'<b>G25</b> voxel and subcell centerline convergence — NOT QUALIFIED; A has resolution-sensitive graph complexity.',
'<b>G26</b> 3D knot invariants / contact gate — UNRESOLVED (no certified ambient-isotopy invariant).',
'<b>G27</b> continuous reconnection event classifier with dt/dx convergence — UNRESOLVED.',
'<b>G28</b> symmetry-reduced relative periodic orbit — UNRESOLVED.',
'<b>G29</b> intrinsic frequency/Floquet held-out prediction — UNRESOLVED.',
'<b>G30</b> independent qualified PKLSA physics and A061 handoff — UNRESOLVED.']:
 story.append(P(t,'SmallDV'))
story.append(P('No homogenous GP bulk Bogoliubov frequency, density-shape oscillation or tracer angle is accepted as a 3D trefoil clock. No golden-ratio or mass-fit inputs are used.'))
story.append(P('Reproduction and next physical threshold','SubDV'))
story.append(P('Run <b>python -m pytest -q tests</b>. To reproduce knot diagnostics, supply <b>--v05-instance &lt;path to A069-v0.5.0&gt;</b> to run_v060_tracking.py (see README). Next version must reconstruct sub-grid continuous vortex zero curves, independently identify knot type and follow them at fixed physical times across grid, timestep and core-size sweeps. Only then attempt relative equilibrium, true Floquet monodromy and a blinded internal-mode prediction.'))
doc.build(story)
print(out)
