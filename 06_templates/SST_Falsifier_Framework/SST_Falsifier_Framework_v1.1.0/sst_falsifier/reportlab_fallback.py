"""Diagnostic-only report when the full LaTeX publisher is unavailable.

This does NOT qualify a scientific PDF. The original TeX and all contracts remain
preserved in the ZIP; omissions are explicit instead of silently dropping a report.
"""
from __future__ import annotations
import json, textwrap
from pathlib import Path

def diagnostic_pdf(root,out,destination,*,reason):
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,LongTable,TableStyle,KeepTogether
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from xml.sax.saxutils import escape
    root=Path(root);out=Path(out);destination=Path(destination)
    destination.parent.mkdir(parents=True,exist_ok=True)
    def j(p):
        try:return json.loads(Path(p).read_text(encoding='utf8'))
        except Exception:return {}
    science=j(root/'science_contract.json'); gates=j(out/'GATE_LEDGER.json'); matrix=j(out/'AUTO_BACKEND_MATRIX.json')
    manifest=j(out/'SCIENCE_EVIDENCE_MANIFEST.json'); source=j(out/'SOURCE_MANIFEST.json')
    summary=j(out/'RUN_SUMMARY.json'); cfg=(root/'falsifier.toml').read_text(encoding='utf8') if (root/'falsifier.toml').exists() else ''
    styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='ScientificBody',parent=styles['BodyText'],fontSize=9.2,leading=14,spaceAfter=7))
    styles.add(ParagraphStyle(name='SmallMono',parent=styles['BodyText'],fontSize=7.5,leading=10,wordWrap='CJK'))
    def p(s,sty='ScientificBody'):return Paragraph(escape(str(s)).replace('\n','<br/>'),styles[sty])
    doc=SimpleDocTemplate(str(destination),pagesize=A4,leftMargin=45,rightMargin=45,topMargin=49,bottomMargin=44,title=f'{root.name} -- diagnostics')
    story=[p('SST Falsifier — Diagnostic Report','Title'),p(root.name,'Heading2'),
       p('NOT SCIENTIFICALLY QUALIFIED: full LaTeX rendering failed. This standalone diagnostic PDF does not replace the frozen scientific TeX source.'),
       p('Render failure: '+reason[:1250]),Spacer(1,13)]
    def sect(h,entries):
        story.append(p(h,'Heading2'))
        for entry in entries:story.append(p(entry))
    sect('Research question and preregistration',[science.get('research_question','MISSING — not preregistered'),
             'Objective: '+science.get('objective','MISSING'),
             'H0: '+science.get('null_hypothesis','MISSING'),
             'H1: '+science.get('alternative_hypothesis','MISSING')])
    sect('Mathematical formulation and dimensional checks',[
         f"{x.get('id','?')} — {x.get('purpose','')}: {x.get('latex','')} | Dimensions: {x.get('dimensional_check','NOT REPORTED')}" for x in science.get('equations',[])] or ['NO EQUATIONS DECLARED'])
    sect('Numerical procedure and reproducibility',[
        f"{x.get('id','?')} / {x.get('gate','?')}: {x.get('operation','')}" for x in science.get('steps',[])] or ['NO STEPS DECLARED'])
    sect('Backend 2/3 qualification',[f"Execution contract: {matrix.get('status','NOT_EXECUTED')}",
         f"Counted categories: {matrix.get('counted_backend_categories',0)} of required 2",
         f"GPU provider: {matrix.get('policy',{}).get('selected_gpu_provider','unknown')}",
         'Backend presence and FFT probes are not physical solver evidence.',
         *[f"{k}: {v.get('status','?')} — {v.get('reason','')}" for k,v in matrix.get('scientific',{}).items()]])
    sect('Gate ledger and qualification',[
        f"{x.get('gate_id','?')} status={x.get('status','?')} qualification={x.get('qualification','UNASSESSED')} reason={x.get('reason','')}" for x in gates.get('records',[])] or ['NO VALIDATED GATE LEDGER'])
    sect('Source / atlas constraints',[f"Source manifest: {source.get('schema','unavailable')}",
         'E010 geometry is intake-only, not evidence for a stable Euler knot or independent dynamical replication.',
         'Selected source data must be frozen and validated separately before physical interpretation.'])
    sect('Outputs, checksums and unresolved work',[f"Run mode: {summary.get('mode','unknown')}",
         f"Scientific evidence SHA-256: {manifest.get('manifest_sha256','missing')}",
         'A diagnostic report is not a certification. Install TeX and rerun REPORT_ONLY without changing science data.',
         'Check convergence, independent source groups, finite-core assumptions, and complete scientific references.'])
    sect('Report provenance',[f'Source file: {root / "report" / "FALSIFIER_REPORT.tex"}',
         'The detailed frozen source remains available within the project and output archive.'])
    doc.build(story)
    if not destination.is_file() or destination.stat().st_size<2000:raise RuntimeError('PDF diagnostic generation failed')
    return destination
