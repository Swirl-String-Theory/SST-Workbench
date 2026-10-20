"""Human-readable status-pure post-export report, never upgrades a physical claim."""
from __future__ import annotations
from pathlib import Path
from html import escape
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

def write(root,result):
    root=Path(root);out=root/'reports'/'POST_EXPORT_V043_REPORT.pdf'
    out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists():raise FileExistsError(out)
    doc=SimpleDocTemplate(str(out),pagesize=A4,leftMargin=48,rightMargin=48,topMargin=42,bottomMargin=42,
                          title='A065-v0.4.3 Independent Post-export FFT audit')
    st=getSampleStyleSheet()
    story=[Paragraph('A065-v0.4.3 | Independent voxel audit',st['Title']),Spacer(1,12),
      Paragraph('Evidence category: independently recomputed numerical diagnostics from saved rounded FP32/FP64 voxels. '
       'Source-native PKLSA/Casimir/gravity and physical pressure closure remain UNRESOLVED.',st['BodyText']),Spacer(1,12),
      Paragraph('New independent gates G49-G54',st['Heading2'])]
    rows=[['Gate','Verdict','Interpretation']]
    for k,g in result.get('gates',{}).items():rows.append([k,g['status'],escape(g.get('reason','')[:155])])
    tbl=Table([[Paragraph(str(cell),st['BodyText']) for cell in row] for row in rows],colWidths=[44,116,342],repeatRows=1)
    tbl.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e8eff7')),
                            ('LINEBELOW',(0,0),(-1,-1),0.2,colors.HexColor('#cccccc'))]))
    story.append(tbl)
    seed=result.get('seeds',{})
    if seed:
        story.append(Spacer(1,14));story.append(Paragraph('12 exported volumes (CPU FP64 and Arc FP32)',st['Heading2']))
        for sid,val in seed.items():
            story.append(Paragraph(escape(sid),st['Heading3']))
            for row in val['grids']:
                c=row['cpu'];g=row['gpu']
                story.append(Paragraph(f"N={row['n']}: CPU {c['audit_status']}, Arc {g['audit_status']}; "
                         f"refinement CPU max={max(c['time_refinement'].values()):.4g}, "
                         f"GPU max={max(g['time_refinement'].values()):.4g}",st['BodyText']))
    ext=result.get('external_evidence')
    if ext:
        story.append(Spacer(1,10));story.append(Paragraph('External evidence input',st['Heading2']))
        story.append(Paragraph(f"Recognized CPU volumes: {ext['count']['cpu']}; GPU volumes: {ext['count']['gpu']}. "
                       'The audit does not assume completeness when fields are absent.',st['BodyText']))
    story.append(Spacer(1,15));story.append(Paragraph('Scientific boundary',st['Heading2']))
    story.append(Paragraph('All numerical pressure fields are calculated from the same velocity data. '
       'Passing Poisson, energy, curl, or GPU parity gates does not independently validate physical vortex core '
       'profile, microscopic dynamics, a Casimir interaction, or gravity. Failed historical gates are immutable.',st['BodyText']))
    doc.build(story)
    return out
