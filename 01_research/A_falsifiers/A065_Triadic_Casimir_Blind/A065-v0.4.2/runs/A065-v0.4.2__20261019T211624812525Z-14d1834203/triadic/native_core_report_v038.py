"""Dual PDF/LaTeX report for v0.3.8 source-native vorticity assay."""
from __future__ import annotations
from pathlib import Path
import math,json

def write(root,result):
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
    from reportlab.lib.enums import TA_LEFT
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,KeepTogether
    root=Path(root);reports=root/'reports';reports.mkdir(parents=True,exist_ok=True)
    pdf=reports/'SOURCE_NATIVE_CORE_V038_REPORT.pdf'
    tex=reports/'SOURCE_NATIVE_CORE_V038_REPORT.tex'
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='section2',parent=styles['Heading2'],spaceBefore=13,spaceAfter=5))
    story=[Paragraph('A065-v0.3.8 | Source-Native Vorticity Core Closure',styles['Title']),
           Paragraph('Blind-compatible numerical preparation - NOT certified PKLSA physics',styles['Italic']),Spacer(1,12),
           Paragraph('Scope and classification',styles['section2']),
           Paragraph('These fields are GENERATED from original parametric trefoil centreline geometry using an ASSUMED Gaussian transverse smoothing width. They are 3D arrays, but they are not measurements or evolved Euler/PKLSA fields. Gamma and enstrophy inversion is conditional on the Gaussian cross-sectional hypothesis.',styles['BodyText']),Spacer(1,9),
           Paragraph('Methods',styles['section2']),
           Paragraph('Omega(x) = Gamma * integral over closed C of G_a(x-X(s)) dX(s), with G_a(R)=exp(-R^2/a^2)/(pi^(3/2) a^3). Compute divergence-free periodic FFT projection, velocity and pressure-Poisson diagnostics. For each local normal plane, compute Gamma = integral (omega dot tangent) dA and Z = integral (omega dot tangent)^2 dA. Gaussian hypothesis implies a = |Gamma|/sqrt(2 pi Z). A different model such as Rankine gives a different width.',styles['BodyText']),
           Paragraph('Numerical gates',styles['section2'])]
    rows=[['Gate','Status','Scope'],['G28',result['G28'],'3D field / spectral constraints'],['G29',result['G29'],'All transverse stations admissible?'],['G30',result['G30'],'At least one admissible inference per source'],['G31',result['G31'],'No-fit withheld velocity and pressure predictions'],['G32',result['G32'].split('_NO_')[0],'Authentic independently qualified PKLSA']]
    tab=Table(rows,colWidths=[55,90,345],repeatRows=1,hAlign='LEFT');tab.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#16334B')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),.3,colors.lightgrey),('FONTSIZE',(0,0),(-1,-1),8),('VALIGN',(0,0),(-1,-1),'TOP'),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F4F6F7')])]))
    story.extend([tab,Spacer(1,12),Paragraph('Measured transverse profiles',styles['section2'])])
    for source in result['sources']:
        n=source['numerics']
        story.append(Paragraph(f"<b>{source['id']}</b> - a_seed = {source['assumed_a_seed_NOT_INFERRED']:.3f}; periodic N={source['field_resolution'][0]}^3; div(u) RMS={n['div_u_rms']:.2g}; Poisson residual={n['pressure_poisson_residual_rms']:.2g}; projected source correction={n['projection_relative_error']:.3%}.",styles['BodyText']))
        data=[['Station','Gamma','Z_axial','a(Gamma,Z)','Admitted','Vel error','Pressure error']]
        for s in source['cross_sections']:
            data.append([f"{s['fraction']:.2f}",f"{s['Gamma_cross_section']:.4f}",f"{s['Z_axial']:.4f}",f"{s['a_Gamma_Z_gaussian_assumption']:.4f}",'YES' if s['section_admissible'] else 'NO',f"{s['heldout_velocity_rms_relative']:.1%}",f"{s['heldout_radial_pressure_gradient_rms_relative']:.1%}"])
        t=Table(data,colWidths=[48,64,66,74,58,76,105],repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('LINEBELOW',(0,0),(-1,0),.7,colors.grey),('FONTSIZE',(0,0),(-1,-1),7.5),('VALIGN',(0,0),(-1,-1),'TOP'),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F7F9FA')])]))
        story.extend([Spacer(1,5),t,Spacer(1,14)])
    story += [Paragraph('Scientific interpretation / fail-closed limits',styles['section2']),
       Paragraph('Some planes intersect neighbouring strands or contain strong non-axial vorticity, leading to cancellations. These are REJECTED before inference. G31 is a synthetic surrogate-prediction failure; the FFT-heldout velocity and pressure derive from the same generated source and are NOT independently measured. The nonzero steady Euler residual shows the generated field is not established as an Euler steady state; no time evolution was solved.',styles['BodyText']),Spacer(1,8),
       Paragraph('For a physical claim the upstream PKLSA runner must export original u(x,y,z,t) or omega(x,y,z,t), a specified domain, boundary conditions, a transverse-core sampling region, circulation and enstrophy convergence, and a separate independently computed heldout u/p field with source hashes. The geometry-only E010/E011 outputs do not fulfil this requirement.',styles['BodyText'])]
    SimpleDocTemplate(str(pdf),pagesize=(595.2756,841.8898),rightMargin=42,leftMargin=42,topMargin=44,bottomMargin=40).build(story)
    latex=r'''\documentclass[11pt,a4paper]{article}
\usepackage[margin=2.1cm]{geometry}
\usepackage{amsmath,amssymb,booktabs,longtable}
\title{A065 v0.3.8: Source-Native Vorticity Core Closure\\\large Numerical Preparation -- Not Physical Certification}
\date{2026-10-19}
\begin{document}\maketitle
\section*{Explicitly assumed smooth tube}
\begin{align}
G_a(R)&=\frac{e^{-R^2/a^2}}{\pi^{3/2}a^3},\\
\boldsymbol\omega(\mathbf x)&=\Gamma\oint_C G_a(|\mathbf x-\mathbf X(s)|)\,d\mathbf X(s),\\
\Gamma_\perp&=\int_\Sigma \boldsymbol\omega\cdot\mathbf t\,dA,\quad
Z_\perp=\int_\Sigma (\boldsymbol\omega\cdot\mathbf t)^2\,dA,\\
a_G&=\frac{|\Gamma_\perp|}{\sqrt{2\pi Z_\perp}}.
\end{align}
The last formula is Gaussian-model-conditional and is not an SST core derivation.
\section*{Periodic numerical reconstruction}
\begin{align}
\hat{\mathbf u}(\mathbf k)&=\frac{i\mathbf k\times\hat{\boldsymbol\omega}(\mathbf k)}{|\mathbf k|^2},\quad \mathbf k\neq0,\\
\nabla^2p&=-\rho\,\partial_i u_j\,\partial_j u_i,\quad \langle p\rangle=0.
\end{align}
These equations use periodic boundaries and do not solve the time-dependent Euler PDE.
\section*{Gate results}
\begin{tabular}{ll}\toprule Gate & Status \\\midrule
'''
    for g in ('G28','G29','G30','G31','G32'):
        val=result[g].replace('_','\\_')
        latex+=f'{g} & {val} \\\n'
    latex+='\\bottomrule\n\\end{tabular}\n\\section*{Interpretation}\nA generated 3D Gaussian vorticity field is only a software control, not a measured source-native 3D Euler field. Transverse planes that fail flux-sign or non-axial-vorticity gates are invalid for core inference. Heldout pressure and velocity are dependent numerical diagnostics. Claims of physical SST core, Casimir, gravity remain unresolved.\n\\end{document}\n'
    tex.write_text(latex,encoding='utf-8')
    return {'pdf':str(pdf),'tex':str(tex)}
