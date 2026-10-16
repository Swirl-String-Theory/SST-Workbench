#!/usr/bin/env python3
"""Non-invasive external falsifier report renderer, version 0.1.0.

Only PUBLIC root-level result files from an explicit --outputs directory are read.
No private/reveal traversal. No mutation of a frozen instance or its result tree.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

VERSION='0.1.0'
FILES=('GATE_LEDGER.json','RUN_SUMMARY.json','BACKEND_MANIFEST.json',
       'SOURCE_MANIFEST.json','DEPENDENCY_CAVEATS.json','REPORT_RENDER.json',
       'OUTPUT_MANIFEST.json')
STATUS_CLASSES={'PASS','FAIL','UNRESOLVED','INDETERMINATE','NOT_APPLICABLE',
                'DEFERRED','SKIP','SKIPPED','BLOCKED','ERROR','NOT_RUN'}


def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as inp:
        for chunk in iter(lambda:inp.read(1<<20),b''):
            h.update(chunk)
    return h.hexdigest()


def read_json(file:Path):
    if not file.is_file():return None
    if file.stat().st_size > 30*1024*1024:
        raise ValueError(f'Refusing oversized public JSON: {file}')
    return json.loads(file.read_text(encoding='utf-8-sig'))


def safe_text(value, limit=700):
    s=' '.join(str(value if value is not None else '').split())
    return s[:limit]+(' ...' if len(s)>limit else '')


def canonical_status(status):
    return str(status or 'NOT_RUN').strip().upper().replace(' ','_')


def extract_gates(ledger):
    if not isinstance(ledger,dict):return []
    definitions={str(x.get('gate_id',x.get('id'))):x for x in ledger.get('definitions',[]) if isinstance(x,dict)}
    records=ledger.get('records',ledger.get('gates',[]))
    if isinstance(records,dict):records=[dict(v,gate_id=k) for k,v in records.items() if isinstance(v,dict)]
    result=[]
    for rec in records if isinstance(records,list) else []:
        if not isinstance(rec,dict):continue
        gid=str(rec.get('gate_id',rec.get('id','?')))
        definition=definitions.get(gid,{})
        result.append({'id':gid,'status':canonical_status(rec.get('status')),
          'question':safe_text(rec.get('question') or definition.get('question') or ''),
          'reason':safe_text(rec.get('reason','')), 'metrics':rec.get('metrics',{}),
          'actual_backend':safe_text(rec.get('actual_backend','')),
          'authority':safe_text(rec.get('authority','')),
          'requires':definition.get('requires',[])})
    return result


def clean_metric_pairs(metrics,max_items=5):
    if not isinstance(metrics,dict):return []
    entries=[]
    for k,v in metrics.items():
        if len(entries)>=max_items:break
        if isinstance(v,dict):continue
        if isinstance(v,list):
            desc=f'array, {len(v)} elements' # Do not expose identity-bearing values.
        else:
            desc=safe_text(v,80)
        entries.append((safe_text(k,70),desc))
    return entries


def build_audit(outputs:Path, files:dict, ledger:dict, summary:dict):
    bound=None
    if isinstance(ledger,dict) and isinstance(summary,dict):
        l=ledger.get('ledger_sha256'); s=summary.get('gate_ledger_sha256')
        bound=(s==l) if l and s else None
    return {'schema':'SST-EXTERNAL-REPORT-AUDIT-1','generator_version':VERSION,
      'generated_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
      'source_root':str(outputs.resolve()),
      'read_files':{n:{'sha256':sha(p),'bytes':p.stat().st_size} for n,p in files.items()},
      'declared_gate_ledger_summary_binding_matches':bound,
      'verification_scope':'Read-only digest inventory and declared ledger/summary binding check only. Does not independently certify framework protocol, scientific results, or frozen output tree.',
      'sealed_source_mutated':False}


def tex_escape(txt):
    text=str(txt)
    repl={'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$',
          '#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}
    return ''.join(repl.get(c,c) if ord(c)<128 else '?' for c in text)


def make_tex(meta,gates,audit,backend,caveats):
    def e(s):return tex_escape(safe_text(s,1600))
    count=Counter(g['status'] for g in gates)
    b=[r'\documentclass[10pt,a4paper]{article}',
       r'\usepackage[T1]{fontenc}', r'\usepackage[utf8]{inputenc}',
       r'\usepackage[margin=17mm]{geometry}',
       r'\usepackage{booktabs,longtable,array,xcolor,hyperref}',
       r'\usepackage{parskip}',
       r'\definecolor{navy}{HTML}{183349}',
       r'\hypersetup{colorlinks=true,urlcolor=navy}',
       r'\setlength{\emergencystretch}{3em}',
       r'\begin{document}',
       r'\color{navy}\Huge\bfseries SST Falsifier Report\par\normalsize\mdseries\color{black}',
       r'\textbf{' + e(meta['label']) + r'}\\',
       e(meta['title']) + r'\\',
       r'External read-only rendering; not an original frozen report.\\',
       'Generated: ' + e(audit['generated_utc']) + r'\\',
       r'\section*{Evidence boundary}',
       'No new science was executed for this report. Gate outcomes are copied from the source ledger without reclassification. Missing records are not silently filled.',
       r'\section*{Gate summary}',
       e(', '.join(f'{k}={v}' for k,v in sorted(count.items()))),
       r'\begin{longtable}{p{13mm}p{24mm}p{119mm}}',
       r'\toprule Gate & Status & Preregistered question \\',
       r'\midrule\endhead']
    for g in gates:
        b.append(r'\textbf{'+e(g['id'])+'} & '+e(g['status'])+' & '+e(g['question'])+r'\\\hline')
    b.extend([r'\bottomrule\end{longtable}',r'\section*{Gate detail (source-derived)}'])
    for g in gates:
        b.extend([r'\subsection*{'+e(g['id'])+' --- '+e(g['status'])+'}',
                  e(g['question']),r'\par\textit{'+e(g['reason'])+r'}\par'])
        pairs=clean_metric_pairs(g['metrics'])
        if pairs:
            b.append(r'\begin{itemize}')
            for k,v in pairs:b.append(r'\item '+e(k)+': '+e(v))
            b.append(r'\end{itemize}')
    b.extend([r'\section*{Backend provenance}',
         e(json.dumps(backend if isinstance(backend,dict) else {},ensure_ascii=True,sort_keys=True)[:1800]),
         r'\section*{Report provenance}',
         'Declared ledger-to-summary digest binding: '+e(audit['declared_gate_ledger_summary_binding_matches'])+r'\\',
         'Files read: '+e(', '.join(sorted(audit['read_files'])))+r'\\',
         r'\textbf{Scope}: '+e(audit['verification_scope']),
         r'\end{document}'])
    return '\n'.join(b)+'\n'


def make_pdf_reportlab(out:Path,meta,gates,audit,backend,caveats):
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,KeepTogether,PageBreak
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    font='Helvetica'
    path=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
    if path.is_file():
        pdfmetrics.registerFont(TTFont('DejaVuSST',str(path)));font='DejaVuSST'
    navy=colors.HexColor('#183349'); teal=colors.HexColor('#14788A')
    grey=colors.HexColor('#607080')
    ss=getSampleStyleSheet()
    ss.add(ParagraphStyle(name='SSTTitle',fontName=font,fontSize=18,leading=24,textColor=navy,spaceAfter=10))
    ss.add(ParagraphStyle(name='SSTSub',fontName=font,fontSize=11,leading=16,textColor=navy,spaceBefore=12,spaceAfter=6))
    ss.add(ParagraphStyle(name='SSTBody',fontName=font,fontSize=8.2,leading=12,spaceAfter=5))
    ss.add(ParagraphStyle(name='SSTSmall',fontName=font,fontSize=7,leading=10,spaceAfter=4))
    ss.add(ParagraphStyle(name='SSTTh',fontName=font,fontSize=7.2,leading=10,textColor=colors.white))
    doc=SimpleDocTemplate(str(out),pagesize=A4,leftMargin=40,rightMargin=40,topMargin=44,bottomMargin=40,title=f"{meta['label']} - External Falsifier Report",author='SST External Report Generator')
    story=[]
    def P(t,style='SSTBody'):
        return Paragraph(xml_escape(str(t)).replace('\n','<br/>'),ss[style])
    def head(t):story.append(P(t,'SSTSub'))
    story.append(P('SST Falsifier Report','SSTTitle'))
    story.append(P(meta['label']+' | '+meta['title'],'SSTBody'))
    story.append(P('EXTERNAL READ-ONLY RENDERING  -  This is not a new scientific run or a replacement for the frozen report.','SSTSmall'))
    story.append(P('Generated UTC: '+audit['generated_utc'],'SSTSmall'))
    head('Scientific evidence boundary')
    story.append(P('Statuses are transcribed from the source gate ledger. No gate is promoted. Absent or unreadable source documents are identified in the provenance section. This renderer does not reopen, alter, or validate the sealed experimental run.'))
    head('Gate summary')
    statuses=Counter(g['status'] for g in gates)
    story.append(P('  |  '.join(f'{s}: {n}' for s,n in sorted(statuses.items())) if gates else 'No readable gate records supplied.'))
    if gates:
        rows=[[P('Gate','SSTTh'),P('Status','SSTTh'),P('Preregistered question','SSTTh')]]
        for g in gates:rows.append([P(g['id'],'SSTSmall'),P(g['status'],'SSTSmall'),P(g['question'] or '[Not in ledger]','SSTSmall')])
        tab=Table(rows,colWidths=[48,97,365],repeatRows=1,hAlign='LEFT')
        tab.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),navy),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,1),(-1,-1),0.25,colors.HexColor('#D2DCE2')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F4F7F9')])]))
        story.append(tab)
    head('Individual gate evidence')
    for g in gates:
        block=[P(g['id']+' - '+g['status'],'SSTSub'),P(g['question'],'SSTBody')]
        if g['reason']:block.append(P('Interpretation / reason: '+g['reason'],'SSTSmall'))
        pairs=clean_metric_pairs(g['metrics'])
        if pairs:block.append(P('Recorded metrics: '+'; '.join(f'{k}={v}' for k,v in pairs),'SSTSmall'))
        if g['actual_backend'] or g['authority']:
            block.append(P(f"Backend: {g['actual_backend']} | authority: {g['authority']}",'SSTSmall'))
        story.append(KeepTogether(block[:2]));story.extend(block[2:])
    head('Backend and dependency notes')
    for k,v in (backend.items() if isinstance(backend,dict) else []):
        story.append(P(f'{k}: {safe_text(json.dumps(v,ensure_ascii=True,sort_keys=True),400)}','SSTSmall'))
    rows=caveats.get('rows',[]) if isinstance(caveats,dict) else []
    limited=[r for r in rows if r.get('interpretation_limited')]
    if limited:story.append(P(f'Dependency caveats: {len(limited)} gates have limited downstream interpretation. This is not changed by report rendering.','SSTBody'))
    head('Source integrity and provenance')
    story.append(P('Declared run-summary-to-ledger digest binding matches: '+str(audit['declared_gate_ledger_summary_binding_matches']),'SSTSmall'))
    for name,f in sorted(audit['read_files'].items()):story.append(P(f"{name} | sha256={f['sha256']} | {f['bytes']} bytes",'SSTSmall'))
    story.append(P(audit['verification_scope'],'SSTSmall'))
    story.append(P('Generator version: '+VERSION,'SSTSmall'))
    def footer(canvas,document):
        canvas.setStrokeColor(colors.HexColor('#D9E1E6'));canvas.line(40,32,A4[0]-40,32)
        canvas.setFont('Helvetica',7);canvas.setFillColor(grey)
        canvas.drawString(40,22,'SST Workbench | external read-only report')
        canvas.drawRightString(A4[0]-40,22,f'Page {document.page}')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)


def generate(outputs:Path,dest:Path,catalog:str,version:str,title:str,pdf_engine:str):
    outputs=outputs.expanduser().resolve()
    dest=dest.expanduser().resolve()
    if not outputs.is_dir():raise ValueError(f'Output directory does not exist: {outputs}')
    if dest==outputs or outputs in dest.parents:raise ValueError('Destination must be OUTSIDE the source outputs tree (immutability).')
    if dest==outputs.parent and (dest/'preregistration').is_dir():raise ValueError('Destination appears to be a frozen instance; choose a separate reports directory.')
    source_paths={f:outputs/f for f in FILES if (outputs/f).is_file()}
    if not source_paths:raise ValueError('No recognized public root-level results in --outputs')
    data={k:read_json(p) for k,p in source_paths.items()}
    ledger=data.get('GATE_LEDGER.json') or {}
    summary=data.get('RUN_SUMMARY.json') or {}
    backend=data.get('BACKEND_MANIFEST.json') or {}
    caveats=data.get('DEPENDENCY_CAVEATS.json') or {}
    gates=extract_gates(ledger)
    audit=build_audit(outputs,source_paths,ledger,summary)
    audit['missing_optional_files']=sorted(set(FILES)-set(source_paths))
    if not gates:audit['warnings']=['No GATE_LEDGER records: informational report only, no fabricated verdicts.']
    dest.mkdir(parents=True,exist_ok=True)
    label=f'{catalog}-{version}';meta={'label':label,'title':title}
    pdf=dest/f'{label}_FALSIFIER_REPORT.pdf';tex=dest/f'{label}_FALSIFIER_REPORT.tex';json_audit=dest/f'{label}_EXTERNAL_REPORT_AUDIT.json'
    tex.write_text(make_tex(meta,gates,audit,backend,caveats),encoding='utf-8')
    if pdf_engine in ('auto','pdflatex') and shutil.which('pdflatex'):
        with tempfile.TemporaryDirectory() as t:
            tmp=Path(t)/tex.name;tmp.write_bytes(tex.read_bytes())
            p=subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error',f'-output-directory={t}',str(tmp)],cwd=t,capture_output=True,text=True,timeout=60)
            if p.returncode==0 and (Path(t)/pdf.name).is_file():
                shutil.copy2(Path(t)/pdf.name,pdf);audit['pdf_engine']='pdflatex'
            elif pdf_engine=='pdflatex':
                raise RuntimeError('LaTeX compilation failed: '+p.stdout[-1700:])
    if not pdf.is_file():
        make_pdf_reportlab(pdf,meta,gates,audit,backend,caveats)
        audit['pdf_engine']='reportlab'
    json_audit.write_text(json.dumps(audit,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return pdf,tex,json_audit,gates


def main():
    p=argparse.ArgumentParser(description='Non-mutating post-hoc PDF report generator for historical SST falsifiers')
    p.add_argument('--outputs',required=True,type=Path,help='Frozen PUBLIC output directory, with GATE_LEDGER.json')
    p.add_argument('--dest',required=True,type=Path,help='Independent target directory, OUTSIDE frozen outputs')
    p.add_argument('--catalog',required=True)
    p.add_argument('--version',required=True)
    p.add_argument('--title',default='Scientific falsification campaign')
    p.add_argument('--engine',choices=['auto','pdflatex','reportlab'],default='auto')
    a=p.parse_args()
    pdf,tex,au,gates=generate(a.outputs,a.dest,a.catalog,a.version,a.title,a.engine)
    print(json.dumps({'pdf':str(pdf),'tex':str(tex),'audit':str(au),'gate_count':len(gates)},indent=2))

if __name__=='__main__':main()
