"""Author a provenance-sensitive PDF and Markdown diagnostic report; no physical certification."""
from __future__ import annotations
import datetime,json
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,KeepTogether


def produce(out,root):
    out=Path(out);root=Path(root)
    freeze=json.loads((out/'SOURCE_FREEZE.json').read_text())
    reports=sorted((out/'RESULTS').glob('*_SUMMARY.json')) if (out/'RESULTS').exists() else []
    summaries=[]
    for f in reports:
        o=json.loads(f.read_text());summaries.append((f.name,o))
    desc=['A006 Blind Borromean & Swirl Clock Falsifier v0.1.0',
          'DEVELOPMENT / UNQUALIFIED; no physical SST claims',
          'Source archive SHA-256: '+freeze['source_zip_sha256'],
          'Contract SHA-256: '+freeze['contract_sha256'],
          'Source population: 64 triple-component nominal Borromean candidates; 2 masked holdout families.',
          'Model: dimensionless unforced midpoint Rosenhead Biot-Savart filament surrogate.',
          'Source topology: component knot labels supplied but not independently verified; Milnor triple-link invariant unresolved.',
          'Selected comparison: same coordinates as an isolated twist knot, pairs and triple; optional translated unlinked controls.',
          'Qualification: B1-B9 remain unresolved/not run. B2 fails on undersampled runs.',
          'Stability: a small-growth ratio is only a finite-horizon diagnostic, not a proof of asymptotic stability.',
          'Clock: no demonstrated reproducible intrinsic frequency or local proper-time relationship.',
          'Guan, Zuccher & Liu (2025), Physics of Fluids 37, 024126, doi:10.1063/5.0252708 (independent compressible GPE benchmark).']
    for file,s in summaries:
        desc.append(f'Batch {file} ({s["mode"]}), cases={len(s["cases"])}, all unresolved for B9.')
        for c in s['cases'][:3]:
            amp=c.get('three_ring_final_shape_error',[])
            desc.append('  '+c['id']+': triple endpoint shape errors '+str([round(float(x),6) for x in amp]) +
                '; B2 '+str(c.get('B2','UNRESOLVED')))
    md=out/'FALSIFIER_REPORT.md'
    md.write_text('# '+desc[0]+'\n\n'+'\n\n'.join(desc[1:])+'\n',encoding='utf8')
    styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='SmallBlue',fontName='Helvetica',fontSize=9,leading=13,textColor=colors.HexColor('#244965'),spaceAfter=8))
    styles.add(ParagraphStyle(name='BodyB',fontName='Helvetica',fontSize=9.2,leading=14,spaceAfter=9))
    story=[Paragraph(desc[0],styles['Title']),Spacer(1,.5*cm),Paragraph(desc[1],styles['SmallBlue']),Spacer(1,.2*cm)]
    section=''
    for i,line in enumerate(desc[2:]):
        safe=line.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
        story.append(Paragraph(safe,styles['BodyB']))
    pdf=out/'FALSIFIER_REPORT.pdf'
    doc=SimpleDocTemplate(str(pdf),pagesize=(21*cm,29.7*cm),rightMargin=2*cm,leftMargin=2*cm,topMargin=2*cm,bottomMargin=1.8*cm,
        title=desc[0],author='SST Workbench; blind candidate diagnostic')
    doc.build(story)
    return pdf,md

if __name__=='__main__':
    import sys
    pdf,md=produce(sys.argv[1],sys.argv[2]);print('Reports:',pdf,md)
