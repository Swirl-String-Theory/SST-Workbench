"""Build a scientific LaTeX/PDF report from output JSON, not from predictions."""
from __future__ import annotations
import json,subprocess,shutil
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak

ROOT=Path(__file__).resolve().parents[1]
def esc(s):return str(s).replace('\\','\\textbackslash{}').replace('_','\\_').replace('%','\\%').replace('&','\\&')
def num(v,fmt='.3g'):
    return format(v,fmt)

def latex(data,stretch,res):
    by={x['knot']:x for x in stretch}
    rows='\n'.join(f"${r['knot']}$ & {r['max_energy_rel_drift']:.2e} & {r['max_divergence']:.2e} & {r['transport'].get('flux_p95_over_U',float('nan')):.3f} & {r['transport'].get('tracer_cross_count',0)}/{r['transport'].get('valid_tracers',0)} & {by[r['knot']]['relative_l2_residual']:.3f} \\\\" for r in data['tests'])
    rr=f"{res['initial_velocity_rel_l2_error_coarse_to_fine']*100:.2f}\\%" if res else 'not available'
    rt=f"{res['final_velocity_rel_l2_error_coarse_to_fine']*100:.2f}\\%" if res else 'not available'
    return r'''\documentclass[10pt,a4paper]{article}
\usepackage[margin=21mm]{geometry}
\usepackage{amsmath,amssymb,booktabs,longtable}
\usepackage[colorlinks=true,urlcolor=blue,linkcolor=black]{hyperref}
\title{A064 v0.2.0 --- PKLSA-Initiated Euler Flow\\Separatrix Candidate and Material-Transport Falsifier}
\author{SST Workbench numerical research prototype}
\date{15 October 2026}
\begin{document}\maketitle
\begin{abstract}
An evolving, periodic, incompressible 3-D Euler numerical lane replaces the repeated frozen velocity fields in A064 v0.1.1. Original, unqualified 3-D KnotPlot/PKLSA centerline coordinates of $3_1$, $5_2$ and $6_1$ are used only as initial-condition shapes. The workflow independently discovers enstrophy-level candidate boundaries before auditing normal relative flux and tracer crossing. The findings concern the selected model-dependent level sets, not global invariant manifolds and not physical SST evidence. Framework v1.0.7 FREEZE/CERTIFY has not run.
\end{abstract}
\section{Source and evidence classification}
Input centerlines: three raw native knot polygons, retained with SHA-256 hashes. E010 v0.3.1/E011 v0.3.0 certify static geometry at their own admitted provider anchors; these bundled native polylines have \emph{not} been mapped to E011 STATIC\_READY anchor IDs. E011 additionally reports $3_1$ and $5_2$ cross-provider robust and $6_1$ cross-provider sensitive in static metrics. No physical dynamical velocity field has been imported.
\par All values in the numerical solver use \emph{dimensionless computational units}. The NPZ uses an arbitrary $L_0=1\,\mathrm m$, $T_0=1\,\mathrm s$ bookkeeping convention for compatibility; this is not a measurement nor calibration of $r_c$ or $\mathbf v_{\!\boldsymbol{\circlearrowleft}}$.
\section{Equations and numerical scheme}
For an inviscid incompressible Euler fluid without external forces:
\begin{align}
\nabla\cdot \mathbf u &= 0, &
\partial_t \mathbf u + (\mathbf u\cdot\nabla)\mathbf u &= -\frac1\rho\nabla p, \\
\boldsymbol\omega &= \nabla\times\mathbf u, &
\partial_t\mathbf u &= \mathsf P(\mathbf u\times\boldsymbol\omega),
\end{align}
where $\mathsf P$ is the Leray projection onto solenoidal fields. Spatial differentiation uses periodic 3-D Fourier modes with strict $2/3$ truncation; time stepping uses RK4 and a CFL limit of $0.16$. The initial knotted tube is a Gaussian-smoothed line-vorticity distribution projected into a divergence-free velocity field. It is a \emph{model assumption}, not a unique physical PKLSA reconstruction.
\par The solver monitors energy $E=\frac12\langle|\mathbf u|^2\rangle$, helicity $H=\langle\mathbf u\cdot\boldsymbol\omega\rangle$, divergence and
\begin{equation}
\frac{D|\boldsymbol\omega|^2}{Dt}=2\omega_i\omega_j\partial_j u_i\,,\quad \frac D{Dt}=\partial_t+\mathbf u\cdot\nabla.
\label{eq:stretch}
\end{equation}
For a discovered level set $F(\mathbf x,t)=|\boldsymbol\omega|^2-\lambda$, its relative normal speed is
\begin{equation}
V_n^{\rm rel}=\frac{\partial_t F+\mathbf u\cdot\nabla F}{|\nabla F|}.
\end{equation}
A vanishing value is necessary for this level set to be material; $\nabla\cdot\mathbf u=0$ alone does \emph{not} establish this. Equation (\ref{eq:stretch}) explains how vortex stretching can alter enstrophy level sets without destroying the material character of actual vortex tubes.
\section{Discovery and independent test}
\textbf{Phase D}: At $t=0$, choose the first closed, watertight $|\boldsymbol\omega|^2$ isosurface in the fixed percentile order $65,75,85,92$. Save surface vertices, triangle faces, candidate metadata and SHA-256 seals \emph{before} computing transport. No candidate tuning using tracer outcomes is allowed.
\par \textbf{Phase T}: Track paired inside/outside initial tracers via RK4 through the evolving velocity snapshots, then independently compare membership relative to the same Eulerian level $\lambda$ at the final time. Report relative normal speed, crossings and numerical refinement. These observables test an enstrophy feature; full three-dimensional stable/unstable manifold extraction is a distinct unresolved gate.
\section{Numerical outcomes (13 time frames; $N=24$)}
\begin{center}\small
\begin{tabular}{lrrrrr}\toprule
Knot & $\Delta E/E$ & $\max|\nabla\cdot u|$ & $Q_{95}/U$ & Crossings & Stretch res.\\\midrule
''' + rows + r'''
\bottomrule\end{tabular}\end{center}
''' +r'''
All three candidate enstrophy isosurfaces are nonmaterial within their respective \emph{periodic numerical models} at this screening resolution. This is not evidence against the existence of some \emph{other} invariant material surface.
\par The centered, three-snapshot vortex-stretching identity residuals are exploratory numerical diagnostics. The $6_1$ residual is larger and prevents strong qualification even though energy and divergence remain well controlled.
\section{Resolution and hard scientific gates}
For the $3_1$ solver, a two-grid ($N=24,32$) velocity comparison gave $L^2$ discrepancies of ''' + rr + ' initially and '+rt+r''' finally. Two grids do not establish asymptotic convergence, and the fit between the core radius and cell width has not been independently calibrated.
\begin{itemize}
\item Software control suite: 17 passing tests, including the stationary ABC Beltrami Euler solution and RK4 refinement.
\item Time-varying NPZ generator, source hashes and candidate discovery seal: implemented.
\item Physical E011 provider-anchor propagation and native independent source agreement: \textbf{UNRESOLVED}.
\item Spatial/temporal convergence of transport flux and crossing fractions: \textbf{UNRESOLVED}.
\item Material versus dynamically invariant separatrix manifold: \textbf{UNRESOLVED}.
\item Framework v1.0.7 official FREEZE/CERTIFY and blind reveal ledger: \textbf{NOT EXECUTED}.
\end{itemize}
\section{Falsifiable next gates}
\begin{enumerate}
\item Replace raw centerlines by every eligible E011 provider anchor; preserve geometry hashes and independent-provider classes. Do not optimize carrier choice on a transport observable.
\item Run $N=24,32,48,64$ with controlled core width, and CFL/temporal ladders. Check normal flux and paired tracer statistics rather than energy drift alone.
\item Extract actual finite-time hyperbolic/elliptic transport structures or invariant manifolds in a suitable frame; validate material transport under time-varying rigid coordinate transformations.
\item Compare periodic Euler dynamics with an independently implemented, nonperiodic finite-core vortex evolution and with available externally generated snapshot data. No cross-model equivalence is presumed.
\end{enumerate}
\section{Reproduction}\texttt{run\_all.cmd EULER\_RUN}; \texttt{run\_all.cmd EULER\_BUILD --force}; \texttt{run\_all.cmd SELFTEST}. A model-NPZ source sidecar contains the input SHA-256, model parameters, timing, solver diagnostics and science-evidence class. Running the pipeline does not imply SST's physical constants are derived or validated.
\begin{thebibliography}{9}
\bibitem{helmholtz1858} H. von Helmholtz (1858), ``\"Uber Integrale der hydrodynamischen Gleichungen, welche den Wirbelbewegungen entsprechen'', \emph{Journal f\"ur die reine und angewandte Mathematik} \textbf{55}, 25--55. \url{https://doi.org/10.1515/crll.1858.55.25}.
\bibitem{saffman1992} P. G. Saffman (1992), \emph{Vortex Dynamics}, Cambridge University Press. \url{https://doi.org/10.1017/CBO9780511624063}.
\bibitem{hou2007} T. Y. Hou and R. Li (2007), ``Computing nearly singular solutions using pseudo-spectral methods'', \emph{Journal of Computational Physics} \textbf{226}, 379--397. \url{https://doi.org/10.1016/j.jcp.2007.04.015}.
\bibitem{haller2015} G. Haller (2015), ``Lagrangian Coherent Structures'', \emph{Annual Review of Fluid Mechanics} \textbf{47}, 137--162. \url{https://doi.org/10.1146/annurev-fluid-010313-141322}.
\end{thebibliography}
\end{document}
'''

def fallback(pdf,data,stretch,res):
    styles=getSampleStyleSheet();doc=SimpleDocTemplate(str(pdf),pagesize=A4,rightMargin=50,leftMargin=50)
    pieces=[]
    def add(s,sty='Normal'):pieces.append(Paragraph(s,styles[sty]));pieces.append(Spacer(1,10))
    add('A064 v0.2.0 — PKLSA Initialized 3D Euler Separatrix Candidate', 'Title')
    add('SCIENTIFIC STATUS: NUMERICAL MODEL ONLY; v1.0.7 official certification and invariant-manifold gate UNRESOLVED')
    add('Model: incompressible periodic 3D Euler, rotational formulation and dealiased Fourier projection; RK4 time integration. Thirteen real evolving frames (not repeated frozen fields). Original native knot geometry is unqualified as a production E011 dynamics provider.')
    add('Three model simulations','Heading2')
    by={x['knot']:x for x in stretch}
    tab=[['Knot','Energy drift','Flux / U','Tracer crossings','Stretch identity residual']]
    for row in data['tests']:
        p=row['transport'];tab.append([row['knot'],f"{row['max_energy_rel_drift']:.2e}",f"{p['flux_p95_over_U']:.3f}",f"{p['tracer_cross_count']}/{p['valid_tracers']}",f"{by[row['knot']]['relative_l2_residual']:.3f}"])
    t=Table(tab,colWidths=[52,96,83,106,112]);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.lightgrey),('GRID',(0,0),(-1,-1),.3,colors.grey),('FONTSIZE',(0,0),(-1,-1),8),('VALIGN',(0,0),(-1,-1),'TOP')]))
    pieces.append(t);pieces.append(Spacer(1,15))
    add('Numerical interpretation: the chosen enstrophy isosurfaces are not material features at this model scale. The existence of different invariant manifolds or free-space physical separatrices is not excluded.')
    add('Gates','Heading2')
    add('17/17 software tests passed. E011 provider source gate, flux/time convergence, invariant manifold and formal Framework v1.0.7 certification remain UNRESOLVED.')
    add('Sources','Heading2')
    add('Helmholtz (1858), Saffman (1992), Hou &amp; Li (2007), Haller (2015). See reports/FALSIFIER_REPORT.tex for complete bibitems and methodology.')
    doc.build(pieces)

def main():
    data=json.loads((ROOT/'A064-v0.2.0-outputs'/'RUN_SUMMARY.json').read_text())
    stretch=json.loads((ROOT/'A064-v0.2.0-outputs'/'VORTEX_STRETCHING_AUDIT.json').read_text())
    rfile=ROOT/'A064-v0.2.0-outputs'/'RESOLUTION_SCREEN.json'
    res=json.loads(rfile.read_text()) if rfile.exists() else None
    report_dir=ROOT/'reports';report_dir.mkdir(exist_ok=True)
    tex=report_dir/'FALSIFIER_REPORT.tex';tex.write_text(latex(data,stretch,res),encoding='utf8')
    pdf=ROOT.parent/'A064-v0.2.0_FALSIFIER_REPORT.pdf'
    engine=shutil.which('pdflatex')
    if engine:
        r=subprocess.run([engine,'-halt-on-error','-interaction=nonstopmode','-output-directory',str(report_dir),str(tex)],capture_output=True,text=True,cwd=report_dir)
        if r.returncode==0:
            # Second pass resolves TeX references.
            r2=subprocess.run([engine,'-halt-on-error','-interaction=nonstopmode','-output-directory',str(report_dir),str(tex)],capture_output=True,text=True,cwd=report_dir)
            if r2.returncode!=0:raise RuntimeError('second LaTeX pass failed: '+r2.stdout[-1000:])
            shutil.copyfile(report_dir/'FALSIFIER_REPORT.pdf',pdf)
        else:
            (report_dir/'TEX_FAILURE.log').write_text(r.stdout[-10000:]+r.stderr[-10000:])
            fallback(pdf,data,stretch,res)
    else:fallback(pdf,data,stretch,res)
    print('PDF:',pdf,'LaTeX:',tex)
    return pdf
if __name__=='__main__':main()
