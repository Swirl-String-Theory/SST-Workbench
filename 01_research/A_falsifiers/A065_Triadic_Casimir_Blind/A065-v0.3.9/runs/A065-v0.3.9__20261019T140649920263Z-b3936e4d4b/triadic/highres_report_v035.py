"""Standalone PDF and TeX for high-resolution numerical runs (does not require a blind pilot)."""
from __future__ import annotations
import os,json
from pathlib import Path
from .report_pdf import _pdf_text
from .security import readjson


def write(root,mode='HIGHRES'):
    root=Path(root)
    run_id=os.environ.get('SST_A065_RUN_ID')
    if not run_id:raise RuntimeError('No run ID: use run_all.cmd/run_all.sh for immutable run')
    q=readjson(root/'outputs/HIGHRES_V035_RESULT.json')
    status=q['native']['status']
    rows=[('h1','A065 v0.3.5 | High-resolution historical trefoil falsifier'),
      ('normal',f'Unique run: {run_id}'),('normal',f'Command: {mode}; native status: {status}'),
      ('h2','1. Scientific contract'),
      ('normal','Independent precommitted geometric seed arrays, numerical reduced regularized filament ODE. Original D01/D02/D03 source seals untouched.'),
      ('small','Preregistration SHA256: '+q['prereg_sha256']),
      ('normal','N=600, 1200, 2400, 4800. gamma=1, T=0.04; RK4 8 steps; epsilon=0.06/0.12/0.24. Original dimensionless geometry unscaled.'),
      ('normal','Every mesh is direct analytic arclength sampling; no new independent physical fluid provider.'),
      ('normal','Spatial E(N,2N)=RMS(final(N)-final(2N)[::2]) / RMS(final(N)-initial(N)).'),
      ('normal','Registered baseline acceptance eps=0.12: spatial E < 1% for all pairs and both trefoils. 0.1% is an aspirational reporting target, not a replacement threshold.'),
      ('h2','2. Gates and epistemic limits'),
      ('normal','G15 input/hash PASS on successful pre-run validation. G16 baseline spatial convergence. G17 all 3 epsilon diagnostic scans. G18 time and limited Python/native parity.'),
      ('normal','G2 legacy FAIL, G13 historical coarse-resolution FAIL retained; Fremlin G11 and physical G3 are independent.'),
      ('normal','Euler PDE, PKLSA time dynamics, Casimir, pressure-wall response, gravity and experimental calibration: UNRESOLVED.'),
      ('h2','3. Executed quantitative results')]
    tex=[r'\documentclass[10pt,a4paper]{article}',r'\usepackage[margin=17mm]{geometry}',r'\usepackage{amsmath,amssymb,booktabs,longtable,hyperref}',
         r'\begin{document}',r'\section*{A065 v0.3.5: Direct analytical trefoils to N=4800}',
         r'\textbf{Status: numerical diagnostic only; not full Euler, true dynamical PKLSA, physical Casimir or gravity.}',
         r'\par N=600,1200,2400,4800; $\Gamma=1$, $T=0.04$, RK4 8 steps; $\varepsilon\in\{0.06,0.12,0.24\}$.',
         r'\par Spatial threshold at baseline $\varepsilon=0.12$: 1\%. Informational target: 0.1\%.',
         r'\[ E_{N,2N}=\frac{\operatorname{RMS}(\mathbf X_N(T)-\mathbf X_{2N}(T)|_N)}{\operatorname{RMS}(\mathbf X_N(T)-\mathbf X_N(0))}.\]']
    def etext(x):
        return str(x).replace('\\',r'\textbackslash{}').replace('_',r'\_').replace('%',r'\%').replace('&',r'\&').replace('#',r'\#')
    if status=='EXECUTED':
        for seed,s in q['native']['seeds'].items():
            rows.append(('h2',seed))
            rows.append(('normal',f'Baseline 1%: {s["baseline_spatial_1pct"]}; temporal {s["temporal_status"]}; CPU Python/native N150 {s["parity_status"]}'))
            tex.append(r'\subsection*{'+etext(seed)+'}')
            tex.append(r'\begin{longtable}{@{}llrrll@{}}\toprule $\epsilon$ & mesh & error (percent) & abs RMS & 1\% & 0.1\%\\\midrule')
            for eps,record in s['epsilon_ladders'].items():
                for name,v in sorted(record['pairs'].items(),key=lambda item:int(item[0].split('_vs_')[0])):
                    pct=100*v['relative_error'] if v['relative_error'] is not None else float('nan')
                    rows.append(('small',f'eps={eps}: {name} | relative={pct:.6f}% | abs_RMS={v["rms_difference"]:.8g} | 1%={v["status_1pct"]} | 0.1% target={v["status_0p1pct"]}'))
                    tex.append(f'{eps} & {etext(name)} & {pct:.6f} & {v["rms_difference"]:.6g} & {v["status_1pct"]} & {v["status_0p1pct"]}'+r'\\')
            tex.append(r'\bottomrule\end{longtable}')
            rows.append(('small',f'N150 Python/C++ RMS={s["parity_N150_python_cpp_rms"]:.3g}; serial-vs-parallel={s["parity_N150_serial_parallel_rms"]:.3g}'))
            for n,v in s['temporal_controls'].items():
                a=v['4_vs_8']['relative_error'];b=v['8_vs_16']['relative_error']
                rows.append(('small',f'N={n} RK4 time: 4vs8={a:.3e}; 8vs16={b:.3e}; status={v["status"]}'))
                tex.append(r'\par N='+n+': RK4 relative time errors: '+f'{a:.3e}, {b:.3e}; status '+v['status']+'.')
    else:
        rows.append(('normal',f'Native run not executed: {status}. No fabricated high-resolution numerical certification.'))
        tex.append(r'\par C++17 execution unavailable: '+etext(status))
    rows.extend([('h2','4. Interpretation / remaining limitations'),
        ('normal','Convergence is observed for the specified discretized filament ODE at fixed epsilon, not for unregularized Euler or a finite-core fluid PDE.'),
        ('normal','Changing epsilon and N are separate operations. In particular, B at epsilon=0.06 fails 600 to 1200 at the 1 percent criterion, then improves on finer grids.'),
        ('normal','The two geometries are different historical formulas; their unlike total arclengths are NOT rescaled to an equal physical core size.'),
        ('normal','The same analytic curve sampled at N600 and N4800 does not count as multiple independent physical providers or multiple experimental measurements.'),
        ('normal','Future tests: self-confinement and source-native finite-core dynamical Euler pressure Poisson, vortex clock frequency, boundary response, held-out independent observations.'),
        ('h2','5. Provenance and references'),
        ('small','G2/G11/G13 historical negative evidence remains; all true physical closure claims unresolved.'),
        ('small','Saffman (1992), Vortex Dynamics, Cambridge University Press, doi:10.1017/CBO9780511624063.'),
        ('small','Butcher (2008), Numerical Methods for Ordinary Differential Equations, Wiley, doi:10.1002/9780470753767.')])
    tex += [r'\section*{Reproducibility and provenance}',r'Original SHA256 and complete machine-readable data: \nolinkurl{HIGHRES_V035_RESULT.json}.',
            r'G2, G11 and historical G13 are not repaired by these new geometry-only diagnostics.',
            r'\begin{thebibliography}{9}',r'\bibitem{Saffman1992} P. G. Saffman, \emph{Vortex Dynamics}, Cambridge University Press (1992). doi:10.1017/CBO9780511624063.',
            r'\bibitem{Butcher2008} J. C. Butcher, \emph{Numerical Methods for Ordinary Differential Equations}, 2nd ed., Wiley (2008). doi:10.1002/9780470753767.',r'\end{thebibliography}',r'\end{document}']
    out=root/'reports';out.mkdir(parents=True,exist_ok=True)
    pdf=out/(run_id+'_FALSIFIER_REPORT.pdf');script=out/(run_id+'_FALSIFIER_REPORT.tex')
    if pdf.exists() or script.exists():raise FileExistsError('Highres report collides with existing run')
    count=_pdf_text(pdf,rows)
    with script.open('x',encoding='utf8') as f:f.write('\n'.join(tex)+'\n')
    return {'pdf':str(pdf),'tex':str(script),'pages':count,'native_status':status}
