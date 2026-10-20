r"""Create a fully standalone A065 scientific LaTeX report.

No \input, \include, \includegraphics, generated fonts or external bib files.
Only standard TeX distribution packages. The source is saved next to every PDF.
"""
from __future__ import annotations
import json
import math
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from .security import readjson, sha


def escape_tex(value):
    text = str(value)
    mapping = {'\\': r'\textbackslash{}', '{':r'\{', '}':r'\}', '_':r'\_',
               '&':r'\&', '%':r'\%', '#':r'\#', '$':r'\$',
               '~':r'\textasciitilde{}', '^':r'\textasciicircum{}'}
    return ''.join(mapping.get(c, c) for c in text)


def write_tex(root, report_path, *, run_id, label, frame_state):
    root = Path(root); report_path = Path(report_path)
    summary = readjson(root/'outputs'/'BLIND'/'RUN_SUMMARY.json')
    d01 = readjson(root/'outputs'/'BLIND'/'D01_EULER.json')
    d02 = readjson(root/'outputs'/'BLIND'/'D02_CLOCK_LINK.json')
    d03 = readjson(root/'outputs'/'BLIND'/'D03_TWO_SURFACE.json')
    seals = readjson(root/'seals'/'GLOBAL_COMMITMENT.json')['seals']
    dyn = d01['filament_dynamics']
    provider = d01.get('second_provider_readiness',{})
    latex_rowbreak=chr(92)*2
    def fmt(value):
        if isinstance(value, (float,int)) and not isinstance(value, bool):
            if not math.isfinite(value):return str(value)
            return f'{value:.8g}'
        return escape_tex(value)
    gate_rows=[]
    for g in summary.get('gates',[]):
        metrics = g.get('metric',g.get('metrics',{}))
        if isinstance(metrics, dict):
            metrics = ', '.join(f'{k}={v:.5g}' if isinstance(v,float) else f'{k}={v}' for k,v in list(metrics.items())[:2])
        metrics = str(metrics)[:62]
        gate_rows.append(f"\\nolinkurl{{{g.get('gate','?')}}} & {escape_tex(g.get('status','?'))} & {escape_tex(metrics)} " + latex_rowbreak)
    seal_rows = [escape_tex(k) + ' & ' + escape_tex(v[:32]) + '...' + latex_rowbreak for k,v in seals.items()]
    fail = [g for g in summary['gates'] if g.get('status') != 'PASS']
    fail_text = ', '.join(escape_tex(g.get('gate','unknown')) for g in fail) or 'none'
    data = d03.get('free_exponents_not_targets',[])
    exponent_rows=[]
    for item in data:
        exponent_rows.append(f"{escape_tex('/'.join(item.get('pair',[])) if isinstance(item.get('pair'),list) else item.get('pair','?'))} & {fmt(item.get('temperature','?'))} & {fmt(item.get('free_fitted_exponent','?'))} " + latex_rowbreak)
    if not exponent_rows: exponent_rows=['N/A & N/A & N/A ' + latex_rowbreak]
    src = readjson(root/'data'/'D01_EULER'/'pklsa'/'source.json')
    tex = r'''\documentclass[10pt,a4paper]{article}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage[margin=16mm]{geometry}
\usepackage{amsmath,amssymb,booktabs,longtable,array}
\usepackage[hidelinks]{hyperref}
\usepackage{xcolor}
\usepackage{lmodern}
\setlength{\parskip}{3pt}
\setlength{\parindent}{0pt}
\title{A065 Triadic--Casimir / PKLSA\\ Blind Falsifier v0.3.4 -- Convergence and Independent Provider Tranche}
\author{SST-Workbench; self-contained computational report}
\date{Run: @@RUN@@}
\begin{document}
\maketitle
\begin{center}
\fbox{\parbox{0.88\linewidth}{\small\textbf{Scientific status:} This is a geometry and synthetic numerical pilot. Neither the time-dependent incompressible Euler equations nor a microscopic metal response nor a measured Casimir force has been certified. All preregistered failures are retained.}}
\end{center}
\section{Identification and provenance}
\begin{tabular}{@{}p{0.32\linewidth}p{0.60\linewidth}@{}}
\toprule
Run mode & @@MODE@@ \\
Framework & @@FRAMEWORK@@ \\
Blind campaign & @@SUMMARY@@ \\
PKLSA source points & 300 KnotPlot trefoil ($3_1$) \\
Original source SHA-256 & \texttt{@@SOURCEHASH@@} \\
\bottomrule
\end{tabular}
\section{The three response channels}
The June three-observable interpretation is retained as three distinct measurements, not as the sum of three forces:
\[
\mathcal O[X;a]=\begin{pmatrix}
\mathbf a_{\mathrm{bulk}}[X;a]\\
\Delta\nu/\nu[X;a]\\
P_{\mathrm{boundary}}[X;a]
\end{pmatrix}.
\]
With constant-density incompressible Euler kinematics,
\begin{align}
\nabla\cdot\mathbf u&=0,&
\boldsymbol\omega&=\nabla\times\mathbf u,\\
\nabla^2p&=\rho_M\left(\tfrac12|\boldsymbol\omega|^2-\|S\|_F^2\right),&
S_{ij}&=\tfrac12(\partial_i u_j+\partial_j u_i).
\end{align}
In a \emph{stationary, irrotational} region the conditional Swirl-Clock reduction gives
\[
p+\tfrac12\rho_M|\mathbf u|^2=C,\qquad
N^2=1-|\mathbf u|^2/c_\star^2
\implies\nabla\ln N=\frac{\nabla p}{\rho_Mc_\star^2N^2}.
\]
This identity is conditional on selecting the same effective velocity in Bernoulli and the clock hypothesis; it is \emph{not} a proof of gravitation.
\section{Gauge-invariant clock difference and two-surface toy}
The proposed coupling requires an as-yet-unverified gauge transformation of the atomic phases:
\begin{align}
\Theta_{AB}&=\theta_B-\theta_A-\sum_{e\in\mathcal P}\vartheta_e,\\
\dot\Theta_{AB}&=\Omega_B^{(0)}N_B-\Omega_A^{(0)}N_A
+\sum_{e\in\mathcal P}E_e.
\end{align}
In the \emph{classical scalar test only} the two-sheet free-energy density is evaluated numerically from
\[
\frac{\Delta\mathcal F}{A}=\frac{T}{4\pi}\int_0^\infty k\,
\ln\!\left[1-r_1r_2\exp(-2ka)\right]dk.
\]
The toy reflectivities $r_j$ are model inputs and are not deduced from conducting metal atoms. There is no claimed quantum zero-point normalization.
\section{PKLSA geometry and dynamical resolution}
The source is a real $N=300$ centerline, but the filament model is a reduced regularized ODE with RK4, not a 3D Euler PDE. All three spatial grids use the same original source, the same $\epsilon=0.12$, $\Gamma=1$, and $T=0.04$. No grid-dependent core fitting is permitted. Its dimensionless velocity kernel is
\[
\mathbf u(\mathbf x)=\frac{\Gamma}{4\pi}\sum_j
\frac{\Delta\mathbf X_j\times(\mathbf x-\mathbf X_{j+\frac12})}
{\big(|\mathbf x-\mathbf X_{j+\frac12}|^2+\epsilon^2\big)^{3/2}}.
\]
\begin{tabular}{@{}p{0.64\linewidth}r@{}}\toprule
Quantity & Registered value \\\midrule
Final time $T$ & @@T@@ \\
Time-step relative discrepancy & @@DT@@ \\
Spatial error (75 vs 150) & @@SPATIAL@@ \\
Spatial error (150 vs 300) & @@SPATIALFINE@@ \\
Spatial error (75 vs 300) & @@SPATIALALL@@ \\
Predeclared spatial threshold & $0.05$ \\
Historical 75--150 gate & \textbf{FAIL} \\
\bottomrule\end{tabular}
\section{Independent source provider reconciliation}
A single pre-run source manifest is verified by both the portable and official framework pipelines; each must recheck the exact raw bytes. A raw provider check is \emph{geometry evidence only}, never an independent 3D Euler or Casimir-force certification.
\par\medskip
\begin{tabular}{@{}p{0.33\linewidth}p{0.57\linewidth}@{}}\toprule
Provider status & \nolinkurl{@@PROVIDER@@} \\
Provider SHA-256 & \texttt{@@PROVIDERHASH@@} \\
Provider points & @@PROVIDERPOINTS@@ \\
\bottomrule\end{tabular}
\section{Independently sealed datasets}
The datasets use separate hash manifests. Different discretizations of the same original trefoil are \emph{not} independent upstream providers.
\par\medskip
\begin{tabular}{@{}ll@{}}\toprule Dataset & Seal digest (prefix) \\\midrule
@@SEALS@@
\bottomrule\end{tabular}
\section{Gate ledger}
\footnotesize
\begin{longtable}{@{}p{0.34\linewidth}p{0.14\linewidth}p{0.42\linewidth}@{}}\toprule
Gate & Status & Metric / reason \\\midrule\endhead
@@GATES@@
\bottomrule\end{longtable}
\normalsize
Non-pass gates: @@FAILS@@.
\section{Two-surface synthetic fit}
\begin{tabular}{@{}lll@{}}\toprule Pair & T & Fitted exponent \\\midrule
@@EXPONENTS@@
\bottomrule\end{tabular}
\section{Qualification boundaries and reproducibility}
\begin{itemize}
\item E010/Fremlin evidence is checked using one identical pre-run manifest in portable and framework mode. Verified raw geometry is not physical independent replication. No invented replacement is accepted.
\item No calibrated moving metal surface, atom--link response, normal-mode quantum statistics, independently evaluated Casimir stress, or gravity-equivalence test is available.
\item A065 physical discovery G3 is \textbf{UNRESOLVED / NOT RUN}; a successful program run cannot promote it to PASS.
\item The frozen SST Falsifier Framework v1.0.7 remains external, unmodified, and authoritative when present. Its own TeX report and frozen gate ledger are kept in the per-run framework instance.
\item This \texttt{.tex} contains \textbf{no} \verb|\input|, \verb|\include|, bibliography file, figures, or generated font dependencies. Recompile using \texttt{pdflatex} twice in the same folder.
\item Each execution receives a UTC-stamped and random-suffixed run ID. Export files are opened create-only; previous experiments are never deleted or overwritten.
\end{itemize}
\end{document}
'''
    qualification_file=root/'outputs'/'QUALIFICATION_V032.json'
    if qualification_file.is_file():
        qual=readjson(qualification_file)
        spat=qual['spatial']; provider2=qual['independent_dynamic_simulation']
        more=r'''\section{v0.3.2: Fixed-core spatial convergence and independent simulation provider}
\textbf{The historical 75/150 failure remains registered.}
The $600$-node geometry is a periodic cubic interpolation of the same $300$ PKLSA points, not independent source data.
\[
  X_{2j+1}=\frac{-X_{j-1}+9X_j+9X_{j+1}-X_{j+2}}{16},\qquad X_{2j}=X_j.
\]
For all spatial comparisons the original $T=0.04$, $\Gamma=1$, and $\epsilon=0.12$ remain unchanged. The error statistic is the RMS difference of final node positions divided by the coarse-grid RMS displacement.
\begin{center}\begin{tabular}{lll}\toprule
Pair & Relative error & Gate at $5\%$ \\\midrule
@@SPATROWS@@
\bottomrule\end{tabular}\end{center}
\textbf{Time refinement:} $N=300$, $4\to8$ steps: @@TIME300@@; $N=600$, $8\to16$ steps: @@TIME600@@.\par
\textbf{Independent Fremlin lane:} @@FREMLIN@@. Source label alone is not accepted: raw SHA-256, a separate C++17 executable, and spatial and temporal controls must all be verified. Missing raw geometry means unresolved, not a simulated pass.\par
\textbf{Physical scope:} these are two independent upstream geometries and independently implemented filament-ODE numerics only if Fremlin passes. They do not certify a second full Euler/PDE dynamics provider, Casimir stress, or gravitation.
'''
        lines=[]
        for key in ['75_vs_150','150_vs_300','300_vs_600','75_vs_300']:
            row=spat['pairs'][key]
            lines.append(key.replace('_',r'\_')+' & '+f"{row['relative_to_coarse_displacement']:.7g}"+' & '+row['status_at_five_percent']+r' \\')
        more=more.replace('@@SPATROWS@@','\n'.join(lines))
        more=more.replace('@@TIME300@@',f"{spat['time_refinement_relative']['N300_4_vs_8']:.7g}")
        more=more.replace('@@TIME600@@',f"{spat['time_refinement_relative']['N600_8_vs_16']:.7g}")
        more=more.replace('@@FREMLIN@@',escape_tex(provider2['status']))
        tex=tex.replace(r'\end{document}',more+r'\end{document}')
    route_file=root/'outputs'/'ROUTING_V033_RESULT.json'
    if route_file.is_file():
        rt=readjson(route_file)
        extra=(r'\section{v0.3.3: Gate-routing qualification}'
               +r'\textbf{Historic G2 remains FAIL.} The G3 execution decision uses only a precommitted G1/G10 refined numerical prerequisite and strict analytic/temporal/provenance guards; it is NOT a physical PASS. '
               +r'\par Routing ready: '+escape_tex(rt['ready_for_G3_evaluation'])
               +r'. G3 permitted outcome: '+escape_tex(rt['g3_permitted_outcome'])
               +r'. Physical force status: '+escape_tex(rt['physical_force_status'])
               +r'. Routing precommit SHA-256: '+escape_tex(rt['prereg_sha256'])
               +r'. GPU G6/G7 remain disabled in CPU profile.')
        tex=tex.replace(r'\end{document}',extra+'\n'+r'\end{document}')
    histfile=root/'outputs/HISTORICAL_V034_RESULT.json'
    if histfile.is_file():
        hh=readjson(histfile)
        htext=(r'\section{v0.3.4 Historical trefoils: 2015 Fourier and torus seeds}'
               +r'\textbf{Scope:} Both samples are historical initial geometric curves, not relaxed PKLSA solutions, not a physical core or Euler validation. Their coordinate units are unscaled dimensionless values. '
               +r'\par Precommit SHA-256: '+escape_tex(hh['precommit_sha256'])+r'. '
               +r'\par Numerical backend: '+escape_tex(hh['native_qualification']['status'])+'.')
        for name,geo in hh['geometry_sources'].items():
            htext+=r'\subsection{'+escape_tex(name)+'}'
            htext+='Historic page '+str(geo['historic_page'])+'. '
            htext+='Formula: '+escape_tex(geo['formula'])+r'.\par '
            htext+='Analytic length = '+f"{geo['parametric_length_independent']:.8f}"+r'; mean edge N600 = '+f"{geo['N600']['average_edge']:.6g}"+'. '
            if hh['native_qualification']['status']=='EXECUTED':
                run=hh['native_qualification']['seeds'][name]
                for pair,metric in run['spatial'].items():
                    htext+=r'\par '+escape_tex(pair)+': '+f"{metric['relative_to_coarse_displacement']:.7g}"+' ('+metric['status']+'). '
                htext+=r'\par Python/C++ parity (N150 RMS) = '+f"{run['python_cpp_parity_N150_rms']:.4g}"+'. '
                for ev,sens in run['core_sensitivity'].items():
                    htext+=r'\par $\epsilon='+escape_tex(ev)+'$: relative difference = '+f"{sens['relative_to_baseline_displacement']:.7g}"+'. '
        htext+=r'\par\textbf{No physical force claims:} gravity, Casimir, metal boundary conditions, mass, and full Euler PDE are UNRESOLVED.'
        tex=tex.replace(r'\end{document}',htext+'\n'+r'\end{document}')
    substitutions = {
        '@@RUN@@': escape_tex(run_id),
        '@@MODE@@': escape_tex(label),
        '@@FRAMEWORK@@': escape_tex(frame_state),
        '@@SUMMARY@@': escape_tex(summary.get('status','unknown')),
        '@@SOURCEHASH@@': escape_tex(str(src.get('raw_sha256','UNRECORDED'))[:24]+'...'),
        '@@T@@': fmt(dyn.get('t_final','?')),
        '@@DT@@': fmt(dyn.get('relative_discretization_error','?')),
        '@@SPATIAL@@': fmt(dyn.get('spatial_75_150_relative_displacement','?')),
        '@@SPATIALFINE@@': fmt(dyn.get('spatial_150_300_relative_displacement','?')),
        '@@SPATIALALL@@': fmt(dyn.get('spatial_75_300_relative_displacement','?')),
        '@@PROVIDER@@': str(provider.get('status','NOT_RUN')),
        '@@PROVIDERHASH@@': escape_tex(str(provider.get('manifest_sha256','?'))[:24]),
        '@@PROVIDERPOINTS@@': fmt(provider.get('point_count','unavailable')),
        '@@SEALS@@': '\n'.join(seal_rows),
        '@@GATES@@': '\n'.join(gate_rows),
        '@@FAILS@@': fail_text,
        '@@EXPONENTS@@': '\n'.join(exponent_rows),
    }
    for key, value in substitutions.items(): tex = tex.replace(key, value)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open('x',encoding='utf-8') as fh: fh.write(tex)
    return report_path


def compile_tex(tex_path: Path, pdf_path: Path) -> dict:
    tex_path=Path(tex_path); pdf_path=Path(pdf_path)
    engine=shutil.which('pdflatex')
    if not engine:
        return {'success':False,'reason':'PDFLATEX_NOT_INSTALLED','tex':str(tex_path)}
    with tempfile.TemporaryDirectory(prefix='a065_tex_') as tmp:
        tmpdir=Path(tmp)
        runs=[]
        for _ in range(2):
            cp=subprocess.run([engine,'-interaction=nonstopmode','-halt-on-error',
                '-output-directory',str(tmpdir),str(tex_path)],
                cwd=str(tex_path.parent),capture_output=True,text=True,timeout=70)
            runs.append(cp.returncode)
            if cp.returncode != 0:
                return {'success':False,'reason':'LATEX_COMPILATION_ERROR',
                        'latex_tail':(cp.stdout+'\n'+cp.stderr)[-3000:], 'tex':str(tex_path)}
        produced=tmpdir/(tex_path.stem+'.pdf')
        if not produced.is_file():
            return {'success':False,'reason':'LATEX_PDF_MISSING','tex':str(tex_path)}
        with produced.open('rb') as fin, pdf_path.open('xb') as fout: shutil.copyfileobj(fin,fout)
    return {'success':True,'renderer':'SELF_CONTAINED_PDFLATEX',
            'pdf':str(pdf_path),'tex':str(tex_path), 'pdf_sha256':sha(pdf_path.read_bytes())}
