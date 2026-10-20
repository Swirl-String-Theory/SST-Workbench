"""Create self-contained TeX diagnostic and render PDF when pdflatex is available.

This is A003's diagnostic PDF, not a blind-framework-produced/reveal-authoritative PDF.
"""
from __future__ import annotations
import shutil, subprocess, tempfile
from pathlib import Path


def tex_escape(s:object)->str:
    specials={'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$',
              '#':r'\#','_':r'\_','{':r'\{','}':r'\}', '~':r'\textasciitilde{}',
              '^':r'\textasciicircum{}'}
    return ''.join(specials.get(ch,ch) for ch in str(s))


def render_report(run_dir:Path,ledger:dict,summary:dict)->dict:
    rows=[]
    for x in ledger['records']:
        cells=(x['gate_id'],x['status'],x['execution_status'],x['qualification'])
        rows.append(' & '.join(tex_escape(y) for y in cells)+r' \\')
    tex=r'''\documentclass[9pt,a4paper]{article}
\usepackage[margin=18mm]{geometry}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{longtable,array}
\usepackage{hyperref}
\setlength{\parindent}{0pt}
\begin{document}
\section*{A003 v0.2.6 --- Full Diagnostic Execution}
\textbf{Framework:} SST Falsifier Framework 1.0.10
(\textbf{LOCAL\_VALIDATED\_CANDIDATE}; not canonical).\\
\textbf{Run ID:} \texttt{RUNID}\\
\textbf{Scientific outcome:} \textbf{OVERALLRESULT}\\
\textbf{Protocol:} raw FAIL remains FAIL; subsequent measurements may be DIAGNOSTIC\_ONLY.\\
\textbf{Source atlas:} A003-v0.1.2; 48 seeds / 384 source XYZ.\\
\textbf{Physical scale:} hypothesis only; no Euler/PKLSA run.\\
\textbf{Certification:} no knot/chirality certification and no reveal.

\subsection*{Recorded evaluations}
\small
\begin{longtable}{|p{13mm}|p{32mm}|p{27mm}|p{43mm}|}
\hline Gate & Raw status & Execution & Scientific qualification \\ \hline
\endhead
TABLEROWS
\hline
\end{longtable}
\normalsize
\subsection*{Independent crossing diagnostic}
The raw crossing detector independently computes 2D polygon intersections,
over/under ordering and a Fox/Wirtinger coloring determinant at $t=-1$.
For the archived F3 case, all four frozen primary mesh/projection combinations
produce determinant $3$, including $N=2400$, projection P1.
The historical \texttt{pyknotid} result for that case was determinant $1$.
The internal source of the provider discrepancy remains \textbf{UNRESOLVED}.

The diagram determinant alone does not establish a complete knot class, chirality,
ambient isotopy, or any SST/PKLSA physical effect.
\end{document}
'''
    tex=tex.replace('RUNID',tex_escape(summary['run_id'])).replace('OVERALLRESULT',tex_escape(summary['final_scientific_status'])).replace('TABLEROWS','\n'.join(rows))
    target=run_dir/'DIAGNOSTIC_REPORT.tex'
    with target.open('x',encoding='utf-8',newline='\n') as f:f.write(tex)
    engine=shutil.which('pdflatex')
    if not engine:return {'status':'PDF_UNAVAILABLE_LATEX_NOT_INSTALLED','tex':target.name,'pdf':None}
    try:
        with tempfile.TemporaryDirectory(prefix='a003_v026_tex_') as tmp:
            result=subprocess.run([engine,'-interaction=nonstopmode','-halt-on-error','-output-directory',tmp,str(target)],
                                  capture_output=True,text=True,timeout=120,cwd=run_dir)
            generated=Path(tmp)/'DIAGNOSTIC_REPORT.pdf'
            if result.returncode!=0 or not generated.exists():
                return {'status':'PDF_RENDER_FAILED','tex':target.name,'exit_code':result.returncode,
                        'error_excerpt':(result.stderr or result.stdout)[-1300:]}
            outfile=run_dir/'A003_v0.2.6_DIAGNOSTIC_REPORT.pdf'
            with outfile.open('xb') as f:f.write(generated.read_bytes())
            return {'status':'PDF_RENDERED','tex':target.name,'pdf':outfile.name}
    except Exception as e:
        return {'status':'PDF_RENDER_FAILED','tex':target.name,'error':str(e)}
