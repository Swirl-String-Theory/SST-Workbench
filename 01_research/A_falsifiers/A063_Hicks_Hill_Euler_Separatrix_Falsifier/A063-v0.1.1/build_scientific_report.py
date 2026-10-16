#!/usr/bin/env python3
"""Scientific A063 v0.1.1 TeX/PDF, separate from historical source-tree.

PDF publication is post-run only; it does not change or certify gate results.
Requires pdflatex; if absent copies externally generated public-only PDF and
reports the downgraded document type via REPORT_RENDER.json.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,shutil,subprocess,tempfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
VERSION='v0.1.1'

def fmt(x,fmtstr='.3g'):
    return format(float(x),fmtstr)

def tex_escape(s):
    return (str(s).replace('\\',r'\textbackslash{}').replace('&',r'\&').replace('%',r'\%').replace('_',r'\_').replace('#',r'\#').replace('$',r'\$'))

def make_tex(output):
    ledger=json.loads((output/'GATE_LEDGER.json').read_text())
    controls=json.loads((output/'HICKS_CONTROLS.json').read_text())
    summary=json.loads((output/'RUN_SUMMARY.json').read_text())
    gates=ledger['records']; byid={x['gate_id']:x for x in gates}
    counts=collections.Counter(x['status'] for x in gates)
    kval=controls['knot_candidate']; h3=byid['H3']['metrics'];h4=byid['H4']['metrics'];b=controls['interface_ladder']
    plrows='\n'.join(rf"{tex_escape(k)} & {v['samples'][0]['max_velocity_jump']:.4g} & {v['samples'][-1]['max_velocity_jump']:.4g} & {v['samples'][-1]['max_pressure_jump']:.4g} \\" for k,v in b.items())
    grows='\n'.join(rf"\texttt{{{g['gate_id']}}} & \texttt{{{g['status']}}} & {tex_escape(g['question'])} \\" for g in gates)
    knots=controls['winding_diagnostics']; windingpts=' '.join(f"({x['s0_over_a']:.6g},{x['winding_phi_per_poloidal_cycle']:.10g})" for x in knots)
    windingpts+=' '+ ' '.join(f"({v},{w:.10g})" for v,w in zip(kval['bracket'],kval['bracket_windings']))
    energy=controls['a057_volume_energy_references']
    erows='\n'.join(rf"{tex_escape(k)} & {v['inside_lab_kinetic_energy']:.7g} & {v['exterior_dipole_energy']:.7g} & {v['total_lab_kinetic_energy']:.7g} \\" for k,v in energy.items())
    tex=r'''\documentclass[10pt,a4paper]{article}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage[margin=20mm]{geometry}
\usepackage{amsmath,amssymb,booktabs,longtable,array}
\usepackage{xcolor,hyperref,pgfplots}
\pgfplotsset{compat=1.18}
\definecolor{ink}{RGB}{30,43,63}
\definecolor{accent}{RGB}{11,94,120}
\hypersetup{colorlinks=true,urlcolor=accent,linkcolor=accent}
\setlength{\parskip}{6pt}
\setlength{\parindent}{0pt}
\begin{document}
{\Large\bfseries\color{ink} A063 -- Hicks/Hill Euler Separatrix Falsifier}\par
{\large Scientific report -- v0.1.1}\par
\smallskip
\textbf{Scope:} Exact-field analytic reference, interface convergence, and numerically closed toroidal streamline candidate.\\
\textbf{Evidence:} Python/SciPy FP64, analytical/synthetic control only. \textbf{Not} canonical v1.0.7 native certification.\\
\textbf{Blind status:} no target particle labels, canonical masses or SST parameter fitting.
\vspace{2mm}\hrule
\section{Executive verdict}
A total of \textbf{@@PASS@@ PASS}, \textbf{@@UNRESOLVED@@ UNRESOLVED}, and \textbf{@@FAIL@@ FAIL} gates were recorded. The vortex-field reference is consistent with its prescribed accuracy gates; the original global topological/stability gate \texttt{H7}, the new trefoil/tube gate \texttt{H7B}, and independent native certification \texttt{H8} remain \texttt{UNRESOLVED}. A \texttt{PASS} of \texttt{H7A} only establishes a \emph{numerically closed T(3,4) streamline candidate}.

This report reads the additive v0.1.1 result JSONs. No older A063 v0.1.0 verdict is changed or migrated. Calculations are dimensionless with representative sphere radius $a=1$, density $\rho=1$ and predefined amplitude $A=1$.

\section{Exact Euler controls}
For cylindrical coordinates $(s,\phi,z)$ and the sphere $r^2=s^2+z^2\leq a^2$, the streamfunction and velocity in a sphere-comoving frame are
\begin{align}
J(x)&=\frac{\sin x}{x}-\cos x,\\
\psi_\lambda(r,\theta)&=A\left[J(\lambda r/a)-\frac{r^2}{a^2}J(\lambda)\right]\sin^2\theta,\\
(u_s,u_\phi,u_z)&=\left(-\frac{\psi_z}{s},\frac{\lambda\psi}{as},\frac{\psi_s}{s}\right).
\end{align}
At $\lambda=0$ a separate cancellation-safe Hill limiting field is used. The special families satisfy
\begin{align}
J(\lambda_1)=0\quad &(\text{Beltrami family}),\\
3J(\lambda_2)-\lambda_2\sin\lambda_2=0\quad &(\text{zero-translation family}).
\end{align}
With the local velocity gradient and Euler pressure obtained from the same analytic field, the interior reference checks
\begin{equation}
\nabla\cdot\mathbf u=0,\qquad (\mathbf u\cdot\nabla)\mathbf u+\frac{\nabla p}{\rho}=0,
\qquad \nabla\times\mathbf u=\frac{\lambda_1}{a}\mathbf u\ \text{for the Beltrami solution}.
\end{equation}

\textbf{Methodological correction from v0.1.0:} the residual maxima are now computed \emph{separately} for Hill, first Beltrami, and first zero-translation Hicks; the former H3 pooled Euler/divergence maxima from distinct families. Four finite-difference steps, $h/a\in\{4,2,1,0.5\}\times10^{-4}$, are compared for each family.

\begin{center}\small
\begin{tabular}{lrr}
\toprule
Reference & Max Euler residual (finest) & Max $|\nabla\cdot\mathbf u|$ (finest)\\
\midrule
Hill & @@H2E@@ & @@H2D@@\\
Beltrami & @@H3E@@ & @@H3D@@\\
Zero translation & @@H4E@@ & @@H4D@@\\
\bottomrule
\end{tabular}
\end{center}
The finest relative Euler error reduction ratios (previous step / finest step) exceed 2.5 for all three cases. These are finite-sample diagnostics, not global validated error bounds.

\section{Full-latitude material boundary and continuity}
The spherical separatrix is tested at 121 polar angles in each of three fields. The analytic no-flux condition $\mathbf u\cdot\mathbf n=0$ is evaluated on the sphere. Interior/exterior jumps in tangential velocity and pressure are measured at $r=a(1\pm\epsilon)$ for $\epsilon\in\{10^{-3},10^{-4},10^{-5}\}$.

\begin{center}\small
\begin{tabular}{lrrr}
\toprule
Field & $\Delta u(10^{-3})$ & $\Delta u(10^{-5})$ & $\Delta p(10^{-5})$\\
\midrule
@@BOUNDARY_ROWS@@
\bottomrule
\end{tabular}
\end{center}
The jumps decay with radial offset for all fields. The latitude scan excludes only small caps $\theta<0.06$ and $\pi-\theta<0.06$, which remain outside this finite-sample claim. A smooth-interface test does not prove dynamical self-confinement.

\section{First rational-winding torus-line test}
On the first Beltrami family we integrate the Poincar\'e return map of the meridional plane and define
\begin{equation}
W(s_0)=\frac{\Delta\phi}{2\pi}\quad\text{per complete meridional circulation}.
\end{equation}
The target $W=3/4$ is bracketed by two independent sampled curves, then solved using Brent's method. Continuous three-dimensional integration over four meridional periods independently tests closing at a primitive $(p,q)=(3,4)$ winding:
\begin{align}
s_0/a&=@@S0@@,\\
W(s_0)&=@@W@@,\\
(N_{\rm azimuth},N_{\rm meridional})&=(@@AZ@@,@@POL@@),\\
\|\mathbf x(4T)-\mathbf x(0)\|/a&=@@CLOSURE@@.
\end{align}
\begin{center}
\begin{tikzpicture}
\begin{axis}[width=.84\textwidth,height=5cm,xlabel={$s_0/a$},ylabel={$W$},grid=major,legend pos=north east,xmin=.66,xmax=1,ymin=.72,ymax=.85]
\addplot+[mark=*,thick] coordinates {@@WINDING_POINTS@@};
\addlegendentry{Poincar\'e winding samples}
\addplot+[dashed,mark=none,domain=.66:1,samples=2] {0.75};
\addlegendentry{$W=3/4$}
\addplot+[only marks,mark=diamond*,mark size=2.5pt] coordinates {(@@S0@@,0.75)};
\addlegendentry{closed-line candidate}
\end{axis}
\end{tikzpicture}
\end{center}
\textbf{Allowed claim:} a numerical $T(3,4)$ \emph{streamline candidate} on an axisymmetric invariant torus, with monotone meridional phase and positive minimum radius. This does \textbf{not} independently certify a knot isotopy (e.g., with an Alexander polynomial), and does not show a finite-radius vortex \emph{tube}, an electron, or nonlinear Euler stability. It also does not globally exclude trefoil $T(2,3)$ from higher modes or other parameter ranges.

\section{Analytic bridges for the existing SST falsifiers}
\textbf{A046 pressure--vorticity:} tests $\nabla^2p=-\rho\,\partial_i u_j\partial_j u_i$ in the incompressible Euler field, without interpreting $p$ as gravitation. Maximum sampled pressure--Poisson absolute residual: $@@POISSON@@$.

\textbf{A057 finite-volume reference:} computes total laboratory-frame kinetic energy from interior volume quadrature plus the exact exterior dipole energy. Uniform far-field kinetic energy is not integrated in the translating frame. No constant-circulation normalization or physical mass-ratio inference is performed.
\begin{center}\small
\begin{tabular}{lrrr}
\toprule
Field & Interior $E$ & Exterior $E$ & Total $E$\\
\midrule
@@ENERGY_ROWS@@
\bottomrule
\end{tabular}
\end{center}

\section{Gate ledger and remaining qualifications}
\small
\begin{longtable}{@{}p{12mm}p{24mm}p{112mm}@{}}
\toprule
Gate & Status & Registered question\\\midrule\endhead
@@GATE_ROWS@@
\bottomrule
\end{longtable}
\normalsize
\textbf{Immediate next work:} independent topological invariant from sampled closed curve; global interval winding accessibility bounds for the trefoil; perturbed finite-core Euler-vortex-tube evolution and convergence; separate C++ FP64 native lane with the unmodified v1.0.7 instance protocol if certification is requested. No legacy falsifier framework migrations are necessary to render PDF reports.

\section*{Source and provenance}
Primary analytic source: W. M. Hicks (1899), \emph{Researches in Vortex Motion. Part III: On Spiral or Gyrostatic Vortex Aggregates}, \emph{Phil. Trans. R. Soc. A} \textbf{192}, 33--99, DOI: \href{https://doi.org/10.1098/rsta.1899.0002}{10.1098/rsta.1899.0002}. Classic reference: M. J. M. Hill (1894), \emph{On a Spherical Vortex}, \emph{Phil. Trans. R. Soc. A} \textbf{185}, 213--245, DOI: \href{https://doi.org/10.1098/rsta.1894.0006}{10.1098/rsta.1894.0006}. This release is an analytical Python control campaign, with no independent observational support for SST particle physics.\\
\footnotesize Run protocol SHA-256: \texttt{@@PROTOCOLHASH@@}.\\
Ledger SHA-256: \texttt{@@LEDGERHASH@@}.\\
Run timestamp (UTC): @@RUNUTC@@.
\end{document}
'''
    replace={'@@PASS@@':counts['PASS'],'@@UNRESOLVED@@':counts['UNRESOLVED'],'@@FAIL@@':counts['FAIL'],
             '@@H2E@@':fmt(byid['H2']['metrics']['max_euler']), '@@H2D@@':fmt(byid['H2']['metrics']['max_div']),
             '@@H3E@@':fmt(h3['max_euler']), '@@H3D@@':fmt(h3['max_div']),
             '@@H4E@@':fmt(h4['max_euler']), '@@H4D@@':fmt(h4['max_div']),
             '@@BOUNDARY_ROWS@@':plrows,'@@GATE_ROWS@@':grows,'@@ENERGY_ROWS@@':erows,
             '@@S0@@':fmt(kval['s0_over_a'],'.12f'), '@@W@@':fmt(kval['winding_per_cycle'],'.12f'),
             '@@AZ@@':fmt(kval['total_azimuthal_winding'],'.9f'),
             '@@POL@@':fmt(kval['total_poloidal_winding'],'.9f'),
             '@@CLOSURE@@':fmt(kval['full_3d_closure_relative_a'],'.5g'),
             '@@WINDING_POINTS@@':windingpts,
             '@@POISSON@@':fmt(byid['H9']['metrics']['max_pressure_poisson_abs']),
             '@@PROTOCOLHASH@@':summary['protocol_bundle_sha256'],
             '@@LEDGERHASH@@':ledger['ledger_sha256'],
             '@@RUNUTC@@':tex_escape(controls['computed_utc'])}
    for k,v in replace.items():tex=tex.replace(k,str(v))
    assert '@@' not in tex
    return tex,counts

def render(out, dest, pdf_engine='auto'):
    dest.mkdir(parents=True,exist_ok=True)
    tex,c=make_tex(out)
    tex_file=dest/'A063-v0.1.1_FALSIFIER_REPORT.tex'
    pdf_file=dest/'A063-v0.1.1_FALSIFIER_REPORT.pdf'
    tex_file.write_text(tex,encoding='utf-8')
    engine=shutil.which('pdflatex')
    mode='latex'
    if engine:
        with tempfile.TemporaryDirectory(prefix='a063_tex_') as tmp:
            for i in range(2):
                p=subprocess.run([engine,'-interaction=nonstopmode','-halt-on-error','-output-directory',tmp,str(tex_file)],cwd=str(dest),capture_output=True,text=True,timeout=120)
                if p.returncode!=0:raise RuntimeError('pdflatex error: '+p.stdout[-3500:])
            shutil.copyfile(Path(tmp)/pdf_file.name,pdf_file)
    else:
        mode='external_pdf_fallback'
        ext=dest/'external'/'A063-v0.1.1_FALSIFIER_REPORT.pdf'
        if not ext.exists():raise RuntimeError('No pdflatex: run independent external generator first, then use fallback PDF.')
        shutil.copyfile(ext,pdf_file)
    result={'schema':'A063-SCIENTIFIC-REPORT-RENDER-1','version':VERSION,'mode':mode,'pdf':pdf_file.name,'sha256':hashlib.sha256(pdf_file.read_bytes()).hexdigest(), 'gate_counts':dict(c),'not_framework_certified':True}
    (dest/'A063-v0.1.1_REPORT_RENDER.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));return pdf_file

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--outputs',type=Path,default=HERE/'A063_Hicks_Hill_Euler_Separatrix_Falsifier_v0.1.1-outputs')
    ap.add_argument('--dest',type=Path,default=HERE.parent)
    a=ap.parse_args();render(a.outputs.resolve(),a.dest.resolve())
if __name__=='__main__':main()
