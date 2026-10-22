"""New four-level report - written as TeX, with optional pdflatex PDF."""
from __future__ import annotations
from pathlib import Path
import shutil, subprocess, tempfile
from diagnostic_pdf import tex_escape


def render_qualification_report(out:Path,ledger:dict,summary:dict):
    headings=['A003 v0.2.8.1 - Corrected G5 Qualification',
        'Framework 1.0.10: '+summary['framework']['source_status'],
        'Run ID: '+summary['run_id'],
        'Bounded screen: '+summary['corrected_g5_bounded_result']]
    rows=[' & '.join(tex_escape(x[k]) for k in ('gate_id','status','execution_status','qualification'))+r' \\' for x in ledger['records']]
    body=r'''\documentclass[a4paper,9pt]{article}
\usepackage[margin=17mm]{geometry}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{longtable,array}
\begin{document}
\section*{TITLE}
\textbf{Framework:} FRAMEWORK\\
\textbf{Run ID:} \texttt{RUNID}\\
\textbf{Result:} RESULT\\
\textbf{Scope:} F3=T(2,3), F4=T(3,5); N=1200,2400,4800,9600;
P0/P1; original and mirror = 32 provider observations.\\
\textbf{Controls:} old v0.2.7 corrected live baseline on N=1200,2400;
unaltered A003-v0.1.2 SHA-256 manifest.\\
\textbf{Restriction:} NOT complete topological or chirality certification;
no G6/Euler/PKLSA and no blind/reveal framework certification.
\subsection*{Gates}
\small
\begin{longtable}{|p{16mm}|p{32mm}|p{31mm}|p{43mm}|}
\hline Gate & Status & Execution & Qualification \\ \hline
\endhead
ROWS
\hline
\end{longtable}
\normalsize
\subsection*{Scientific boundary}
Software correctness of a corrected crossing detector does not uniquely
identify a knot or guarantee a physical finite-core self-confining vortex.
All unexecuted gates are UNRESOLVED/NOT EXECUTED. A scientific FAIL is retained
and does not stop the remaining enabled independent diagnostics. The previous
stock-provider G5 failure remains immutable historical evidence.
\end{document}'''
    body=body.replace('TITLE',tex_escape(headings[0])).replace('FRAMEWORK',tex_escape(headings[1]))\
        .replace('RUNID',tex_escape(summary['run_id'])).replace('RESULT',tex_escape(summary['corrected_g5_bounded_result']))\
        .replace('ROWS','\n'.join(rows))
    tex=out/'G5_QUALIFICATION_REPORT.tex';tex.write_text(body,encoding='utf-8')
    exe=shutil.which('pdflatex')
    if not exe:return {'status':'PDF_NOT_RENDERED_LATEX_UNAVAILABLE','tex':tex.name,'pdf':None}
    try:
        with tempfile.TemporaryDirectory(prefix='a003_v028_pdf_') as td:
            x=subprocess.run([exe,'-interaction=nonstopmode','-halt-on-error','-output-directory',td,str(tex)],
                             cwd=out,text=True,capture_output=True,timeout=120)
            pdf=Path(td)/(tex.stem+'.pdf')
            if x.returncode or not pdf.is_file():
                return {'status':'PDF_FAILED','tex':tex.name,'stderr':(x.stderr+x.stdout)[-1000:]}
            target=out/'A003_v0.2.8.1_G5_QUALIFICATION_REPORT.pdf'
            with target.open('xb') as f:f.write(pdf.read_bytes())
            return {'status':'PDF_RENDERED','pdf':target.name,'tex':tex.name}
    except Exception as exc:
        return {'status':'PDF_FAILED','tex':tex.name,'exception':str(exc)}
