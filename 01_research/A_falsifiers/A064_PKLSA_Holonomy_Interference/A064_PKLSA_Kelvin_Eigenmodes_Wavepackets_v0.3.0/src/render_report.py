"""Generate charts and a machine-grounded PDF report (reportlab)."""
import json, os, sys
from pathlib import Path
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak,KeepTogether
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs'
D=json.loads((OUT/'A064-v0.3.0_results.json').read_text())
GEOS=['knot_3.1','knot_5.2','knot_6.1','link_6.3.3']
for nm in GEOS:
    f=pd.read_csv(OUT/(nm+'_wave_timeseries.csv'))
    fig,ax=plt.subplots(figsize=(7.5,2.7))
    ax.plot(f.t,f.A_detector,label='A detector energy')
    ax.plot(f.t,f.B_detector,label='B detector energy')
    ax.plot(f.t,f.detector_cross,label='Interference cross-term')
    ax.set(xlabel='Dimensionless time',ylabel='Windowed intensity',title=nm+' — full Euler-tangent evolution')
    ax.legend(loc='best',fontsize=8);ax.grid(alpha=.15)
    fig.tight_layout();fig.savefig(OUT/(nm+'_packets.png'),dpi=160);plt.close(fig)
fig,ax=plt.subplots(figsize=(6,3))
for n in [8,12,16]:
    vals=D['computed']['knot_3.1']['eigen'][str(n)]['candidates']
    ax.scatter([n]*len(vals),[v['imag'] for v in vals],label=f'{n}³')
ax.set(xlabel='Grid linear size N',ylabel='Imaginary part of instantaneous eigenvalue',title='Trefoil: eigenpairs are not branch-matched')
ax.grid(alpha=.15);fig.tight_layout();fig.savefig(OUT/'spectrum_imag.png',dpi=160);plt.close(fig)

sty=getSampleStyleSheet();sty.add(ParagraphStyle(name='SSTtitle',parent=sty['Title'],fontSize=16,leading=19,spaceAfter=7))
sty.add(ParagraphStyle(name='SSTsmall',parent=sty['BodyText'],fontSize=8.5,leading=11.8,spaceAfter=6))
sty.add(ParagraphStyle(name='SSTmid',parent=sty['Heading2'],fontSize=11,spaceBefore=10,spaceAfter=6))
sty.add(ParagraphStyle(name='SSTcap',parent=sty['Normal'],fontSize=7.6,leading=10,textColor=colors.HexColor('#54637d')))
text=lambda x:Paragraph(str(x),sty['SSTsmall'])
paragraph=lambda x:Paragraph(str(x),sty['SSTsmall'])
def tbl(cells,widths):
    t=Table([[Paragraph(str(c),sty['SSTcap']) for c in row] for row in cells],colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e5eaf0')),('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#c6cdd6')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('BOTTOMPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6)]))
    return t
num=[x for x in D['gates'] if x['category']=='NUMERICAL'];scr=[x for x in D['gates'] if x['category']=='SCREENING']
story=[Paragraph('A064 v0.3.0 — Kelvin Eigenmode &amp; Two-Wavepacket Falsifier',sty['SSTtitle']),
        text('Executed 14 October 2026 | Existing PKLSA KnotPlot geometries | Dimensionless incompressible Euler–Galerkin'),
        tbl([['Numerical checks','Packet screen','Physics status'],[f"{sum(x['status']=='PASS' for x in num)}/{len(num)} PASS",f"{sum(x['status']=='PASS' for x in scr)}/{len(scr)} PASS",'G6 UNRESOLVED; G7 SCREEN_FAIL']],[62*mm,62*mm,60*mm]),
        Paragraph('Scope and main result',sty['SSTmid']),
        text('Matrix-free ARPACK eigenpairs were calculated directly from the linearized spectral Euler operator about the vortex-derived background. Eigenpair residuals pass. The background evolves: its frozen eigenvectors are NOT a certified Kelvin eigenmode basis. Two independently initialized localized complex perturbations were then integrated under the same time-dependent tangent Euler operator. Neither verified counter-propagation of both arms nor their synchronized arrival was detected on any of the four geometries.'),
        Paragraph('Instantaneous eigenpairs for the trefoil',sty['SSTmid'])]
eig=D['computed']['knot_3.1']['eigen']
rows=[['N³','Re(lambda)','Im(lambda)','Relative residual','Background rate']]
for n in [8,12,16]:
    v=eig[str(n)]['candidates'][0];q=eig[str(n)]
    rows.append([str(n),f"{v['real']:.7f}",f"{v['imag']:+.7f}",f"{v['relative_residual']:.2e}",f"{q['nonstationary_rate']:.4f}"])
story+=[tbl(rows,[21*mm,33*mm,33*mm,48*mm,49*mm]),Spacer(1,6),Image(str(OUT/'spectrum_imag.png'),width=165*mm,height=82.5*mm),
        Paragraph('Interpretation',sty['SSTmid']),text('These are validated eigenpairs of a finite Fourier–Galerkin matrix at a frozen instant, not identified branches with spatial-resolution convergence. Eigenvectors and oscillation frequencies cannot be promoted into Kelvin modes until a stationary or relative-periodic background and a co-moving operator have been certified.')]
story+=[PageBreak(),Paragraph('Wavepacket time evolution and falsifier gates',sty['SSTtitle'])]
rows=[['Geometry','max |cross| / energy','A expected direction','B expected direction','Recombine']]
for name in GEOS:
    d=D['computed'][name]['wave']
    rows.append([name,f"{d['max_abs_interference_fraction']:.5f}",'PASS' if d['evidence']['A']['evidence'] else 'FAIL',
                 'PASS' if d['evidence']['B']['evidence'] else 'FAIL','PASS' if d['verified_collision'] else 'FAIL'])
story+=[tbl(rows,[33*mm,44*mm,39*mm,39*mm,29*mm]),
        Spacer(1,8),Image(str(OUT/'knot_3.1_packets.png'),width=175*mm,height=63*mm),
        Image(str(OUT/'knot_5.2_packets.png'),width=175*mm,height=63*mm),
        Paragraph('Critical meaning of the negative screen',sty['SSTmid']),
        text('A signed spatial carrier exp(±iks) is only a labelled launch condition; the Euler operator does not guarantee that it travels with a prescribed group velocity. The actual energy centroids and detector peaks are evaluated from the evolved fields. All candidate arms are subjected to the same preregistered screen. The failures disqualify the claimed split/recombine interpretation for these launch packets, but do not falsify all possible Euler/Kelvin mode families.')]
story+=[PageBreak(),Paragraph('Controls, source status and follow-up gates',sty['SSTtitle'])]
c=D['global_controls']
story+=[tbl([['Control','Result'],['No-flow detector absolute drift',f"{c['null_detector_max_absolute_drift']:.3e}"],
              ['Half-step versus standard response discrepancy',f"{c['timestep_cross_fraction_difference']:.3e}"],
              ['Centered derivative vs Euler Jacobian',f"{c['tangent_fd_error']:.3e}"],
              ['Numerical gate pass',f"{sum(x['status']=='PASS' for x in num)}/{len(num)}"]],[100*mm,84*mm]),
        Paragraph('The physical qualification gates remain open',sty['SSTmid'])]
for k,v in D['scientific_gates'].items():story.append(text(f'<b>{k}</b>: {v}'))
story+=[Paragraph('Provenance and limitations',sty['SSTmid']),
        text('Four native KnotPlot census v0.1.2 objects, geometry-only and not publication-qualified. All derive from one source family. Geometric coordinates and simulation times are not calibrated to SI units; normalized Gaussian core width is not the canonical physical SST radius. The physical G6/G7 gates remain UNRESOLVED; numerical screening failures do not constitute a complete falsification of Kelvin-wave interference. Official frozen framework v1.0.7 runner and reveal have not been invoked.'),
        Paragraph('Next independent falsification tranche',sty['SSTmid']),
        text('Compute an Euler relative equilibrium or periodic orbit; move to its comoving frame; identify a converged isolated Kelvin branch and its group velocity. Construct wavepackets from certified positive- and negative-velocity mode branches and test actual detector collision under source- and topology-matched controls. Only then define a parallel-transport connection and test a loop-phase against a non-topological null.'),
        Paragraph('References',sty['SSTmid']),
        text('Saner et al., Nature Physics (2026), doi:10.1038/s41567-026-03400-6. Moffatt, J. Fluid Mech. 35 (1969), doi:10.1017/S0022112069000991. Saffman, Vortex Dynamics (Cambridge University Press, 1992), doi:10.1017/CBO9780511624063.'),
        text('Full equations and LaTeX thebibliography are provided in docs/SCIENTIFIC_METHOD.tex and the corresponding PDF.')]
pdf=str(OUT/'A064-v0.3.0_FALSIFIER_REPORT.pdf')
SimpleDocTemplate(pdf,pagesize=(210*mm,297*mm),leftMargin=12*mm,rightMargin=12*mm,topMargin=13*mm,bottomMargin=14*mm).build(story)
print('Rendered',pdf)
