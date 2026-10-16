"""Scientific LaTeX+PDF report for A063 v0.2.1. PDF fallback if LaTeX absent."""
from __future__ import annotations
import json,os,subprocess,shutil
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'A063_Hicks_Invariant_Surface_v0.2.1-outputs'
REP=ROOT/'A063-v0.2.1-reports'

def esc(s):
    return str(s).replace('\\',r'\textbackslash{}').replace('_',r'\_').replace('%',r'\%').replace('&',r'\&').replace('#',r'\#')

def report():
    REP.mkdir(exist_ok=True)
    ctrl=json.loads((OUT/'INVARIANT_SURFACE_CONTROLS.json').read_text())
    ledger=json.loads((OUT/'GATE_LEDGER.json').read_text())
    summ=json.loads((OUT/'RUN_SUMMARY.json').read_text())
    c=np.load(OUT/'CANDIDATE_LINE.npz');mesh=np.load(OUT/'PSI_LEVEL_MESH.npz')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'figure.dpi':140})
    fig,ax=plt.subplots(figsize=(6.8,4.7))
    for i,label in enumerate(('0.90 psi0','1.00 psi0','1.10 psi0')):
        s=mesh[f'level_{i}_s'];z=mesh[f'level_{i}_z']
        ax.plot(np.r_[s,s[0]],np.r_[z,z[0]],label=label,lw=1.8)
    ax.plot([.6106],[0],marker='x',color='black',label='meridional center')
    ax.plot([ctrl['s0_over_a']],[0],marker='o',color='black',ms=4,label='T(3,4) equatorial start')
    ax.set(xlabel='cylindrical radius s / a',ylabel='height z / a',title='Three regular Hicks streamfunction contours')
    ax.set_aspect('equal');ax.grid(alpha=.2);ax.legend(fontsize=7,loc='best')
    fig.tight_layout();fig.savefig(REP/'psi_meridional_levels.png',dpi=190);plt.close(fig)
    fig=plt.figure(figsize=(7.0,5.0));ax=fig.add_subplot(projection='3d')
    s=mesh['level_1_s'][::4];z=mesh['level_1_z'][::4]
    phi=np.linspace(0,2*np.pi,70)
    X=s[:,None]*np.cos(phi[None,:]);Y=s[:,None]*np.sin(phi[None,:]);Z=np.broadcast_to(z[:,None],X.shape)
    ax.plot_surface(X,Y,Z,alpha=.17,color='cadetblue',linewidth=0,shade=False)
    xyz=c['xyz'];ax.plot(xyz[:,0],xyz[:,1],xyz[:,2],linewidth=1.6,color='crimson',label='T(3,4) streamline')
    ax.plot(.6106*np.cos(phi),.6106*np.sin(phi),0*phi,color='navy',ls='--',lw=1,label='unknotted solid-torus core')
    ax.set(xlabel='x/a',ylabel='y/a',zlabel='z/a',title='T(3,4) streamline ON an unknotted psi-level torus')
    ax.view_init(elev=26,azim=38)
    try:ax.set_box_aspect((1,1,.8))
    except AttributeError:pass
    ax.legend(loc='upper center',fontsize=7)
    fig.tight_layout();fig.savefig(REP/'unknotted_psi_torus_T34.png',dpi=190);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(8.7,3.3))
    for lev in ctrl['levels']:
        hs=[v['fd_h_over_a'] for v in lev['normal_flux_fd']]
        fs=[v['max_material_flux_relative'] for v in lev['normal_flux_fd']]
        axes[0].loglog(hs,fs,marker='o',label=f"{lev['psi_factor']:.2f} psi0")
    axes[0].set(xlabel='finite difference step / a',ylabel='max |u.n| / u_rms',title='Independently differenced normal flux')
    axes[0].grid(True,which='both',alpha=.25);axes[0].legend(fontsize=7)
    fac=[v['psi_factor'] for v in ctrl['levels']]
    vals=[v['winding']['W'] for v in ctrl['levels']]
    axes[1].plot(fac,vals,'o-');axes[1].axhline(.75,ls='--',color='gray',label='T(3,4) rational rotation')
    axes[1].set(xlabel='psi / psi0',ylabel='azimuth/poloidal winding W',title='Neighboring invariant-torus pitch')
    axes[1].legend(fontsize=7);axes[1].grid(alpha=.25)
    fig.tight_layout();fig.savefig(REP/'flux_and_shear.png',dpi=180);plt.close(fig)
    ng=ledger['counts']
    gate_rows='\n'.join(f"{esc(g['gate_id'])} & {esc(g['status'])} & {esc(g['question'])} \\\\" for g in ledger['records'])
    level_rows='\n'.join(
        f"{lev['psi_factor']:.2f} & {lev['meridional']['s_min']:.5f} & {lev['meridional']['sphere_clearance_min']:.5f} & {lev['winding']['W']:.9f} & {lev['normal_flux_fd'][0]['max_material_flux_relative']:.3e} \\\\"
        for lev in ctrl['levels'])
    latex=r'''\documentclass[10pt,a4paper]{article}
\usepackage[margin=20mm]{geometry}
\usepackage[T1]{fontenc}
\usepackage{lmodern,amsmath,amssymb,booktabs,longtable,graphicx,array,xcolor,hyperref,float}
\definecolor{navy}{RGB}{24,61,91}
\hypersetup{colorlinks=true,urlcolor=navy,linkcolor=navy,pdftitle={A063 v0.2.1 - Hicks invariant-surface qualification}}
\setlength{\parindent}{0pt}\setlength{\parskip}{5pt}
\begin{document}
{\Large\bfseries A063 v0.2.1 --- Hicks invariant-surface qualification}\par
{\small \textit{Analytical reference (selected T34 target); parent v0.2.0 preserved; no v1.0.7 certification.}}\par
\hrule\smallskip
\textbf{New gates: @PASS@ PASS / @FAIL@ FAIL / @UNR@ UNRESOLVED.}
\section*{Scientific question and preregistered hypotheses}
Does the closed $T(3,4)$ Beltrami vortex-line orbit admit a finite smooth stationary material/vorticity surface whose \emph{solid-torus core} is also knotted, and can this be certified as nonlinearly stable under coupled perturbed 3D Euler evolution? We contrast two constructions: (i) the previously failed constant-radius tube centered on the knot and (ii) regular stationary Hicks level sets $\psi=\psi_0$. The latter are not assumed to be knotted tubes.
\begin{align}
\psi(s,z)&=A\big[J(\lambda r/a)-(r/a)^2J(\lambda)\big]s^2/r^2,\\
J(x)&=\frac{\sin x}{x}-\cos x,\quad r=\sqrt{s^2+z^2},\quad\lambda=4.4934094579,\\
u_s&=-\frac{1}{s}\partial_z\psi,\quad u_z=\frac1s\partial_s\psi,\quad
u_\phi=\frac{\lambda\psi}{as},\quad\boldsymbol\omega=(\lambda/a)\mathbf u.
\end{align}
Therefore $\mathbf u\cdot\nabla\psi=0$ and $\boldsymbol\omega\cdot\nabla\psi=0$ for the exact first-Beltrami Hicks branch, wherever $\nabla\psi\ne0$. We independently evaluate numerical normals using centered derivatives of analytic $\psi$ against the separately evaluated analytic velocity.
\section*{1. Explicit regular level surfaces}
The vortex-line initial position $s_0/a=@S0@$, and its reconstructed level is $\psi_0=@PSI0@$. We solve $\psi(s_c+r(\theta)\cos\theta,r(\theta)\sin\theta)=q\psi_0$ for $q\in\{0.9,1,1.1\}$, with 96, 192 and 384 meridional samples. The radial solutions are single-valued and strictly positive in the tested intervals. Revolving each curve around the symmetry axis yields a regular embedded torus.
\begin{table}[H]\centering\small\begin{tabular}{rrrrr}\toprule
$\psi/\psi_0$ & $s_{\min}/a$ & sphere clearance $/a$ & $W$ & max $|u_n|/u_{\rm rms}$ \\
\midrule
@LEVELROWS@
\bottomrule\end{tabular}\end{table}
\begin{figure}[H]\centering\includegraphics[width=.69\linewidth]{psi_meridional_levels.png}\caption{Closed nested meridional $\psi$ contours. Each avoids the axis $s=0$ and the sphere boundary.}\end{figure}
\section*{2. Topology: unknotted invariant torus, knotted line ON the torus}
The meridional contours are star-shaped about $s=s_c,z=0$, and can be continuously deformed to a small circle by $r_t(\theta)=(1-t)r(\theta)+tr_*$ without touching $s=0$. Revolution constructs an explicit isotopy to the \textbf{standard, unknotted solid torus}. Its core is a planar circle $C(\phi)=(s_c\cos\phi,s_c\sin\phi,0)$, an unknot. In contrast, the original $T(3,4)$ trajectory winds three times azimuthally and four times meridionally on the \emph{boundary} $\psi=\psi_0$. The torus is not a knotted tubular neighborhood whose solid-torus core is $T(3,4)$.
\begin{figure}[H]\centering\includegraphics[width=.73\linewidth]{unknotted_psi_torus_T34.png}\caption{An invariant standard torus (translucent), the red knotted vortex line, and the dashed unknotted circle that is the solid-torus core.}\end{figure}
\section*{3. Material and vorticity flux}
The exact invariant surface has zero normal flux. A separate numerical check yields the normal-velocity values above; Richardson-like reduction across finite-difference steps checks convergence to zero. Since $\omega=(\lambda/a)u$, the exact vorticity-normal flux is zero too. This is \textbf{not} a localized vortex tube: the volume enclosed is a standard solid torus and the original Hicks flow has distributed vorticity throughout the spherical vortex aggregate.
\begin{figure}[H]\centering\includegraphics[width=.88\linewidth]{flux_and_shear.png}\caption{FD-normal flux convergence (left) and invariant-torus winding shear (right). Winding shear is kinematic and is not a 3D Euler instability growth rate.}\end{figure}
\section*{4. Frozen parent evidence and continuation semantics}
Parent v0.2.0 gate statuses were loaded from byte-hashed files, checked against its original gate ledger and source-seal hash, and \emph{not recomputed or rewritten}. The failed steady constant-normal-radius tube (T5 FAIL) and constant rotation of neighbor lines (T6 FAIL) remain historical results. A v0.2.1 S6 FAIL specifically rejects \emph{the psi-level torus as a knotted-core construction}; it is not a proof that no other knotted material surface could exist.
\section*{5. New gate ledger}
\small\begin{longtable}{p{.07\linewidth}p{.14\linewidth}p{.69\linewidth}}\toprule
Gate & Status & Qualification \\\midrule
@GATEROWS@
\bottomrule\end{longtable}\normalsize
\section*{6. Remaining scientific blockers}
A complete falsifier of general finite-core vortex-tube persistence must construct a localized finite-vorticity field, a nonaxisymmetric material boundary with independently checked knot type, and a \emph{coupled 3D incompressible Euler perturbation/pressure evolution}. Register perturbations and grid resolutions in advance; monitor div($u$), energy, helicity, knot/link invariants, tube flux, boundary clearance and error convergence for at least ten core periods. None of these certifications was executed in v0.2.1. This is an analytical/numerical \texttt{REFERENCE\_ONLY} package, not an official v1.0.7 FREEZE/CERTIFY instance.
\textbf{Conclusion.} Smooth stationary Hicks $\psi$-tori \emph{do} exist and are material/vorticity-tangent. They are unknotted ordinary tori of revolution. A $T(3,4)$ trajectory on such a surface does not supply a stable isolated $T(3,4)$ vortex-tube core. General finite-core existence and time-dependent stability remain \textbf{UNRESOLVED}.
\section*{References}
W. M. Hicks, \emph{Researches in Vortex Motion III} (1899), \href{https://doi.org/10.1098/rsta.1899.0002}{doi:10.1098/rsta.1899.0002}. A063 v0.2.0 local archival evidence, byte-bound to v0.2.1 in \texttt{baseline/}.
\end{document}
'''
    for k,v in {'@PASS@':ng['PASS'],'@FAIL@':ng['FAIL'],'@UNR@':ng['UNRESOLVED'],
                '@PSI0@':f'{ctrl["candidate_psi"]:.12f}','@S0@':f'{ctrl["s0_over_a"]:.10f}',
                '@LEVELROWS@':level_rows,'@GATEROWS@':gate_rows}.items():latex=latex.replace(k,str(v))
    (REP/'A063-v0.2.1_FALSIFIER_REPORT.tex').write_text(latex,encoding='utf-8')
    if shutil.which('pdflatex'):
        (REP/'A063-v0.2.1_FALSIFIER_REPORT.pdf').unlink(missing_ok=True)
        for _ in range(2):
            p=subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error','-output-directory',str(REP),
                str(REP/'A063-v0.2.1_FALSIFIER_REPORT.tex')],cwd=REP,capture_output=True,text=True)
            if p.returncode:
                print(p.stdout[-1800:]);print(p.stderr[-400:]);break
        if (REP/'A063-v0.2.1_FALSIFIER_REPORT.pdf').exists():
            print('PDF generated using pdflatex');return
    # Self-contained PDF fallback without LaTeX (not a substitute for TeX source)
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    pdf=REP/'A063-v0.2.1_FALSIFIER_REPORT.pdf'
    doc=SimpleDocTemplate(str(pdf));styles=getSampleStyleSheet();story=[]
    story.append(Paragraph('A063 v0.2.1 - Hicks invariant-surface falsifier',styles['Title']))
    story.append(Paragraph(f'New gates: {ng["PASS"]} PASS / {ng["FAIL"]} FAIL / {ng["UNRESOLVED"]} UNRESOLVED',styles['Heading2']))
    for img in ('psi_meridional_levels.png','unknotted_psi_torus_T34.png','flux_and_shear.png'):
        story.append(Image(str(REP/img),width=425,height=295));story.append(Spacer(1,10))
    for g in ledger['records']:
        story.append(Paragraph(f"{g['gate_id']} {g['status']}: {g['question']}",styles['BodyText']))
    story.append(Paragraph('Invariant psi tori are unknotted. Isolated knotted-core Euler stability remains UNRESOLVED. Python reference only.',styles['BodyText']))
    doc.build(story);print('PDF generated with fallback backend')
if __name__=='__main__':report()
