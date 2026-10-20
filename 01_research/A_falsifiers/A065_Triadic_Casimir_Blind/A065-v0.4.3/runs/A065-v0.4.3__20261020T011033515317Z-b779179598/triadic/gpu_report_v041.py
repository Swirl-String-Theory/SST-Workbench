"""Mandatory portable GPU report. Status-pure; no fabricated Arc measurements."""
from __future__ import annotations
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4

def write(root, data):
    root=Path(root);dest=root/'reports'/'ARC_GPU_V041_REPORT.pdf'
    dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists():raise FileExistsError(dest)
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='SSTSub',parent=styles['Heading2'],spaceBefore=14,spaceAfter=7))
    styles.add(ParagraphStyle(name='SSTBody',parent=styles['BodyText'],fontSize=9,leading=13,spaceAfter=8))
    doc=SimpleDocTemplate(str(dest),pagesize=A4,leftMargin=46,rightMargin=46,topMargin=44,bottomMargin=44,
                          title='A065-v0.4.1 Arc A770 numerical Euler GPU audit')
    story=[Paragraph('A065-v0.4.1 | Arc A770 3D Euler numerical audit',styles['Title']),
       Spacer(1,12),Paragraph('Release category: NUMERICAL SCREENING ONLY',styles['Heading3']),
       Paragraph('This report records device-executed FFT/RK4 tests only when an actual Intel Arc A770 '
       'Level Zero device is identified. Missing hardware produces NOT_RUN_PREREQUISITE, never PASS. '
       'Synthetic Gaussian-initialized Euler data do not establish physical PKLSA, Casimir, gravity, '
       'or independently observed pressure.',styles['SSTBody']),
       Paragraph('Pre-registered inputs',styles['SSTSub'])]
    specs=[('A003 source geometries','torus_3_1_direct / torus_3_1_hoste'),('Grid ladder','48^3 / 64^3 / 96^3'),
           ('Numerical cube','L = 12 periodic'),('Initial vortex core','Gaussian a = 0.55 (assumed)'),
           ('Circulation / density','Gamma = 1; rho = 1'),('Euler integrator','Fourier projected rotational RK4; 4 steps, T = 0.02'),
           ('GPU','SYCL Level Zero / dpnp FFT FP32'),('Reference','NumPy FFT FP64, same initial data'),
           ('Precision warning','Previous DD32 Biot-Savart parity is NOT FFT/Euler parity')]
    specs_t=Table([[Paragraph(a,styles['SSTBody']),Paragraph(b,styles['SSTBody'])] for a,b in specs],colWidths=[150,335],hAlign='LEFT')
    specs_t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),.25,colors.HexColor('#dddddd'))]))
    story+=[specs_t,Spacer(1,12),Paragraph('New gates G43-G48',styles['SSTSub'])]
    gtable=[[Paragraph('Gate',styles['SSTBody']),Paragraph('Result',styles['SSTBody']),Paragraph('Interpretation',styles['SSTBody'])]]
    for gid,record in data.get('gates',{}).items():
        gtable.append([Paragraph(gid,styles['SSTBody']),Paragraph(record['status'],styles['SSTBody']),
                       Paragraph(record.get('reason','')[:230].replace('&','&amp;'),styles['SSTBody'])])
    t=Table(gtable,colWidths=[41,136,308],repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e9edf2')),
        ('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),.25,colors.HexColor('#dddddd'))]))
    story+=[t,Spacer(1,12)]
    dev=data.get('device')
    if dev:
        story.append(Paragraph('Detected GPU: '+str(dev.get('device_name','?')),styles['SSTBody']))
    else:
        story.append(Paragraph('GPU unavailable: '+str(data.get('device_error','not detected')).replace('&','&amp;'),styles['SSTBody']))
    for sid,s in data.get('a003',{}).items():
        story.append(Paragraph('A003 '+sid,styles['SSTSub']))
        for row in s.get('grids',[]):
            story.append(Paragraph(f"N={row['grid']}: relative L2 u={row['u_error']:.6g}; "
                    f"omega={row['omega_error']:.6g}; numerical p={row['p_error']:.6g}; "
                    f"div RMS={row['gpu_div_u_rms']:.6g}",styles['SSTBody']))
    story += [Paragraph('Authority boundary',styles['SSTSub']),
        Paragraph('G48 remains UNRESOLVED. The Euler solver integrates assumed geometry-derived initial '
                  'vorticity; no external physical transverse-vorticity, force or pressure holdout '
                  'is supplied. Historical failed gates are unchanged.',styles['SSTBody'])]
    doc.build(story)
    return str(dest)
