"""Report source/overlay policy from Framework v1.1.0 RC2, local non-certified renderer."""
from __future__ import annotations
import json,subprocess,shutil,hashlib
from pathlib import Path

def esc(s):
    return str(s).replace('\\',r'\textbackslash{}').replace('_',r'\_').replace('&',r'\&').replace('%',r'\%').replace('#',r'\#')

def render(out:Path,root:Path,stamp:str):
    out=Path(out);root=Path(root)
    shutil.copy2(root/'report'/'FALSIFIER_REPORT.tex',out/'FALSIFIER_REPORT.tex')
    cfg=json.loads((out/'config.json').read_text());results=json.loads((out/'results.json').read_text());gates=json.loads((out/'gates.json').read_text());manifest=json.loads((out/'source_manifest.json').read_text())
    contract=json.loads((root/'configs'/'science_contract.json').read_text())
    reg=[r'\subsection*{Machine-readable equation register}',r'\begin{itemize}']
    for eq in contract['equations']:
        reg.append(r'\item \textbf{'+esc(eq['id'])+r'}: \texttt{'+esc(eq['implementation'])+'}, gate '+esc(eq['gate'])+'.')
    reg.append(r'\end{itemize}\noindent Framework-runtime validation: NOT EXECUTED.')
    (out/'AUTO_SCIENCE_CONTRACT.tex').write_text('\n'.join(reg)+'\n',encoding='utf-8')
    lines=[r'\subsection*{Executed run}',r'\begin{tabular}{ll}\toprule',
      'Mode & '+esc(cfg['mode'])+r'\\','Recorded UTC & '+esc(manifest['utc'])+r'\\',
      'Configuration SHA-256 & '+r'\texttt{'+esc(manifest['configuration_sha256'][:32])+r'} (prefix)\\',
      'Backend & Python/Numba float64 - DEVELOPMENT ONLY'+r'\\',r'\bottomrule\end{tabular}',
      r'\subsection*{Numerical results}',r'\begin{center}\small\begin{tabular}{rrrrrl}\toprule',
      r'$B_0$ & $N$ & $t$ & $\epsilon_H$ & $\Delta z$ & stop \\ \midrule']
    for r in results:
      lines.append(f"{r['b0']:.3f} & {r['n']} & {r['attained_time']:.4g} & {r['last']['energy_rel']:.2e} & {r['net_z_travel']:.3f} & \\texttt{{{esc(r['stop_reason'])}}} \\\\")
    lines += [r'\bottomrule\end{tabular}\end{center}',r'\subsection*{Gate ledger}',r'\begin{tabular}{ll}\toprule Gate & Status \\ \midrule']
    for k,v in gates.items():lines.append(r'\texttt{'+esc(k)+r'} & '+esc(v)+r'\\')
    lines += [r'\bottomrule\end{tabular}',r'\par\smallskip\noindent Reports of apparent persistence at short times or without G5 convergence are NOT long-time stability certification.\par']
    (out/'AUTO_RESULTS.tex').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    pdflatex=shutil.which('pdflatex')
    if pdflatex is None:raise RuntimeError('pdflatex not installed; authoritative TeX source and AUTO_RESULTS retained, PDF unavailable')
    for k in range(2):
        p=subprocess.run([pdflatex,'-halt-on-error','-interaction=nonstopmode','-file-line-error','FALSIFIER_REPORT.tex'],cwd=out,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=80)
        if p.returncode:
            (out/'latex_error.txt').write_text(p.stdout[-10000:],encoding='utf-8')
            raise RuntimeError('PDF compilation failed (see latex_error.txt): '+p.stdout[-700:])
    pdf=out/'FALSIFIER_REPORT.pdf'
    target=out.parent/(root.name+'_FALSIFIER_REPORT.pdf')
    if target.exists():target=out.parent/(root.name+'_'+stamp+'_FALSIFIER_REPORT.pdf')
    shutil.copy2(pdf,target)
    return target
