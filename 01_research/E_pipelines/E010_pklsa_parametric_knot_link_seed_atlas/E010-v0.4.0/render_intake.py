"""Technical intake report; not a scientific falsifier report."""
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak


def render(path, summary, publication):
    path=Path(path)
    if path.exists():raise FileExistsError(path)
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='SmallBody',fontName='Helvetica',fontSize=9,leading=13,spaceAfter=8))
    styles.add(ParagraphStyle(name='HashText',fontName='Courier',fontSize=8,leading=11,spaceAfter=8,wordWrap='CJK'))
    styles['Title'].textColor=colors.HexColor('#17374e');styles['Title'].fontSize=25
    body=[]
    def p(text,style='SmallBody'):body.append(Paragraph(text,styles[style]))
    def h(text):p(text,'Heading2')
    def table(rows,widths):
        t=Table([[Paragraph(escape(str(x)),styles['SmallBody']) for x in row] for row in rows],colWidths=widths,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e6eef3')),('VALIGN',(0,0),(-1,-1),'TOP'),
           ('LINEBELOW',(0,0),(-1,0),0.7,colors.HexColor('#8daab9')),('BOTTOMPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5)]))
        body.append(t);body.append(Spacer(1,12))
    p('PKLSA / E010 v0.4.0','Title')
    p('Combined seed atlas - technical intake and portability report','Heading2')
    p('Publication run: '+escape(publication['run_id'])+'<br/>Recorded UTC: '+escape(publication['created_utc'])+
      '<br/>Reporting timezone: Europe/Amsterdam')
    h('Outcome')
    p('The combined atlas preserves the historical v0.3.1 carrier collection and adds the full v0.3.6 nominal/perturbed Ruban release. '
      'Source admission, data integrity and portable ingestion passed. No new scientific qualification is asserted.')
    table([['Collection','Logical records','Meaning'],['Historical v0.3.1','4,497','2,227 historical topology labels'],
           ['Ruban nominal','3,630','24 knot and 6 three-component link families'],
           ['Ruban perturbed','3,630','Parent-linked variants from the same analytic source'],
           ['Combined','11,757','Records, not distinct topologies or providers']],[145,90,240])
    h('Separate gate axes')
    table([['Gate','Result'],['Source / integrity',summary['gates']['integrity']],
           ['Execution',summary['gates']['execution']],['Geometry',summary['gates']['geometry']],
           ['Science',summary['gates']['scientific']]],[115,360])
    p('Historical topology verdicts remain '+str(summary['historical_pass_topologies'])+' PASS and '+str(summary['historical_fail_topologies'])+
      ' FAIL. These are preserved historical verdicts, not evidence of a newly run campaign. All 54,450 proposed Ruban dynamics scenarios remain PENDING / NOT_RUN.')
    body.append(PageBreak())
    h('Integrity and provenance')
    p('All 10,169 original Ruban manifest entries were verified; 10,164 are XYZ component files. Every component was parsed as 1,024 finite XYZ points. '
      'The local original manifest matches the separately retrieved Drive manifest byte-for-byte. All 4,497 original carrier raw hashes and parsed geometry hashes were verified. '
      f"The payload preserves {summary['history_files']:,} historical output files and {summary['raw_source_paths']:,} original source paths.")
    p('Source folder: <link href="https://drive.google.com/drive/folders/1eULt2H9CZjX8-WDwS5xX0sbwQRu4YAH0">Google Drive / supplied E010-v0.3.6 geometry release</link>. '
      'Manifest file ID: 17PUIzvrb5TUx15cBGJ01yv0OvUZiNHJZ. Original file IDs, timestamps, size and retrieval evidence are retained in provenance/DRIVE_PROVENANCE.json. '
      'Admission is user-authorized; independent publisher authentication and a provider revision ID are not asserted.')
    for title,value in [('Original Drive/local manifest SHA-256',summary['drive_manifest_sha256']),
                        ('Frozen intake contract SHA-256',summary['source_contract_sha256']),
                        ('Combined index SHA-256',publication['index_sha256']),
                        ('Portable ZIP SHA-256',publication['zip_sha256'])]:
        p(title,'Heading3');p(value,'HashText')
    h('Duplicates and topology identity')
    p(f"{summary['distinct_ordered_geometries']:,} distinct ordered float64 geometry hashes; {summary['exact_geometry_duplicate_groups']:,} groups share an exact geometry hash. "
      f"{summary['shared_raw_groups']:,} raw-hash groups are shared by multiple logical records/components. All logical records remain present. "
      'Duplicate detection does not assert equivalence under rigid motion, reparametrization or isotopy.')
    p('1,452 nominal records have no supplied canonical topology ID, with the same condition retained for their perturbed children. '
      'Supplied knot/link labels are preserved as source labels. Three-component links remain three ordered, separate closed components.')
    body.append(PageBreak())
    h('Portability, validation and repeat safety')
    p(f"The build ran {publication['test_count']} targeted regression tests before ingestion. They cover damaged bytes, missing components, duplicate IDs, path traversal, "
      'component order, invalid point arrays, parsed-hash mismatch, parent relations, scientific/admission promotion and create-only repeat behavior.')
    p(f"The ZIP was reopened for CRC validation, extracted into an independent run directory and checked in an isolated Python process. "
      f"Every payload manifest hash was checked and {publication['portable_loaded_geometries']} representative geometries were loaded, covering all historical formats and research variants/component counts. "
      'The reader resolves geometry only inside the extracted payload. It does not use historical absolute input locations.')
    p('A repeated run verifies the existing immutable payload and publications. Each invocation writes a unique execution log. '
      'A conflicting target or hash error fails closed. Original manifests and source releases are not repaired in place.')
    h('Runtime and commands')
    p(escape(summary['environment']['python'])+'<br/>NumPy '+escape(summary['environment']['numpy'])+'<br/>'+escape(summary['environment']['platform']))
    for command in ['run_all.cmd', 'run_all.cmd SELFTEST', 'run_all.cmd VERIFY', 'py -3.14 -B verify_atlas.py']:
        p(command,'HashText')
    p('The first three commands are run from E010-v0.4.0. The final command runs from an extracted output ZIP. '
      'Reader calls to research geometry require allow_research=True. Default enumeration excludes research records; it does not assert that all historical carriers are scientifically admitted.')
    h('Unresolved scientific evidence')
    p('No equilibrium, stability, lifetime, continuum reach or finite-core validation has been added. R0=1 coordinates are dimensionless; B0 is a geometric radius ratio, not a calibrated physical core size. '
      'The 7,260 analytic variants remain one source group and add zero independent empirical providers. No falsifier dataset contract or blind/reveal commitment changes.')
    p('The corrected v0.4.0 research binding points to v0.3.6. Existing family defaults, active v0.3.4 selection, A011/A054/A065 and Scheduled settings are unchanged. '
      'Further use in a falsifier requires its own explicit dataset-admission contract and execution budget.')
    def footer(canvas,doc):
        canvas.setStrokeColor(colors.HexColor('#8daab9'));canvas.line(44,39,A4[0]-44,39)
        canvas.setFont('Helvetica',8);canvas.drawString(44,26,'E010 v0.4.0 | Technical intake only | No scientific promotion')
        canvas.drawRightString(A4[0]-44,26,str(doc.page))
    with path.open('xb') as stream:
        SimpleDocTemplate(stream,pagesize=A4,leftMargin=44,rightMargin=44,topMargin=40,bottomMargin=52,
                          title='PKLSA E010 v0.4.0 - Technical Intake',author='SST-Workbench').build(body,onFirstPage=footer,onLaterPages=footer)
