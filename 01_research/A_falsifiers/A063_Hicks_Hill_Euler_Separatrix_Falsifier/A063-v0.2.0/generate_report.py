"""Reproducible LaTeX/PDF scientific report for A063-v0.2.0.
Does not modify gate status or source evidence; PDF build failure is reported.
"""
from __future__ import annotations
import json, pathlib, shutil, subprocess
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HOME=pathlib.Path(__file__).resolve().parent
OUT=HOME/'A063_Hicks_Hill_Torus_Tube_Falsifier_v0.2.0-outputs'
REPORT=HOME/'A063-v0.2.0-reports'

def main():
    REPORT.mkdir(parents=True,exist_ok=True)
    ctrl=json.loads((OUT/'TORUS_TUBE_CONTROLS.json').read_text())
    ledger=json.loads((OUT/'GATE_LEDGER.json').read_text())
    xyz=np.load(OUT/'CANDIDATE_LINE.npz')['xyz']
    fig=plt.figure(figsize=(8,5.3));ax=fig.add_subplot(projection='3d')
    ax.plot(xyz[:,0],xyz[:,1],xyz[:,2],lw=1.5)
    ax.set(xlabel='x/a',ylabel='y/a',zlabel='z/a');ax.set_box_aspect((1,1,.8))
    ax.view_init(elev=24,azim=30)
    fig.tight_layout();fig.savefig(REPORT/'T34_vortex_line.png',dpi=165);plt.close(fig)
    fig,ax=plt.subplots(figsize=(6.8,3.6))
    rad=[x['radius_over_a'] for x in ctrl['constant_radius_tube_flux']]
    fl=[x['normal_flow_rms_over_urms'] for x in ctrl['constant_radius_tube_flux']]
    ax.plot(rad,fl,'o-',label='Normal-flow RMS / velocity RMS')
    ax.axhline(0.0001,linestyle='--',label='registered material-surface tolerance')
    ax.set(xlabel='Tube radius / separatrix radius',ylabel='normalized RMS normal flow')
    ax.legend(fontsize=8);ax.grid(alpha=.25)
    fig.tight_layout();fig.savefig(REPORT/'tube_flux.png',dpi=170);plt.close(fig)
    adv=ctrl['kinematic_advection']['diagnostics']
    fig,ax=plt.subplots(figsize=(6.8,3.4))
    ax.plot([x['core_periods'] for x in adv],
            [x['distance_to_core_rms_over_initial_radius'] for x in adv],'o-')
    ax.set(xlabel='Periods of closed core orbit',ylabel='Material surface RMS distance / initial tube radius')
    ax.grid(alpha=.25);fig.tight_layout();fig.savefig(REPORT/'material_advection.png',dpi=170);plt.close(fig)
    fig,ax=plt.subplots(figsize=(6.8,3.4))
    slip=ctrl['shear']['samples']
    ax.plot([x['ds_over_a'] for x in slip],[x['four_cycle_phase_slip_rad'] for x in slip],'o-')
    ax.set(xlabel='Poincare radial initial-condition offset / a',ylabel='4-cycle azimuthal phase slip (radian)')
    ax.grid(alpha=.25);fig.tight_layout();fig.savefig(REPORT/'pitch_shear.png',dpi=170);plt.close(fig)

    c=ctrl['curve'];shape=ctrl['geometric_thickness_proxy']
    counts=ledger['counts'];proj=ctrl['independent_alexander'];vals=' / '.join(str(x['n_crossings']) for x in proj)
    def sf(x,fmt='.4g'):return format(x,fmt)
    rows=[]
    for r in ledger['records']:
        col='green!40!black' if r['status']=='PASS' else ('red!75!black' if r['status']=='FAIL' else 'orange!75!black')
        rows.append(r'\texttt{'+r['gate_id']+r'} & \textcolor{'+col+'}{'+r['status']+'} & '+tex_escape(r['question'])+r' \\')
    lines='\n'.join(rows)
    flux_rows='\n'.join(f"{x['radius_over_a']:.4f} & {x['normal_flow_rms_over_urms']:.7f} & {x['normal_flow_max_over_urms']:.7f} \\\\" for x in ctrl['constant_radius_tube_flux'])
    repl={
      'VERSION':'v0.2.0','PASSED':str(counts['PASS']),'FAILED':str(counts['FAIL']),'UNRESOLVED':str(counts['UNRESOLVED']),
      'S0':sf(c['s0_over_a'],'.12f'),'W':sf(c['W'],'.14f'),'CLOSURE':sf(c['closure_over_a'],'.4e'),
      'PROJECTIONS':vals,'POLY':', '.join(str(z) for z in ctrl['alexander_expected']),
      'THICKNESS':sf(shape['radius_curvature_min'],'.5f'), 'NONLOCAL':sf(shape['nonlocal_distance_proxy_min'],'.5f'),
      'CLEARANCE':sf(ctrl['separatrix_clearance_over_a'],'.6f'),'SHEAR':sf(ctrl['shear']['dW_d_s_over_a'],'.6f'),
      'CENTERCONTROL':sf(ctrl['zero_radius_control']['normal_flow_rms_over_urms'],'.3e'),
      'ADVECTION':sf(ctrl['kinematic_advection']['diagnostics'][-1]['distance_to_core_rms_over_initial_radius'],'.3f'),
      'ADVECTION_FINE':sf(ctrl['kinematic_advection_fine']['diagnostics'][-1]['distance_to_core_rms_over_initial_radius'],'.3f'),
      'GATES':lines,'FLUX_ROWS':flux_rows}
    template=r'''\documentclass[10pt,a4paper]{article}
\usepackage[margin=18mm,top=19mm,bottom=19mm]{geometry}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern,amsmath,amssymb,booktabs,array,graphicx,xcolor,hyperref,float}
\hypersetup{colorlinks=true,linkcolor=blue!50!black,urlcolor=blue!60!black}
\definecolor{navy}{RGB}{21,46,80}
\definecolor{pale}{RGB}{230,239,248}
\setlength{\parskip}{4pt}\setlength{\parindent}{0pt}\emergencystretch=3em
\newcommand{\sectionline}[1]{\vspace{6pt}{\large\bfseries\color{navy}#1}\par\vspace{3pt}\hrule\vspace{4pt}}
\begin{document}
{\small\color{navy}\bfseries SST-WORKBENCH / A063 / INDEPENDENT NUMERICAL FALSIFIER}\hfill{\footnotesize 13 October 2026}
\vspace{3pt}\hrule\vspace{7pt}
{\LARGE\bfseries Does the Hicks $T(3,4)$ vortex line support a finite stable vortex tube?}\par
{\large A063 @VERSION@ --- analytical/numerical reference report}\par\vspace{5pt}
\fcolorbox{navy}{pale}{\parbox{.965\linewidth}{\textbf{Outcome:} The closed $T(3,4)$ vortex-field-line is independently classified numerically. The tested constant-radius knotted tubular surface is \textbf{not material}, and neighboring winding shows nonzero shear. The existence and nonlinear stability of a differently shaped finite tube remains \textbf{UNRESOLVED}. \hfill \textbf{@PASSED@ PASS / @FAILED@ FAIL / @UNRESOLVED@ UNRESOLVED}}}
\sectionline{1. Model and falsifiable distinctions}
Inside the spherical Hicks aggregate ($r<a$), the exact axisymmetric streamfunction is
\begin{equation}
\psi=A\!\left[J(\lambda r/a)-(r/a)^2J(\lambda)\right]\!\sin^2\theta,
\quad J(y)=\frac{\sin y}{y}-\cos y.
\end{equation}
With $(s,\phi,z)$, $u_s=-\partial_z\psi/s$, $u_z=\partial_s\psi/s$, $u_\phi=(\lambda/a)\psi/s$; the first root of $\tan\lambda=\lambda$ is $\lambda_1\simeq 4.4934094579$. In this Beltrami branch, $\boldsymbol\omega=(\lambda/a)\mathbf u$, hence a streamline is also a \emph{vorticity line}.

Separate four propositions: (I) a closed knotted line; (II) an embedded geometric neighborhood; (III) an actual vortex-aligned/material surface $\boldsymbol\omega\cdot\mathbf n=0$; (IV) nonlinear time-dependent Euler stability. (I) never implies (III) or (IV).
\sectionline{2. Reproduced orbit and independent topology test}
A new high-accuracy integration gives $s_0/a=\mathbf{@S0@}$, winding $W=\mathbf{@W@}$ and closed-orbit residual $\|X(T)-X(0)\|/a=\mathbf{@CLOSURE@}$ over four poloidal turns.

The 3-D polygon was projected along four distinct generic directions (raw crossing counts: @PROJECTIONS@). For each projection, over/under crossing order yields a Wirtinger/Fox Alexander matrix, and its minor gives the same normalized polynomial:
\begin{equation}
\Delta_{\mathrm{numerical}}(t)=t^6-t^5+t^3-t+1
=\Delta_{T(3,4)}(t),\qquad |\Delta(-1)|=3.
\end{equation}
This is independent of a mere winding-label assignment. Matching the Alexander polynomial is not a unique-knot theorem in isolation; the numerically embedded invariant torus and $(3,4)$ winding supply additional classification evidence.
\begin{figure}[H]\centering\includegraphics[width=.76\linewidth]{T34_vortex_line.png}\caption{Numerical $T(3,4)$ Hicks-Beltrami vortex line in dimensionless Cartesian coordinates.}\end{figure}
\sectionline{3. Geometric thickening versus material vortex tube}
The sampled minimum curvature-radius proxy is $R_\kappa/a\simeq @THICKNESS@$ and the excluded-neighbor point-distance proxy is $d_{\mathrm{nonlocal}}/a\simeq @NONLOCAL@$. The orbit stays at least $@CLEARANCE@a$ inside the spherical separatrix. These are \textbf{not continuum tube reach bounds} and cannot certify absence of every self-intersection for an arbitrary surface.

For the explicit normal tube $X_{\delta}(\sigma,\vartheta)=X(\sigma)+\delta[\mathbf N(\sigma)\cos\vartheta+\mathbf B(\sigma)\sin\vartheta]$, a material steady tube must satisfy $\mathbf u\cdot\mathbf n=0$ pointwise; and the Beltrami vortex flux satisfies $\boldsymbol\omega\cdot\mathbf n=(\lambda/a)\mathbf u\cdot\mathbf n$. We sampled the actual velocity using the exact field (90 longitudinal points, 16 angular samples, plus a finer 180$\times$24 check).
\begin{table}[H]\centering\begin{tabular}{rrr}\toprule $\delta/a$ & RMS $|u_n|/u_{\rm rms}$ & max $|u_n|/u_{\rm rms}$ \\ \midrule
@FLUX_ROWS@
\bottomrule\end{tabular}\caption{Pointwise normal-velocity diagnostic for an initially constant-radius knot tube.}\end{table}
The zero-radius tangent control is @CENTERCONTROL@. The normal leakage is substantially above the preregistered $10^{-4}$ threshold; therefore \textbf{this steady constant-radius normal tube fails the material-surface gate (T5)}. This does not rule out a nonconstant-radius or advected time-dependent tube.
\begin{figure}[H]\centering\includegraphics[width=.70\linewidth]{tube_flux.png}\caption{Measured positive normal flow increases with tube radius.}\end{figure}
\sectionline{4. Nearby field lines and pitch-shear test}
The Poincar\'e return rotation $W(s_0)$ has derivative $dW/d(s_0/a)\simeq @SHEAR@$. Thus a nonzero radial displacement develops azimuthal phase slip after four poloidal circuits:
\begin{equation}\Delta\phi_4\simeq 8\pi\,[W(s_0+\delta s)-3/4].\end{equation}
Therefore a positive-width annulus of neighboring lines does not share the exact same $3{:}4$ closure under this integrable Hicks flow. \textbf{T6 FAIL is a field-line-coherence result, not a time-dependent Euler instability eigenvalue.}
\begin{figure}[H]\centering\includegraphics[width=.70\linewidth]{pitch_shear.png}\caption{Neighboring initial conditions produce opposite signed four-period slip.}\end{figure}
\sectionline{5. Finite-time material advection in the prescribed Hicks field}
A material knotted surface (initial $\delta/a=0.004$, 384 markers; confirmation with 720 markers) was transported with $\dot{X}=u_{\rm Hicks}(X)$ while the steady Euler field itself remained fixed. The surface's RMS distance to the original closed knot after four core periods rose to @ADVECTION@ times its initial radius (confirmation sample: @ADVECTION_FINE@ times); intermediate records are stored in the JSON output. This is finite-time kinematic deformation, not a coupled perturbed 3-D Euler evolution.
\begin{figure}[H]\centering\includegraphics[width=.67\linewidth]{material_advection.png}\caption{Localization of the advected material surface relative to the closed reference knot.}\end{figure}
\sectionline{6. Gate ledger and continuation policy}
\small\begin{longtable}{@{}p{0.055\linewidth}p{0.115\linewidth}p{0.76\linewidth}@{}}\toprule Gate & Result & Qualification question \\ \midrule
@GATES@
\bottomrule\end{longtable}\normalsize
A scientific FAIL never stops later diagnostic gates. T8A PASS certifies execution of the prescribed-field deformation measurement, not stability. Gates T8 and T9 remain open, rather than being relabeled PASS: no three-dimensional, pressure-coupled perturbed Euler evolution or independent native C++ FP64/canonical-framework certification has been performed.
\sectionline{7. What a decisive follow-up must demonstrate}
Pre-register: a finite smooth tubular surface with independent knot invariant and positive clearance; a flux condition $\boldsymbol\omega\cdot\mathbf n=0$ (or an explicitly time-dependent material-boundary evolution law); constrained-energy stationarity; reproducible linearized-Euler spectra; three spatial resolutions, at least three perturbation amplitudes, and non-linear bounded deformation for 10 core periods, with energy/helicity, divergence, topology and pressure-Poisson audits. Source-independent carriers must be identified separately (E013), not silently substituted.

\textbf{Strict conclusion.} The observed $T(3,4)$ is a convincing \emph{numerical vortex-line knot}, and a finite geometric neighborhood can be sampled. A naive steady constant-radius vortex tube is rejected. No physical particle, persistent finite vortex core, full 3D stability or mass quantization follows.
\sectionline{References and provenance}
\begin{enumerate}\item W. M. Hicks (1899), \emph{Researches in Vortex Motion. Part III: On Spiral or Gyrostatic Vortex Aggregates}, \href{https://doi.org/10.1098/rsta.1899.0002}{doi:10.1098/rsta.1899.0002}.
\item M. J. M. Hill (1894), \emph{On a Spherical Vortex}, \href{https://doi.org/10.1098/rsta.1894.0006}{doi:10.1098/rsta.1894.0006}.
\item A063-v0.1.1: numerical streamline precursor. A063-v0.2.0: release source seal, gate ledger, controls JSON and vortex-line NPZ. All evidence is numerical, not experimental.
\end{enumerate}
\end{document}
'''
    # longtable needed for continuation-safe gate table
    template=template.replace('lmodern,amsmath,amssymb,booktabs,array,graphicx,xcolor,hyperref,float', 'lmodern,amsmath,amssymb,booktabs,array,graphicx,xcolor,hyperref,float,longtable')
    template=template.replace(r'\newcommand{\sectionline}[1]{\vspace{6pt}{\large\bfseries\color{navy}#1}\par\vspace{3pt}\hrule\vspace{4pt}}',
               r'\newcommand{\sectionline}[1]{\par\vspace{6pt}\noindent{\large\bfseries\color{navy}#1}\par\vspace{3pt}\hrule\vspace{4pt}}')
    template=template.replace(r'\hfill \textbf{@PASSED@ PASS / @FAILED@ FAIL / @UNRESOLVED@ UNRESOLVED}',
               r'\par\smallskip\textbf{@PASSED@ PASS / @FAILED@ FAIL / @UNRESOLVED@ UNRESOLVED}')
    template=template.replace(r'\begin{longtable}{@{}p{0.055\linewidth}p{0.115\linewidth}p{0.76\linewidth}@{}}',
               r'\begin{longtable}{@{}p{0.075\linewidth}p{0.155\linewidth}>{\raggedright\arraybackslash}p{0.665\linewidth}@{}}')
    template=template.replace('GATE\\_LEDGER, TORUS\\_TUBE\\_CONTROLS',r'\texttt{GATE\_LEDGER}, \texttt{TORUS\_TUBE\_CONTROLS}')
    template=template.replace(r'\texttt{CANDIDATE\_LINE.npz}', r'\texttt{CANDIDATE\_LINE.npz}')
    template=template.replace('\\_LEDGER, TORUS\\_TUBE\\_CONTROLS',r'\_LEDGER}, \texttt{TORUS\_TUBE\_CONTROLS}')
    template=template.replace('\\_LEDGER, TORUS\\_TUBE\\_CONTROLS','\\_LEDGER; TORUS\\_TUBE\\_CONTROLS')
    for k,v in repl.items():template=template.replace('@'+k+'@',v)
    tex=REPORT/'A063-v0.2.0_FALSIFIER_REPORT.tex'
    tex.write_text(template,encoding='utf-8')
    if not shutil.which('pdflatex'):
        raise RuntimeError('pdflatex unavailable; LaTeX source and figures were generated, but PDF NOT created')
    cmd=['pdflatex','-interaction=nonstopmode','-halt-on-error','-output-directory',str(REPORT),str(tex)]
    for it in range(2):
        r=subprocess.run(cmd,cwd=REPORT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        if r.returncode:raise RuntimeError(f'pdflatex failed: {r.stdout[-3500:]}')
    print('Report:',REPORT/'A063-v0.2.0_FALSIFIER_REPORT.pdf')

def tex_escape(s):
    out=s.replace('\\',r'\textbackslash{}')
    for a,b in [('&',r'\&'),('%',r'\%'),('_',r'\_'),('#',r'\#')]:out=out.replace(a,b)
    return out

if __name__=='__main__':main()
