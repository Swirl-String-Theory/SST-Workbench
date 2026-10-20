"""Finite-core analytic controls report, independent of physical SST target."""
from pathlib import Path
from .report_pdf import _pdf_text


def write(root, result):
    root=Path(root);reports=root/'reports';reports.mkdir(parents=True,exist_ok=True)
    pdf=reports/'FINITE_CORE_V037_REPORT.pdf'
    tex=reports/'FINITE_CORE_V037_REPORT.tex'
    lines=[('h1','A065-v0.3.7 | Finite-Core Inference Falsifier'),
       ('normal','Status: SYNTHETIC METHOD CHECK. No independent physical PKLSA core source available.'),
       ('normal','Precommit SHA256: '+result['prereg_sha256']),('blank',''),
       ('h2','1. Hypothesis and observables'),
       ('normal','H0: a centerline and circulation alone do not fix a physical vortex core or a universal numerical smoothing epsilon.'),
       ('normal','Gamma and cross-section enstrophy Z are training observables. Held-out radial swirl and circular Euler pressure-gradient controls are never used to infer epsilon.'),
       ('h2','2. Analytical mapping'),
       ('normal','Gaussian omega(r) = Gamma / (pi*a^2) * exp(-r^2/a^2). Z = Gamma^2/(2*pi*a^2); a = Gamma/sqrt(2*pi*Z).'),
       ('normal','Rankine omega(r) = Gamma/(pi*a^2) inside core, zero outside. Z = Gamma^2/(pi*a^2); a = Gamma/sqrt(pi*Z).'),
       ('normal','Rosenhead swirl: v_R = Gamma*r/(2*pi*(r^2+epsilon^2)). Matching near-axis v/r yields epsilon=a; matching half-circulation yields a different epsilon.'),
       ('normal','Radial pressure gradient for stationary azimuthal Euler control: dp/dr = rho*v_theta^2/r.'),
       ('h2','3. Gate results')]
    for g in ('G22','G23','G24','G25','G26','G27'):
        lines.append(('normal',f'{g}: {result[g]}'))
    lines.extend([('normal','G24 FAIL is an expected rejection of universal Rosenhead representation, not a failure of source recovery.'),
        ('h2','4. Independent held-out predictions'),
        ('small','Rows: id / derived a / epsilon by half circulation / Rosenhead swirl error / pressure error / wrong-profile error')])
    for c in result['cases']:
        lines.append(('small',f"{c['id']}: {c['a_derived_from_Gamma_and_Z']:.7f} / {c['epsilon_from_half_circulation']:.7f} / {c['rosenhead_swirl_heldout_relative_RMS']:.3%} / {c['rosenhead_pressure_gradient_heldout_relative_RMS']:.3%} / {c['wrong_profile_negative_control_swirl_relative_RMS']:.3%}"))
    lines.extend([('h2','5. Physical closure blocker'),
        ('normal','Original knot XYZ specifies filament centerline geometry only, not transverse vorticity, cross-section enstrophy, SI dimensions or an independently validated Euler evolution.'),
        ('normal','No identification of a physical SST rc; no pressure-force, surface, Casimir or gravity claim.'),
        ('normal','The synthetic pressure gradient is algebraically generated from the same synthetic swirl field and is not an independent measurement.'),
        ('h2','6. Reproduction'),('normal','Run: run_all.cmd CORE; run_all.cmd SELFTEST; run_all.cmd ALL with frozen SST framework v1.0.7 installed.'),
        ('normal','G26 C++17 is kernel-only; no independent full PDE integration.')])
    _pdf_text(pdf,lines)
    body=r'''\documentclass[11pt,a4paper]{article}
\usepackage[margin=18mm]{geometry}
\usepackage{amsmath,booktabs,longtable,hyperref}
\title{A065-v0.3.7: Finite-Core Inference Falsifier}
\date{2026-10-19}
\begin{document}\maketitle
\section{Hypotheses}
The null states that the centerline and circulation alone cannot identify a physical vortex-core radius or a unique numerical regularizer. All data below are synthetic analytic controls, not measured PKLSA core-vorticity.
\section{Two finite-core models}
\begin{align}
\omega_G(r)&=\frac{\Gamma}{\pi a^2}e^{-r^2/a^2}, & Z_G&=\frac{\Gamma^2}{2\pi a^2}, & a_G&=\frac{\Gamma}{\sqrt{2\pi Z_G}},\\
\omega_R(r)&=\frac{\Gamma}{\pi a^2}\mathbf 1_{r\le a}, & Z_R&=\frac{\Gamma^2}{\pi a^2}, & a_R&=\frac{\Gamma}{\sqrt{\pi Z_R}}.\end{align}
\begin{align}
 v_\theta(r)&=\frac{\Gamma_{\rm enc}(r)}{2\pi r}, &v_{\rm RM}(r)&=\frac{\Gamma r}{2\pi(r^2+\varepsilon^2)}, &\frac{dp}{dr}&=\rho\frac{v_\theta^2}{r}.
\end{align}
Near-axis slope matching fixes $\varepsilon=a$. Half-circulation matching instead yields $\varepsilon=a\sqrt{\ln2}$ for Gaussian and $\varepsilon=a/\sqrt2$ for Rankine. This nonuniqueness is intrinsic to the adopted kernel-equivalence criterion.
\section{Blind gate outcomes (method-only)}
\begin{center}\begin{tabular}{ll}\toprule Gate & Outcome \\\midrule
'''
    for g in ('G22','G23','G24','G25','G26','G27'):
        body+=g+' & '+result[g].replace('_',r'\_')+r' \\'+'\n'
    body+=r'''\bottomrule\end{tabular}\end{center}
\section{Held-out diagnostics}
\small\begin{longtable}{lrrrr}\toprule Case & $a(\Gamma,Z)$ & $\varepsilon_{50\%}$ & swirl RMS & pressure-gradient RMS\\\midrule\endhead
'''
    for x in result['cases']:
        body+=f"{x['id'].replace('_',r'\_')} & {x['a_derived_from_Gamma_and_Z']:.6f} & {x['epsilon_from_half_circulation']:.6f} & {100*x['rosenhead_swirl_heldout_relative_RMS']:.3f}\\% & {100*x['rosenhead_pressure_gradient_heldout_relative_RMS']:.3f}\\%"+r' \\'+'\n'
    body+=r'''\bottomrule\end{longtable}\normalsize
\section{Qualification boundary}
The only recovered quantity is a \emph{profile-conditional dimensionless $a$}. The actual PKLSA knots contain no measured transverse $\omega(r)$ or independent radial pressure profiles. No physical $r_c$, finite-core Euler stability, Casimir, or gravity closure is claimed. The synthetic pressure gradient is computed from the synthetic swirl velocity itself, hence does not count as independent physical replication.
\section{References}
P. G. Saffman, \emph{Vortex Dynamics}, CUP (1992).\\
D. D. Holm, M. Nitsche, V. Putkaradze, \emph{J. Fluid Mech.} \textbf{555}, 149--176 (2006), DOI:10.1017/S0022112006008846.\\
M. Perlman, \emph{J. Comput. Phys.} \textbf{59}, 200--223 (1985), DOI:10.1016/0021-9991(85)90142-1.
\end{document}
'''
    # Report PDF uses a portable stdlib backend, LaTeX remains a full editable source.
    tex.write_text(body,encoding='utf-8')
    return str(pdf)
