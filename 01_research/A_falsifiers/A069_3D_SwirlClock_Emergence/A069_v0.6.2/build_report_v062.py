"""Generate a deterministic DEVELOPMENT report, not a framework-certified PDF."""
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from a069_v061.campaign_v062 import CASES,screening,resource_forecast

ROOT=Path(__file__).resolve().parent
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
if Path(FONT).exists():
    pdfmetrics.registerFont(TTFont('DV',FONT));pdfmetrics.registerFont(TTFont('DV-Bold',BOLD))
    regular='DV';bold='DV-Bold'
else:regular='Helvetica';bold='Helvetica-Bold'
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='DocTitleX',fontName=bold,fontSize=17,leading=22,spaceAfter=7,textColor=colors.HexColor('#102a43')))
styles.add(ParagraphStyle(name='SectionX',fontName=bold,fontSize=11.5,leading=15,spaceBefore=13,spaceAfter=5,textColor=colors.HexColor('#173b58')))
styles.add(ParagraphStyle(name='BodyX',fontName=regular,fontSize=8.7,leading=13,spaceAfter=6))
styles.add(ParagraphStyle(name='SmallX',fontName=regular,fontSize=7.6,leading=10,spaceAfter=3))
styles.add(ParagraphStyle(name='CodeX',fontName=regular,fontSize=7.3,leading=10,spaceAfter=4))
styles.add(ParagraphStyle(name='CellX',fontName=regular,fontSize=7.5,leading=10))
styles.add(ParagraphStyle(name='HeaderX',fontName=bold,fontSize=7.5,leading=10,textColor=colors.white))

P=lambda x,style='BodyX':Paragraph(x,styles[style])
flow=[]
flow+=[P('A069 v0.6.2 - Dual-Trefoil High-Resolution GP Campaign','DocTitleX'),P('SCIENTIFIC DEVELOPMENT REPORT  |  19 October 2026  |  NOT FROZEN  /  NOT CERTIFIED','SmallX')]
flow+=[P('Research scope','SectionX'),P('The user-requested campaign includes 160 cubed grids for both historical trefoil seeds: Fourier A (2015 p.32) and Torus B (2015 p.66). Optional grid refinements are B192, B256, A320 and A512. The goal is to test knot-line reconstruction and dynamical topology, not to fit a Swirl Clock or claim an already established internal eigenmode.')]
flow+=[P('Critical preregistered core-readiness inequality','SectionX'),P('At box length L=10, G32 requires xi*N/L &gt;= 4, xi*kappa_max &lt;= 0.30 and xi/d_nonlocal &lt;= 0.30. The nonlocal gap is a screened segment-distance estimate; it is not a mathematically certified tube reach. Thus even G32 PASS is only a preflight screen.')]
flow+=[P('Fourier A at N=160 requires xi &gt;= 0.25 to resolve four cells per core, but xi &lt;= 0.08524 from the nonlocal separation estimate. No value of xi satisfies both constraints. The requested A160 run is therefore <b>diagnostic-only</b>. For A, the first even grid meeting this screen is N=470; A512 with xi=0.08 is the selected high-memory candidate. Torus B at N=160 with xi=0.28 passes the screening inequalities.')]
rows=[[P('Case','HeaderX'),P('N x N x N','HeaderX'),P('xi','HeaderX'),P('cells/xi','HeaderX'),P('xi*kappa','HeaderX'),P('xi/gap','HeaderX'),P('G32','HeaderX'),P('Peak RAM*','HeaderX')]]
for name in ['A160','B160','B192','B256','A320','A512']:
    c=CASES[name];s=screening(c.kind,c.n,c.xi);r=resource_forecast(c.n)
    cells=s['metrics']
    vals=[name,str(c.n),f'{c.xi:.2f}',f'{cells["cells_per_xi"]:.2f}',f'{cells["xi_times_kappa"]:.3f}',f'{cells["xi_over_nonlocal_gap"]:.3f}', 'SCREEN PASS' if s['all_preconditions_met'] else 'FAIL',f'{r["conservative_peak_gib"]:.1f} GiB']
    rows.append([P(v,'CellX') for v in vals])
t=Table(rows,colWidths=[21*mm,26*mm,12*mm,17*mm,19*mm,17*mm,30*mm,26*mm],repeatRows=1,hAlign='LEFT')
t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#173b58')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LINEBELOW',(0,0),(-1,0),.3,colors.HexColor('#7591a6')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f0f4f8')]),('BOTTOMPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('LEFTPADDING',(0,0),(-1,-1),5)]))
flow.append(t)
flow+=[P('* RAM figures are conservative forecasts rather than measured resident peaks; free physical memory and temporary FFT arrays are checked prior to execution. N512 may require about 96-128 GiB of installed RAM, large storage and many CPU-hours.','SmallX')]
flow+=[P('Actual computations performed in this build environment','SectionX'),P('46/46 inherited and new Python regression tests have passed. Two short actual 3D Gross-Pitaevskii smoke evolutions were performed at N=32 (Fourier A) and N=48 (Torus B). They exercised initialization, split-step time propagation, conservation diagnostics, subgrid face-zero tracking, multi-angle knot projection and immutable JSON output; a strict continuation/checkpoint test also completed. Both smoke runs intentionally fail G32 due to insufficient core resolution.')]
flow+=[P('The B48 smoke run recovered a closed final polygon with numerical Fox determinant three, but its initial graph was ambiguous. This is a useful topological projection diagnostic only, NOT a proof of ambient isotopy during evolution. No 160-cubed or larger 3D GP dynamics has been executed in this environment: the conservative RAM guard fails here.','BodyX')]
flow+=[P('GP coupling and physical core-scale compatibility','SectionX'),P('A scientific defect in the earlier GP preflight has been isolated: the v0.5.0 normalized equation fixes the GP nonlinearity to mu=1, whereas xi was varied only in the initial amplitude profile. Those profiles are not generally stationary and can broaden to the bulk healing scale. In v0.6.2 we evolve i dPsi/dT = -0.5 Laplacian(Psi) + mu (|Psi|^2 - 1) Psi, setting mu=1/(2 xi^2) to match the exact planar black-soliton width convention used by the initializer tanh[d/(sqrt(2)xi)]. This makes initialization and GP bulk coupling dimensionally consistent. It does NOT establish a stationary curved 3D vortex core. The flag --legacy-normalized-gp retains mu=1 strictly for historical regression.'),P('The B160/B192/B256 ladder at fixed xi=0.28 also holds mu=6.377551 constant, allowing spatial refinement of one GP model. Comparing xi=0.28 against 0.24 changes mu and is an independent physical-model/core sensitivity test, not pure continuum grid convergence.'),P('Scientific gate state','SectionX')]
for x in ['G32: B160/B192/B256 and A512 pass the preregistered geometry screening at the stated xi; A160/A320 fail. This is neither certified reach nor vortex stability.',
'G33: subgrid localization, dual graph diagnostics and five numerical projection directions are implemented. Single-snapshot projection consistency does not certify a time-continuous trefoil.',
'G34: UNRESOLVED - no complete cross-grid/time/core/domain convergence, ambient-isotopy continuity or independently verified reconnection event.',
'G35: UNRESOLVED - no stationary or relative-periodic knot, symmetry-reduced 3D Floquet/BdG eigenmode or blinded frequency holdout.']:
    flow.append(P(x))
flow+=[P('Method and computational integrity','SectionX'),P('The GP equation is i dPsi/dT = -1/2 Laplacian(Psi) + (|Psi|^2 - 1) Psi, in dimensionless units. The public A069 v0.5.0 source and initializer remain SHA-256 pinned (bb8e1d392e3e72c0c2caee22df406469f9f3de5504296da45cedc6fda8d04b6e). The v0.6.1 lattice/subgrid modules are inherited with a versioned configurable-coupling 3D GP stepper and new non-mutating development overlays. The code computes evolving order-parameter fields in all three spatial coordinates, not full incompressible SST Euler dynamics. It excludes gold-ratio constraints, measured clock values, Compton-frequency fits, Lorentz input and legacy visual KnotPlot relaxations.')]
flow+=[P('Windows campaign execution','SectionX'),P('Install requirements, unpack pinned solver, run 38 regression tests and print the grid/memory plan:','BodyX')]
for cmd in ['py -m pip install -r requirements.txt','py bootstrap_upstream.py','py -m pytest -q tests','py plan_v062.py','run_preflight_160.cmd','run_optional_high_res.cmd']:
    flow.append(P(cmd.replace('&','&amp;'),'CodeX'))
flow+=[P('The supplied scripts do not run A512 automatically. Source ZIP and output JSON are separate versions; neither FREEZE, BASIC, C++/SYCL parity nor official scientific BLIND reveal was performed here.','BodyX')]
flow+=[P('Bottom line','SectionX'),P('A069 v0.6.2 is a tested, runnable high-resolution campaign package, NOT a new scientific result from a 160-cubed run. The next valid decision depends on new user-side convergence data, particularly B160/B192/B256 first. The intrinsic Swirl Clock eigenfrequency remains UNRESOLVED.')]

out=ROOT/'A069_v0.6.2_DEVELOPMENT_REPORT.pdf'

def footer(canvas,doc):
    canvas.saveState();canvas.setFont(regular,7.4);canvas.setFillColor(colors.HexColor('#69829a'))
    canvas.drawString(18*mm,12*mm,'A069 / v0.6.2  |  DEVELOPMENT / NOT CERTIFIED')
    canvas.drawRightString(196*mm,12*mm,f'Page {doc.page}')
    canvas.restoreState()
SimpleDocTemplate(str(out),pagesize=(210*mm,297*mm),leftMargin=18*mm,rightMargin=16*mm,topMargin=18*mm,bottomMargin=19*mm).build(flow,onFirstPage=footer,onLaterPages=footer)
print(out)
