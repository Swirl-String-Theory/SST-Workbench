"""Autogenerate figures, TeX and PDF for the A064 Hopf-link model comparison."""
from __future__ import annotations
import json,subprocess,math
from pathlib import Path
import numpy as np

def tex(s):
    return (str(s).replace('\\','\\textbackslash{}').replace('_','\\_').replace('%','\\%')
            .replace('&','\\&').replace('#','\\#'))

def generate(root):
    root=Path(root);rep=root/'reports';rep.mkdir(exist_ok=True)
    from hopf_extension import CASES,geometry,audit
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig=plt.figure(figsize=(12,3.65))
    for ii,case in enumerate(CASES):
        ax=fig.add_subplot(1,3,ii+1,projection='3d')
        curves,_=geometry(case)
        for k,c in enumerate(curves):
            d=np.vstack((c,c[0]));ax.plot(d[:,0],d[:,1],d[:,2],lw=1.65)
        ax.set_title(case.replace('_',' '),fontsize=9)
        ax.set_xlim(-2.6,2.6);ax.set_ylim(-2.6,2.6);ax.set_zlim(-2.6,2.6)
        ax.set_box_aspect((1,1,1));ax.set_xticks([]);ax.set_yticks([]);ax.set_zticks([])
        ax.view_init(elev=25,azim=38)
    fig.tight_layout();fig.savefig(rep/'THREE_HOPF_GEOMETRIES.png',dpi=155);plt.close(fig)
    data=[]
    for c in CASES:
        for n in (24,32,48):
            f=root/'outputs'/f'{c}_N{n}'/'GATE_RESULTS.json'
            if f.exists():
                d=json.loads(f.read_text());data.append(d)
    # Full safety: absent/incomplete output is explicitly NOT_COMPLETED.
    table=[]
    for case in CASES:
        for n in (24,32,48):
            d=next((x for x in data if x['case']==case and x['grid']==n),None)
            if d is None:
                table.append(f'{tex(case)} & {n} & \\multicolumn{{6}}{{c}}{{\\textsf{{NOT\\_COMPLETED}}}} \\\\')
                continue
            t=d['outer_enstrophy'];g=d['genus_one_feature'];own=d['kinematic_nearest_core_exchange']
            frac=t.get('tracer_cross_fraction');drift=d['euler_diagnostics']['max_energy_rel_drift']
            gt='none' if g is None else f'{g["percentile"]}th'
            assert own['seeds_valid']<=own['seeds_total']
            table.append(f'{tex(case)} & {n} & {drift:.2e} & {t.get("flux_p95_over_U",float("nan")):.3f} & '
                         f'{t.get("tracer_cross_count",0)}/{t.get("valid_tracers",0)} & '
                         f'{gt} & {own["changed_ownership"]}/{own["seeds_valid"]} & {frac:.3f} \\\\')
    # Source-native and mechanical embedding must be differentiated explicitly.
    template=r'''\documentclass[10pt,a4paper]{article}
\usepackage[margin=16mm]{geometry}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern,amsmath,amssymb,booktabs,longtable,graphicx,xcolor,hyperref}
\hypersetup{colorlinks=true,urlcolor=blue,linkcolor=blue}
\setlength{\parskip}{5pt}\setlength{\parindent}{0pt}
\begin{document}
\begin{center}
{\LARGE\bfseries A064 v0.2.2 --- L6n1 and Triple Gear}\par
{\Large Three-core Euler flow: topology, enstrophy candidates and transport}\par
SST-Workbench numerical research prototype --- 15 October 2026
\end{center}
\begin{abstract}
Three embeddings of the same three-component Hopf-link isotopy class are studied independently:
source-native KnotPlot \texttt{link\_6.3.3} (L6n1), source-native KnotPlot \texttt{torus\_3.3} ($T(3,3)$), and
an analytic geometric centreline proxy for the Schleimer--Segerman triple gear.
The study tests whether candidate Eulerian enstrophy boundaries and tracer transport depend on embedding rather
than solely on pairwise linking. No mechanical teeth, force transmission or phase locking are simulated.
This is not a certified PKLSA dynamical provider, SST evidence, or a genuine invariant-manifold discovery.
\end{abstract}
\section{Native source and mathematical identity}
The user's Knotilus Gauss code for L6n1 is
$\{1,6,-5,-3\},\{-4,-1,2,5\},\{-6,4,3,-2\}$, i.e. Rolfsen's $6_3^3$ link.
All three components are individually unknotted, whereas each pair has $|\mathrm{Lk}_{ij}|=1$.
Both native KnotPlot sources are included with SHA-256 metadata.
Their three components are recovered from closed source-polygons separated by exceptional inter-component export jumps; per-component order is retained except for a recorded orientation reversal in L6n1 to standardize signed linking.
The Triple Gear proxy uses three congruent 120-degree rotated circles from the published geometrical arrangement
$r=0.4950197$, $\theta=-0.8560281$ rad, reflected to match the source chirality.
A common similarity scaling maps each whole link into $[-2.35,2.35]^3$, then all computational velocity fields are normalized to a common RMS speed. Those are modeling choices, not physical SST unit calibrations.
\begin{figure}[h]\centering\includegraphics[width=0.98\linewidth]{THREE_HOPF_GEOMETRIES.png}
\caption{Three independently prepared Hopf-link embeddings; plot shows centerlines only.\label{fig:links}}\end{figure}
The topological qualification screens calculate three Alexander determinants equal to 1 and three Gauss-linking
integrals with magnitude approximately 1. This verifies necessary topology metrics, not a full certified link isotopy.
\section{Euler initial-value lane}
A Gaussian vorticity tube of width $a=0.42$ in a periodic $[0,2\pi]^3$ domain is laid along each source curve.
The common initial velocity is the solenoidal Biot--Savart reconstruction.
Evolution follows
\begin{equation}
\nabla\!\cdot\mathbf u=0,\qquad
\partial_t\mathbf u=\mathbb P(\mathbf u\times\boldsymbol\omega),\qquad
\boldsymbol\omega=\nabla\times\mathbf u,
\end{equation}
with Fourier pseudo-spectral RK4, $2/3$ de-aliasing, 13 saved frames over dimensionless $\Delta t=0.32$ and a bounded CFL.
Energy drift and spectral divergence are solver diagnostics, not sufficient evidence of converged tracer transport.
The native polyline geometry and initial-core conversion have no E011 anchor certificate.
\section{Discovery must precede transport}
At the first saved time step the preregistered percentiles $65,75,85,92,96,98,99,99.5$
are used to find closed, watertight isosurfaces of $|\boldsymbol\omega|^2$.
The entire discovery ledger is SHA-256 sealed before particle advection; the selected genus-one candidate is a topology-screened enstrophy feature, not an established core tube.
The independent transport stage measures
\begin{equation}
v_{n,\mathrm{rel}}=\frac{\partial_tF+\mathbf u\cdot\nabla F}{|\nabla F|},\qquad
 F(\mathbf x,t)=|\boldsymbol\omega|^2-\lambda,
\end{equation}
plus initial/final membership of RK4 advected tracers and a nearest-to-advected-core neighborhood probe.
A changing label is neither a vortex reconnection nor proof of crossing a material separatrix.
\section{Numerical outcomes}
\begin{center}\footnotesize
\begin{tabular}{lrrrrrrr}\toprule
Case & $N$ & $|\Delta E/E|$ & $Q_{95}/U$ & outer crossings & genus-1 & neighborhood & fraction\\\midrule
@TABLE@
\bottomrule
\end{tabular}\end{center}
\textbf{Interpretation:} The quantities above differ between distinct geometric embeddings despite common
$|\mathrm{Lk}_{ij}|=1$. A surface is not accepted as a dynamical separatrix unless
its identity persists through a resolution ladder, it remains material under particle advection, and an independent
invariant manifold or comparable transport barrier is identified.
If a genus-one candidate switches proximity-owner across grids, or first appears at a finer grid, it is
\textbf{not resolution-qualified}. A zero core-neighborhood reassignment count is only a short-time kinematic
proximity observation; it is not proof of no leakage and not an actual gear-locking observation.
\section{Falsification and unresolved gates}
\begin{enumerate}
\item Separate-source-file embedding contrast: \textbf{SCREENED}, not cross-provider qualified. Both native XYZ exports share the KnotPlot provider group.
\item Spatial/temporal/core-width convergence of tracer crossings, flux and feature surfaces: \textbf{UNRESOLVED}.
\item True material vortex tube and independently computed hyperbolic/elliptic manifold: \textbf{UNRESOLVED}.
\item Mechanical tooth-contact forces, central helix, and rational phase-lock $\theta_i=\sigma_i\kappa_i\phi+\delta_i$: \textbf{NOT MODELED}.
\item E011 STATIC\_READY matching, physical units, and framework v1.0.7 formal FREEZE/CERTIFY: \textbf{NOT EXECUTED}.
\end{enumerate}
\section{Reproduction and provenance}
\verb|run_all.cmd SELFTEST| and \verb|run_all.cmd RUN --grid 24| execute the primary lane.
\begin{verbatim}
run_all.cmd BUILD --case L6n1_KNOTPLOT --grid 32
run_all.cmd BUILD --case T33_KNOTPLOT --grid 48
run_all.cmd REPORT
\end{verbatim}
\noindent A run with \texttt{--grid 48} for the Triple Gear proxy is currently marked \texttt{NOT\_COMPLETED}.
The ZIP contains source geometry, source provenance and NPZ with source-sidecar hashes; incomplete runs are explicitly marked
\texttt{NOT\_COMPLETED}. Controls from A064 v0.2.1 (Borromean L6a4) can be compared separately, but are not claimed as the same link class.
\begin{thebibliography}{9}\small
\bibitem{KnotAtlas} Knot Atlas, ``L6n1'', \url{https://katlas.org/wiki/L6n1}.
\bibitem{Gear} S.~Schleimer and H.~Segerman (2013), ``Triple gear'', arXiv:1304.6859, \url{https://arxiv.org/abs/1304.6859}.
\bibitem{Saffman} P.~G.~Saffman (1992), \emph{Vortex Dynamics}, Cambridge University Press, DOI:10.1017/CBO9780511624063.
\bibitem{Haller} G.~Haller (2015), ``Lagrangian Coherent Structures'', \emph{Annual Review of Fluid Mechanics} 47, 137--162, DOI:10.1146/annurev-fluid-010313-141322.
\bibitem{Milnor} D.~DeTurck et al. (2013), ``Triple linking numbers, ambiguous Hopf invariants and integral formulas for three-component links'', \emph{Commun. Math. Phys.} 317, 347--370, arXiv:0901.1612.
\end{thebibliography}\end{document}
'''
    out=template.replace('@TABLE@','\n'.join(table))
    path=rep/'A064_v0.2.2_L6n1_TripleGear_FALSIFIER_REPORT.tex';path.write_text(out)
    try:
        for _ in range(2):
            subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error',path.name],cwd=rep,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT,timeout=100)
    except Exception as exc:
        raise RuntimeError('PDF/TeX build failed; check LaTeX log') from exc
    pdf=rep/path.with_suffix('.pdf').name
    summary={'schema':'A064-HOPF-RESEARCH-CAMPAIGN-v1','version':'0.2.2','runs_completed':len(data),
      'required_grid_cases':len(CASES)*3,
      'omitted_or_timeout':[{'case':c,'grid':n,'status':'NOT_COMPLETED'} for c in CASES for n in [24,32,48] if not any(d['case']==c and d['grid']==n for d in data)],
      'results':[{'case':d['case'],'grid':d['grid'],'outer_crossings':d['outer_enstrophy'].get('tracer_cross_count'),
        'outer_valid_tracers':d['outer_enstrophy'].get('valid_tracers'),
        'outer_fraction':d['outer_enstrophy'].get('tracer_cross_fraction'),
        'candidate_genus1':d['genus_one_feature'],
        'kinematic_neighborhood_exchange':d['kinematic_nearest_core_exchange']['changed_ownership'],
        'kinematic_neighborhood_valid':d['kinematic_nearest_core_exchange']['seeds_valid'],
        'energy_rel_drift':d['euler_diagnostics']['max_energy_rel_drift'],
        'max_divergence':d['euler_diagnostics']['max_divergence']} for d in data],
      'scientific_conclusion':'SCREENING_ONLY_CONVERGENCE_AND_PHYSICAL_SEPARATRIX_UNRESOLVED',
      'model_exclusion':'MECHANICAL_GEAR_FORCING_NOT_MODELED','framework_v1_0_7':'NOT_EXECUTED'}
    (root/'outputs/RUN_SUMMARY.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    print('PDF',pdf,'runs',len(data),'missing',summary['omitted_or_timeout'])
    return pdf
